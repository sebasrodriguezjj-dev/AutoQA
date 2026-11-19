"""Failure classification and reports based on actual execution records."""

from collections import Counter

from jinja2 import Environment, PackageLoader, select_autoescape

from autoqa.core import Discovery, Project, TestCase, load_json, save_json


def diagnose(project: Project) -> list[dict]:
    result = load_json(project.root / "reports/latest-run.json")
    findings = []
    cases = {c["id"]: c for c in result.get("case_snapshot", [])}
    if not cases and (project.root / "test-cases/test-matrix.json").exists():
        cases = {c.id: c.model_dump() for c in project.cases()}
    for record in result["records"]:
        if record["status"] not in {"FAILED", "ERROR", "NOT_EXECUTED"}:
            continue
        category = "Unknown"
        advice = "Review the trace and application logs; reproduce manually."
        failure_class = "UNKNOWN"
        for fragment, label, recommendation in [
            (
                "net::",
                "Navigation failure",
                "Verify availability, DNS and authorized network scope.",
            ),
            (
                "strict mode violation",
                "Locator failure",
                "Inspect locator ambiguity against the recorded DOM.",
            ),
            (
                "timeout",
                "Timeout",
                "Review the trace for missing elements, slow UI or environment delays.",
            ),
            (
                "assert",
                "Assertion failure",
                "Compare the approved expectation with UI evidence; investigate a possible application defect or stale baseline.",
            ),
            (
                "no junit",
                "Environment issue",
                "Inspect pytest.log for collection errors or interrupted execution.",
            ),
        ]:
            if fragment in record["error"].lower():
                category, advice = label, recommendation
                break
        case = cases.get(record["id"], {})
        error = record["error"].lower()
        if "strict mode violation" in error:
            category, failure_class = "Locator ambiguity", "TEST AUTOMATION FAILURE"
        elif any(
            fragment in error
            for fragment in (
                "net::",
                "browser has been closed",
                "executable doesn't exist",
                "no junit",
            )
        ):
            failure_class = "ENVIRONMENT FAILURE"
        elif "to_have_url" in error:
            category = "Unexpected navigation"
        elif case.get("kind") == "functional" and "result mismatch" in error:
            workflow = case.get("contract", {}).get("workflow")
            category = {
                "search": "Search result mismatch",
                "filter": "Filter result mismatch",
                "sorting": "Sorting mismatch",
                "form": "Form validation failure",
            }.get(workflow, "Assertion mismatch")
            failure_class = "APPLICATION DEFECT CANDIDATE"
            advice = "Compare approved contract and captured results; reproduce manually before confirming a product defect."
        elif "waiting for locator" in error:
            category, failure_class = "Locator not found", "TEST AUTOMATION FAILURE"
        findings.append(
            {
                "test_id": record["id"],
                "category": category,
                "observed_error": record["error"],
                "evidence": [
                    result["artifact_dir"] + "/pytest.log",
                    result["artifact_dir"] + "/" + record["name"] + ".zip",
                ],
                "possible_cause": category + "; root cause is not established",
                "confidence": "low",
                "recommendation": advice,
                "human_review_required": True,
                "failure_class": failure_class,
                "expected_behavior": case.get("expected", "Unknown; no matching scenario snapshot"),
                "observed_behavior": record["error"] or record["status"],
            }
        )
    for finding, record in zip(
        findings,
        [r for r in result["records"] if r["status"] in {"FAILED", "ERROR", "NOT_EXECUTED"}],
        strict=True,
    ):
        screenshot = result["artifact_dir"] + "/" + record["name"] + ".png"
        if (project.root / screenshot).is_file():
            finding["evidence"].append(screenshot)
        finding["evidence"] = [
            path for path in finding["evidence"] if (project.root / path).is_file()
        ]
    save_json(
        project.root / "reports/diagnosis.json", {"run_id": result["run_id"], "findings": findings}
    )
    project.audit(f"Diagnosed {len(findings)} failures")
    return findings


def report(project: Project, format: str) -> str:
    run_path = project.root / "reports/latest-run.json"
    executed = run_path.exists()
    result = (
        load_json(run_path)
        if executed
        else {
            "run_id": None,
            "created_at": project.discovery().created_at,
            "records": [],
            "exit_code": None,
            "duration": 0,
            "artifact_dir": "artifacts",
            "base_url": project.config.application_url,
            "execution_state": "NOT_EXECUTED",
        }
    )
    cases = (
        [TestCase.model_validate(c) for c in result["planning_snapshot"]]
        if "planning_snapshot" in result
        else project.cases()
    )
    discovery = (
        Discovery.model_validate(result["discovery_snapshot"])
        if "discovery_snapshot" in result
        else project.discovery()
    )
    findings = diagnose(project) if executed else []
    manifest_path = project.root / "automation/manifest.json"
    manifest = load_json(manifest_path) if manifest_path.exists() else {"cases": {}}
    payload = {
        "project": project.config.model_dump(),
        "run": result,
        "counts": dict(Counter(r["status"] for r in result["records"])),
        "workflow_count": len(discovery.workflows),
        "approved": sum(c.review_status == "approved" for c in cases),
        "automated": len(manifest["cases"]),
        "unautomated": sum(c.id not in manifest["cases"] for c in cases),
        "discovery_errors": discovery.errors,
        "findings": findings,
        "pages_analyzed": len(discovery.pages),
        "interactive_elements": sum(
            sum(e.kind in {"a", "button", "input", "select", "textarea"} for e in p.elements)
            for p in discovery.pages
        ),
        "proposed": len(cases),
        "pending": sum(c.review_status == "pending" for c in cases),
        "rejected": sum(c.review_status == "rejected" for c in cases),
        "executed": sum(
            r["status"] in {"PASSED", "FAILED", "SKIPPED", "ERROR"} for r in result["records"]
        ),
        "functional_validated": sum(
            r["status"] == "PASSED"
            and any(c.id == r["id"] and c.kind == "functional" for c in cases)
            for r in result["records"]
        ),
        "potential_defects": sum(
            f.get("failure_class") == "APPLICATION DEFECT CANDIDATE" for f in findings
        ),
        "unverified": [
            c.model_dump() for c in cases if c.review_status != "approved" or not c.feasible
        ],
        "workflow_results": {},
        "artifacts": [],
        "discovery_screenshots": [p.screenshot for p in discovery.pages],
        "blocked_requests": discovery.blocked_requests,
        "blocked_summary": [
            {"origin": origin, "method": method, "count": count}
            for (origin, method), count in Counter(
                (r["origin"], r["method"]) for r in discovery.blocked_requests
            ).items()
        ],
    }
    artifact_root = project.root / result["artifact_dir"]
    if artifact_root.is_dir():
        payload["artifacts"] = [
            p.relative_to(project.root).as_posix()
            for p in sorted(artifact_root.iterdir())
            if p.is_file() and p.suffix in {".png", ".zip", ".log", ".xml"}
        ]
    if "case_snapshot" in result:
        payload["automated"] = len(result["case_snapshot"])
        payload["unautomated"] = sum(
            c.id not in {s["id"] for s in result["case_snapshot"]} for c in cases
        )
    for record in result["records"]:
        case = next((c for c in cases if c.id == record["id"]), None)
        workflow = case.feature if case else "Unknown"
        group = payload["workflow_results"].setdefault(workflow, {})
        group[record["status"]] = group.get(record["status"], 0) + 1
    if format == "json":
        name = "qa-report.json"
        save_json(project.root / "reports" / name, payload)
    elif format == "html":
        environment = Environment(
            loader=PackageLoader("autoqa", "templates"), autoescape=select_autoescape(["html"])
        )
        name = "qa-report.html"
        (project.root / "reports" / name).write_text(
            environment.get_template("report.html").render(**payload), encoding="utf-8"
        )
    else:
        raise ValueError("Report format must be html or json.")
    project.audit(f"Created {name}")
    return str(project.root / "reports" / name)
