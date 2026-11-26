"""Standalone validation, collection, bounded execution and run-scoped reporting."""

import argparse
import ast
import hashlib
import html
import json
import os
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .integrity import safe_path, validate
from .management import ExecutionResult, ExecutionRun, TestSelection, load_inventory, select


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def reconcile_collection(manifest, selected_cases, plan, collection):
    """Collection is complete only when every selected invocation is observed once."""
    expected = []
    unsupported = [c.id for c in selected_cases if not c.supported]
    for case in selected_cases:
        if not case.supported:
            continue
        node = "tests/test_approved.py::test_" + case.id.replace("-", "_")
        rows = manifest.get("parameters", {}).get(case.id)
        expected.extend([node + f"[{i}]" for i in range(rows)] if rows else [node])
    observed = Counter(
        line.strip() for line in collection.stdout.splitlines() if ".py::" in line.strip()
    )
    missing = sorted(set(expected) - observed.keys())
    duplicate = sorted(node for node in expected if observed[node] > 1)
    unexpected = sum(count for node, count in observed.items() if node not in expected)
    complete = not (unsupported or missing or duplicate or unexpected) and bool(expected)
    code = collection.returncode or (0 if complete else 3)
    return {
        "schema_version": "0.6",
        "exit_code": code,
        "collected_only": True,
        "selection_snapshot": plan.model_dump(),
        "selected_case_ids": plan.case_ids,
        "collection_status": "COMPLETE" if code == 0 else "INCOMPLETE_OR_FAILED",
        "unsupported_case_ids": unsupported,
        "missing_node_ids": missing,
        "duplicate_node_ids": duplicate,
        "unexpected_node_count": unexpected,
        "expected_invocations": len(expected),
        "collected_invocations": sum(observed[node] for node in expected),
    }


def junit(path):
    records = []
    if not path.exists():
        return records
    for node in ET.parse(path).getroot().iter("testcase"):
        status, error = "PASSED", ""
        for tag, outcome in (("error", "ERROR"), ("failure", "FAILED"), ("skipped", "SKIPPED")):
            failure = node.find(tag)
            if failure is not None:
                status, error = outcome, (failure.text or failure.get("message", ""))[:12000]
                break
        records.append(
            {
                "name": node.get("name"),
                "status": status,
                "duration": float(node.get("time", "0")),
                "error": error,
            }
        )
    return records


def read_steps(output, run_id, case_ids):
    records = []
    for case_id in case_ids:
        path = output / (case_id + "-steps.json")
        if not path.is_file() or path.is_symlink():
            continue
        for record in json.loads(path.read_text()):
            if record.get("run_id") != run_id or record.get("test_id") != case_id:
                continue
            prefix = case_id + "-step-"
            refs = []
            for name in record.get("evidence", []):
                if not isinstance(name, str) or "/" in name or "\\" in name:
                    continue
                if not (
                    name == case_id + ".zip" or (name.startswith(prefix) and name.endswith(".png"))
                ):
                    continue
                target = safe_path(output, name)
                if target.is_file():
                    refs.append(name)
            record["evidence"] = refs
            records.append(record)
    return records


def render_report(output, result):
    findings = []
    for record in result["records"]:
        if record["status"] not in {"FAILED", "ERROR", "NOT_EXECUTED"}:
            continue
        references = sorted(
            {
                ref
                for step in result["steps"]
                if step["test_id"] == record["id"]
                for ref in step["evidence"]
            }
        )
        findings.append(
            {
                "test_id": record["id"],
                "run_id": result["run_id"],
                "status": record["status"],
                "evidence": references,
                "possible_cause": "Not established; reproduce against the reviewed expectation",
                "human_review_required": True,
            }
        )
    write_json(output / "diagnosis.json", findings)
    result["counts"] = dict(Counter(r["status"] for r in result["records"]))
    write_json(output / "results.json", result)

    def escape(value):
        return html.escape(str(value), quote=True)

    rows = "".join(
        f"<tr><td>{escape(r['id'])}</td><td>{escape(r['status'])}</td>"
        f"<td>{escape(r['duration'])}</td></tr>"
        for r in result["records"]
    )
    steps = "".join(
        f"<tr><td>{escape(s['test_id'])}</td><td>{escape(s['sequence'])}</td>"
        f"<td>{escape(s['kind'])}</td><td>{escape(s['status'])}</td>"
        f"<td>{escape(s['duration'])}</td><td>"
        + " ".join(f'<a href="{escape(ref)}">{escape(ref)}</a>' for ref in s["evidence"])
        + "</td></tr>"
        for s in result["steps"]
    )
    (output / "report.html").write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>QA run</title>"
        "<style>body{font:16px system-ui;max-width:1200px;margin:32px auto}"
        "td,th{padding:8px;border:1px solid #ddd}table{border-collapse:collapse}</style></head>"
        f"<body><h1>QA run {escape(result['run_id'])}</h1><p>{escape(result['counts'])}</p>"
        f"<h2>Selection and accounting</h2><pre>{escape(json.dumps({k: result.get(k) for k in ['scope', 'overall_status', 'selection_snapshot', 'accounting']}, indent=2))}</pre>"
        "<h2>Actual scenario outcomes</h2><table><tr><th>Case</th><th>Status</th><th>Seconds</th>"
        f"</tr>{rows}</table><h2>Recorded operations</h2><table><tr><th>Case</th><th>Step</th>"
        f"<th>Kind</th><th>Status</th><th>Seconds</th><th>Evidence</th></tr>{steps}</table>"
        "<h2>Diagnostics</h2><p>Failures require human review; root cause is not established.</p>"
        f"<pre>{escape(json.dumps(findings, indent=2))}</pre>"
        '<p><a href="junit.xml">JUnit</a> | <a href="pytest.log">Raw log (may contain sensitive data)</a></p>'
        "<p>Missing/unexecuted steps have no fabricated outcomes. Review all evidence before sharing."
        " Traces may contain DOM snapshots and images.</p></body></html>",
        encoding="utf-8",
    )


def execute(root, *, collect_only=False, selection=None):
    from .config import Config
    from .security import Scope

    root = Path(root).absolute()
    manifest = validate(root)
    inventory = load_inventory(root, manifest)
    plan = select(inventory, selection or TestSelection())
    selected_cases = [c for c in inventory.cases if c.id in plan.case_ids]
    started_at = datetime.now(UTC).isoformat()
    for name in manifest["files"]:
        if name.endswith(".py"):
            ast.parse(safe_path(root, name).read_text(encoding="utf-8"), filename=name)
    config = Config.model_validate(json.loads((root / "config/environment.json").read_text()))
    base = os.environ.get("AUTOQA_BASE_URL", config.application_url)
    if not collect_only and config.application_url:
        Scope(base, config)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    # Capture reviewed expected identity before collection/execution. Never infer
    # cardinality from JUnit or the subsequently received invocation records.
    plan_projection = plan.model_dump()
    plan_projection["case_ids"] = sorted(plan_projection["case_ids"])
    plan_projection["pack_ids"] = sorted(plan_projection["pack_ids"])
    plan_projection["selection"]["values"] = sorted(plan_projection["selection"]["values"])
    parameter_counts = {
        case_id: manifest.get("parameters", {}).get(case_id) for case_id in plan.case_ids
    }
    diagnostic_scope = {
        "schema_version": "0.8",
        "run_id": run_id,
        "project_id": plan.project_id,
        "selected_case_ids": list(plan.case_ids),
        "parameter_counts": parameter_counts,
        "expected_invocation_ids": {
            case_id: [case_id] if rows is None else [f"{case_id}--row-{i}" for i in range(rows)]
            for case_id, rows in parameter_counts.items()
        },
        "case_signatures": {
            case_id: manifest["cases"][case_id]
            for case_id in plan.case_ids
            if case_id in manifest["cases"]
        },
        "plan_digest": hashlib.sha256(
            json.dumps(
                plan_projection,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    }
    output = safe_path(root, "artifacts/" + run_id)
    output.mkdir(parents=True)
    keep = {
        "SYSTEMROOT",
        "WINDIR",
        "PATH",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "HOME",
        "LOCALAPPDATA",
        "APPDATA",
        "COMSPEC",
        "PLAYWRIGHT_BROWSERS_PATH",
    }
    protected = manifest.get("privacy") == "summary_only"
    if protected:
        from .contracts import APIScenario, Authentication

        auths = [
            Authentication.model_validate(
                json.loads((root / "config/authentication.json").read_text())
            )
        ]
        cases = json.loads((root / "review/cases.json").read_text())
        auths += [
            APIScenario.model_validate(c["contract"]).authentication
            for c in cases
            if c["kind"] == "api"
        ]
        keep.add("AUTOQA_ENVIRONMENT")
        for auth in auths:
            keep.update(
                name for name in (auth.token_env, auth.username_env, auth.password_env) if name
            )
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    env.update(
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        AUTOQA_RUN_ID=run_id,
        AUTOQA_BASE_URL=base or "",
        PYTHONPATH=str(root),
    )
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        "pytest.ini",
        "--rootdir",
        str(root),
        "--confcutdir",
        str(root),
        "-q",
        *[
            "tests/test_approved.py::test_" + c.id.replace("-", "_")
            for c in selected_cases
            if c.supported
        ],
    ]
    has_executable = any(c.supported for c in selected_cases)
    started = time.monotonic()
    collection = (
        subprocess.run(
            command + ["--collect-only"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if has_executable
        else subprocess.CompletedProcess(command, 3, "No compiled scenario in selected scope", "")
    )
    collection_log = (
        f"Collection exit: {collection.returncode}; details withheld by summary_only policy"
        if protected
        else collection.stdout + collection.stderr
    )
    (output / "collection.log").write_text(collection_log, encoding="utf-8")
    if collect_only:
        result = reconcile_collection(manifest, selected_cases, plan, collection)
        result["run_id"] = run_id
        write_json(output / "collection.json", result)
        print(collection_log)
        print(
            f"Selection collection: {result['collection_status']}; "
            f"unsupported={len(result['unsupported_case_ids'])}, "
            f"missing={len(result['missing_node_ids'])}, "
            f"duplicate={len(result['duplicate_node_ids'])}, "
            f"unexpected={result['unexpected_node_count']}; details: {output / 'collection.json'}"
        )
        return result
    try:
        process = (
            subprocess.run(
                command + ["--junitxml", str(output / "junit.xml")],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                timeout=config.overall_timeout_seconds,
            )
            if collection.returncode == 0
            else collection
        )
        code, log = process.returncode, process.stdout + process.stderr
    except subprocess.TimeoutExpired:
        code, log = 124, "Execution timed out; outcomes may be incomplete."
    if protected:
        log = f"Execution exit: {code}; details withheld by summary_only policy"
    (output / "pytest.log").write_text(log, encoding="utf-8")
    actual = {}
    reconciliation_errors = []
    try:
        junit_records = junit(output / "junit.xml")
    except ET.ParseError, ValueError, OSError:
        junit_records = []
        reconciliation_errors.append("Unreadable or malformed JUnit; outcomes not established")
        code = code or 3
    for record in junit_records:
        name = record["name"]
        if name in actual:
            # Never let a later duplicate overwrite an earlier failure or error.
            actual[name] = {
                "name": name,
                "status": "ERROR",
                "duration": 0,
                "error": "Ambiguous duplicate JUnit testcase identity",
            }
        else:
            actual[name] = record
    records = []
    for case_id in plan.case_ids:
        if case_id not in manifest["cases"]:
            records.append(
                {
                    "id": case_id,
                    "case_id": case_id,
                    "name": case_id,
                    "status": "UNSUPPORTED",
                    "duration": 0,
                    "error": "No compiled scenario",
                }
            )
            continue
        name = "test_" + case_id.replace("-", "_")
        rows = manifest.get("parameters", {}).get(case_id)
        names = [name + f"[{i}]" for i in range(rows)] if rows else [name]
        for index, instance_name in enumerate(names):
            record = actual.get(
                instance_name,
                {
                    "name": instance_name,
                    "status": "NOT_EXECUTED",
                    "duration": 0,
                    "error": "No JUnit testcase; inspect collection and execution logs",
                },
            )
            identity = case_id + f"--row-{index}" if rows else case_id
            records.append({"id": identity, "case_id": case_id, **record})
    steps = read_steps(output, run_id, [r["id"] for r in records])
    for record in records:
        if record["status"] != "PASSED":
            continue
        observed = [step for step in steps if step["test_id"] == record["id"]]
        required_operations = manifest.get("operation_counts", {}).get(record["case_id"])
        if (
            (required_operations is not None and len(observed) != required_operations)
            or not observed
            or any(
                step["status"] != "PASSED"
                or step["sequence"] != index
                or step["step_id"] != f"{record['id']}:step-{index}"
                for index, step in enumerate(observed, 1)
            )
        ):
            record.update(
                status="ERROR",
                error="Passing JUnit outcome lacks consistent current-run operation evidence",
            )
    if code == 0 and any(
        r["status"] in {"FAILED", "ERROR", "NOT_EXECUTED", "UNSUPPORTED", "SKIPPED"}
        for r in records
    ):
        code = 3
        (output / "pytest.log").write_text(
            log + "\nExecution did not emit successful JUnit results for every approved case.\n",
            encoding="utf-8",
        )
    expected = {r["name"] for r in records if r["status"] != "UNSUPPORTED"}
    if set(actual) - expected:
        reconciliation_errors.append("JUnit contains identities outside the selected scope")
        code = code or 3
    case_results = []
    for case_id in plan.case_ids:
        outcomes = {r["status"] for r in records if r["case_id"] == case_id}
        outcome = next(
            status
            for status in ["ERROR", "FAILED", "NOT_EXECUTED", "UNSUPPORTED", "SKIPPED", "PASSED"]
            if status in outcomes
        )
        case_results.append(
            {
                "case_id": case_id,
                "status": outcome,
                "evidence": [
                    r["id"] + "-steps.json"
                    for r in records
                    if r["case_id"] == case_id and any(s["test_id"] == r["id"] for s in steps)
                ],
            }
        )
    distribution = Counter(r["status"] for r in case_results)
    eligible = sum(c.enabled and c.review_status == "approved" for c in inventory.cases)
    executed = sum(r["status"] in {"PASSED", "FAILED", "ERROR", "SKIPPED"} for r in case_results)
    completed_at = datetime.now(UTC).isoformat()
    execution_run = ExecutionRun(
        run_id=run_id,
        plan=plan,
        started_at=started_at,
        completed_at=completed_at,
        results=[ExecutionResult.model_validate(r) for r in case_results],
    )
    result = {
        "execution_run": execution_run.model_dump(),
        "evidence_policy": "summary_only" if protected else "standard",
        "diagnostic_snapshot": [
            {
                "id": case.id,
                "kind": case.kind,
                "signature": manifest["cases"].get(case.id),
                "operation_count": manifest.get("operation_counts", {}).get(case.id),
                "review_status": case.review_status,
            }
            for case in selected_cases
            if case.id in manifest["cases"]
        ],
        "diagnostic_scope": diagnostic_scope,
        "schema_version": "0.6",
        "project_id": plan.project_id,
        "suite_id": plan.suite_id,
        "pack_ids": plan.pack_ids,
        "selected_case_ids": plan.case_ids,
        "selection_mode": plan.selection.mode,
        "selection_snapshot": plan.model_dump(),
        "scope": "FULL_REGRESSION" if plan.selection.mode == "all" else "SELECTED_SCOPE",
        "overall_status": "PASSED" if code == 0 else "INCOMPLETE_OR_FAILED",
        "started_at": started_at,
        "completed_at": completed_at,
        "case_results": case_results,
        "reconciliation_errors": reconciliation_errors,
        "accounting": {
            "eligible": eligible,
            "selected": len(plan.case_ids),
            "executed": executed,
            **{
                status.lower(): distribution[status]
                for status in [
                    "PASSED",
                    "FAILED",
                    "ERROR",
                    "SKIPPED",
                    "NOT_EXECUTED",
                    "UNSUPPORTED",
                ]
            },
            "coverage_within_selection": executed / len(plan.case_ids),
            "ui": sum(c.kind == "UI" for c in selected_cases),
            "api": sum(c.kind == "API" for c in selected_cases),
        },
        "junit": "junit.xml",
        "evidence_directory": ".",
        "run_id": run_id,
        "exit_code": code,
        "records": records,
        "duration": round(time.monotonic() - started, 3),
        "steps": steps,
    }
    render_report(output, result)
    print(f"Run {run_id}: exit {code}; report: {output / 'report.html'}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate/run the approved standalone framework")
    parser.add_argument("command", choices=["validate", "collect", "run"])
    group = parser.add_mutually_exclusive_group()
    for mode in ["case", "pack", "suite", "tag"]:
        group.add_argument("--" + mode, action="append")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    mode = next((m for m in ["case", "pack", "suite", "tag"] if getattr(args, m)), "all")
    selection = TestSelection(mode=mode, values=getattr(args, mode) if mode != "all" else [])
    root = Path(__file__).resolve().parents[1]
    try:
        if args.command == "validate":
            manifest = validate(root)
            for name in manifest["files"]:
                if name.endswith(".py"):
                    ast.parse(safe_path(root, name).read_text(encoding="utf-8"), filename=name)
            print(f"Validated {len(manifest['cases'])} approved scenarios")
            return 0
        return execute(root, collect_only=args.command == "collect", selection=selection)[
            "exit_code"
        ]
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Framework operation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
