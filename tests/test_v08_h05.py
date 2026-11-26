"""H05 actual standalone three-row invocation completeness regressions."""

import copy
import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from autoqa.api_service import plan_api
from autoqa.authorization import AuthorizationContext
from autoqa.core import initialize
from autoqa.framework import FrameworkService
from autoqa.management import approve_suite, propose
from autoqa.planning import approve, save_cases
from autoqa.v08_diagnosis import DiagnosisService


@pytest.fixture(scope="module")
def actual_three_row_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("h05-three-row")

    class Handler(BaseHTTPRequestHandler):
        broken = False

        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            value = parse_qs(urlsplit(self.path).query).get("sample", [""])[0]
            self.wfile.write(
                json.dumps({"sample": "controlled-defect" if self.broken else value}).encode()
            )

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    project = initialize("h05-owned", root / "projects")
    context = AuthorizationContext(
        project.root, frozenset({"plan", "review", "generate", "execute"})
    )
    spec = root / "api.json"
    spec.write_text(
        json.dumps(
            [
                {
                    "id": "TC-H05",
                    "title": "Owned three-row observation",
                    "request": {"path": "/health", "query": {"sample": "${sample}"}},
                    "expect": {"status": 200, "json_values": {"sample": "${sample}"}},
                    "environments": [
                        {
                            "name": "local",
                            "origin": f"http://127.0.0.1:{server.server_port}",
                            "allow_localhost": True,
                        }
                    ],
                    "environment": "local",
                    "data": {
                        "name": "owned",
                        "rows": [{"sample": f"owned-value-{i}"} for i in range(3)],
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    try:
        plan_api(project, spec, context)
        approve(project, ["TC-H05"], authorization=context)
        approve_suite(project, propose(project), context)
        export = root / "independent"
        FrameworkService(project, context).build(export)
        subprocess.run(["uv", "sync"], cwd=export, check=True, capture_output=True, timeout=120)
        python = export / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [
                str(python),
                "-c",
                "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
            ],
            cwd=export,
            check=True,
            capture_output=True,
            timeout=30,
        )
        execution = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", "run", "--all"],
            cwd=export,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert execution.returncode == 0, execution.stdout + execution.stderr
        result = json.loads(
            next((export / "artifacts").glob("*/results.json")).read_text(encoding="utf-8")
        )
        assert result["counts"] == {"PASSED": 3}
        assert {record["id"] for record in result["records"]} == {
            f"TC-H05--row-{i}" for i in range(3)
        }
        assert len(result["steps"]) == 6
        work = root / "copies"
        work.mkdir()
        Handler.broken = True
        defect_process = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", "run", "--all"],
            cwd=export,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert defect_process.returncode != 0
        candidates = [
            p
            for p in (export / "artifacts").glob("*/results.json")
            if json.loads(p.read_text(encoding="utf-8"))["run_id"] != result["run_id"]
        ]
        assert len(candidates) == 1
        defect = json.loads(candidates[0].read_text(encoding="utf-8"))
        assert defect["counts"] == {"FAILED": 3}
        assert sum(s["status"] == "FAILED" for s in defect["steps"]) == 3
        (work / "defect.json").write_bytes(candidates[0].read_bytes())
        yield project, result, work
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def analyze(project, result, path):
    path.write_text(json.dumps(result), encoding="utf-8")
    return DiagnosisService(project).analyze(path)


def test_complete_actual_three_rows_is_recorded_healthy(actual_three_row_run):
    project, result, work = actual_three_row_run
    report = analyze(project, result, work / "complete.json")
    assert len([f for f in report.findings if f.category == "HEALTHY_RECORDED_EXECUTION"]) == 3


@pytest.mark.parametrize(
    "change",
    [
        "one_missing",
        "first_missing",
        "middle_missing",
        "multiple_missing",
        "unexpected_row",
        "mixed_identity",
        "aggregate",
        "plan",
        "operation",
        "historical",
        "eligible",
        "kind-accounting",
        "execution-schema",
        "case-result-schema",
    ],
)
def test_incomplete_actual_invocation_scope_never_establishes_health(actual_three_row_run, change):
    project, original, work = actual_three_row_run
    result = copy.deepcopy(original)
    if change in {"one_missing", "first_missing", "middle_missing", "multiple_missing"}:
        removed = {
            "one_missing": {"TC-H05--row-2"},
            "first_missing": {"TC-H05--row-0"},
            "middle_missing": {"TC-H05--row-1"},
            "multiple_missing": {"TC-H05--row-1", "TC-H05--row-2"},
        }[change]
        result["records"] = [r for r in result["records"] if r["id"] not in removed]
        result["steps"] = [s for s in result["steps"] if s["test_id"] not in removed]
        # Conceal the trivial count mismatch: expected scope must not derive from records.
        result["counts"] = {"PASSED": len(result["records"])}
    elif change in {"unexpected_row", "mixed_identity"}:
        old = "TC-H05--row-2"
        new = "TC-H05--row-99" if change == "unexpected_row" else "TC-H05"
        for record in result["records"]:
            if record["id"] == old:
                record["id"] = new
        for step in result["steps"]:
            if step["test_id"] == old:
                step["test_id"] = new
                step["step_id"] = f"{new}:step-{step['sequence']}"
    elif change == "aggregate":
        result["case_results"][0]["status"] = "FAILED"
        result["accounting"]["passed"] = 0
    elif change == "plan":
        result["execution_run"]["plan"]["case_ids"] = ["TC-UNRELATED"]
    elif change == "operation":
        result["steps"].pop()
    elif change == "eligible":
        result["accounting"]["eligible"] += 1
    elif change == "kind-accounting":
        result["accounting"].update(ui=1, api=0)
    elif change == "execution-schema":
        result["execution_run"]["schema_version"] = "unsupported"
    elif change == "case-result-schema":
        result["execution_run"]["results"][0]["schema_version"] = "unsupported"
    else:
        result.pop("diagnostic_scope", None)
    report = analyze(project, result, work / f"{change}.json")
    assert not any(f.category == "HEALTHY_RECORDED_EXECUTION" for f in report.findings)
    assert any(
        f.category
        in {"INCOMPLETE_EXECUTION", "EVIDENCE_INTEGRITY_FAILURE", "INSUFFICIENT_EVIDENCE"}
        for f in report.findings
    )


def test_actual_assertion_failure_retains_symptom_without_claiming_root_cause(actual_three_row_run):
    project, _, work = actual_three_row_run
    report = DiagnosisService(project).analyze(work / "defect.json")
    symptoms = [f for f in report.findings if f.category == "ASSERTION_MISMATCH"]
    assert len(symptoms) == 3
    assert all(
        {h.category for h in f.hypotheses}
        >= {"APPLICATION_DEFECT_CANDIDATE", "AUTOMATION_DEFECT_CANDIDATE"}
        for f in symptoms
    )
    assert all(not f.root_cause_confirmed for f in report.findings)
    assert "controlled-defect" not in report.model_dump_json()


def test_duplicate_actual_invocation_is_rejected(actual_three_row_run):
    project, original, work = actual_three_row_run
    value = copy.deepcopy(original)
    value["records"].append(copy.deepcopy(value["records"][1]))
    with pytest.raises(ValueError, match="Invalid bounded recorded-run input"):
        analyze(project, value, work / "duplicate.json")


def test_historical_scope_is_private_deterministic_and_independent_of_current_data(
    actual_three_row_run,
):
    project, original, work = actual_three_row_run
    path = work / "historical-source.json"
    first = analyze(project, original, path)
    source_identity = path.read_bytes(), path.stat().st_mtime_ns
    cases = project.cases()
    cases[0].expected = "Later unrelated expectation"
    cases[0].contract["data"]["rows"] = [{"sample": "later-current-data"}]
    cases[0].review_status = "pending"
    save_cases(
        project, cases, authorization=AuthorizationContext(project.root, frozenset({"review"}))
    )
    before = {
        p.relative_to(project.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in project.root.rglob("*")
        if p.is_file()
    }
    assert DiagnosisService(project).analyze(path) == first
    assert (path.read_bytes(), path.stat().st_mtime_ns) == source_identity
    assert {
        p.relative_to(project.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in project.root.rglob("*")
        if p.is_file()
    } == before
    scope = json.dumps(original["diagnostic_scope"])
    assert "owned-value" not in scope and "controlled-defect" not in scope
    assert str(project.root) not in scope and "later-current-data" not in first.model_dump_json()
    permuted = copy.deepcopy(original)
    permuted["diagnostic_scope"]["expected_invocation_ids"]["TC-H05"].reverse()
    permuted["duration"] = 999
    assert analyze(project, permuted, work / "permuted.json") == first


@pytest.mark.parametrize("change", ["boolean", "oversized", "duplicate", "injected"])
def test_malformed_historical_scope_rejects_without_payload_echo(actual_three_row_run, change):
    project, original, work = actual_three_row_run
    result = copy.deepcopy(original)
    scope = result["diagnostic_scope"]
    if change == "boolean":
        scope["parameter_counts"]["TC-H05"] = True
    elif change == "oversized":
        scope["parameter_counts"]["TC-H05"] = 1001
    elif change == "duplicate":
        scope["expected_invocation_ids"]["TC-H05"][1] = "TC-H05--row-0"
    else:
        scope["expected_value"] = "private-sentinel"
    with pytest.raises(ValueError) as error:
        analyze(project, result, work / f"invalid-{change}.json")
    assert str(error.value) == "Invalid bounded recorded-run input"
    assert "private-sentinel" not in str(error.value)


@pytest.mark.browser
def test_actual_nonparameterized_chromium_run_remains_historically_diagnosable(project, tmp_path):
    from test_v08_framework import prepare

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b'<input type="number" data-testid="amount-old"><h1 data-testid="result">Approved result</h1>'
            )

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        export, case = prepare(project, tmp_path, f"http://127.0.0.1:{server.server_port}/")
        subprocess.run(["uv", "sync"], cwd=export, check=True, capture_output=True, timeout=120)
        python = export / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [
                str(python),
                "-c",
                "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
            ],
            cwd=export,
            check=True,
            capture_output=True,
            timeout=30,
        )
        execution = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", "run", "--all"],
            cwd=export,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert execution.returncode == 0, execution.stdout + execution.stderr
        path = next((export / "artifacts").glob("*/results.json"))
        recorded = json.loads(path.read_text(encoding="utf-8"))
        assert recorded["diagnostic_scope"]["parameter_counts"] == {case.id: None}
        assert recorded["diagnostic_scope"]["expected_invocation_ids"] == {case.id: [case.id]}
        assert recorded["counts"] == {"PASSED": 1} and len(recorded["steps"]) == 3
        report = DiagnosisService(project).analyze(path)
        assert len(report.findings) == 1
        assert report.findings[0].category == "HEALTHY_RECORDED_EXECUTION"
        assert not report.findings[0].missing_evidence
        legacy = copy.deepcopy(recorded)
        del legacy["diagnostic_scope"]
        uncertain = analyze(project, legacy, tmp_path / "legacy-ui.json")
        assert not any(f.category == "HEALTHY_RECORDED_EXECUTION" for f in uncertain.findings)
        assert any(
            "Historical expected invocation scope is unavailable" in text
            for f in uncertain.findings
            for text in f.missing_evidence
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
