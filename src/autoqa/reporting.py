"""Reporting orchestration; preserves public entry points and write side effects."""

from autoqa.core import Discovery, Project, TestCase, load_json
from autoqa.diagnostics import project_diagnostics
from autoqa.report_projection import project_report
from autoqa.report_rendering import render_html


def diagnose(project: Project) -> list[dict]:
    result = project.storage.read_json("reports/latest-run.json")
    cases = {c["id"]: c for c in result.get("case_snapshot", [])}
    if not cases and project.storage.path("test-cases/test-matrix.json").exists():
        cases = {c.id: c.model_dump() for c in project.cases()}
    available = set()
    for record in result["records"]:
        for suffix in (".png", ".zip"):
            reference = result["artifact_dir"] + "/" + record["name"] + suffix
            if project.storage.path(reference).is_file():
                available.add(reference)
    log = result["artifact_dir"] + "/pytest.log"
    if project.storage.path(log).is_file():
        available.add(log)
    findings = project_diagnostics(result, cases, available)
    project.storage.write_json(
        "reports/diagnosis.json", {"run_id": result["run_id"], "findings": findings}
    )
    project.audit(f"Diagnosed {len(findings)} failures")
    return findings


def report(project: Project, format: str) -> str:
    run_path = project.storage.path("reports/latest-run.json")
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
    manifest_path = project.storage.path("automation/manifest.json")
    manifest = load_json(manifest_path) if manifest_path.exists() else {"cases": {}}
    artifact_root = project.storage.path(result["artifact_dir"])
    artifacts = (
        [
            p.relative_to(project.root).as_posix()
            for p in sorted(artifact_root.iterdir())
            if p.is_file() and not p.is_symlink() and p.suffix in {".png", ".zip", ".log", ".xml"}
        ]
        if artifact_root.is_dir()
        else []
    )
    payload = project_report(
        project.config.model_dump(), result, cases, discovery, manifest, findings, artifacts
    )
    if format == "json":
        name = "qa-report.json"
        project.storage.write_json("reports/" + name, payload)
    elif format == "html":
        name = "qa-report.html"
        project.storage.write_text("reports/" + name, render_html(payload))
    else:
        raise ValueError("Report format must be html or json.")
    project.audit(f"Created {name}")
    return str(project.root / "reports" / name)
