"""Pure diagnostics/projections and preserved reporting orchestration."""

from copy import deepcopy

import pytest

from autoqa.core import Discovery, save_json
from autoqa.diagnostics import classify_failure, project_diagnostics
from autoqa.report_projection import historical_step_evidence, project_report
from autoqa.report_rendering import render_html
from autoqa.reporting import diagnose, report


@pytest.mark.parametrize(
    ("error", "kind", "category", "failure_class"),
    [
        ("strict mode violation", "heading", "Locator ambiguity", "TEST AUTOMATION FAILURE"),
        ("net::ERR", "heading", "Navigation failure", "ENVIRONMENT FAILURE"),
        ("timeout", "heading", "Timeout", "UNKNOWN"),
        ("to_have_url", "link", "Unexpected navigation", "UNKNOWN"),
        ("result mismatch", "functional", "Search result mismatch", "APPLICATION DEFECT CANDIDATE"),
        ("waiting for locator", "heading", "Locator not found", "TEST AUTOMATION FAILURE"),
        ("no junit", "heading", "Environment issue", "ENVIRONMENT FAILURE"),
    ],
)
def test_classification(error, kind, category, failure_class):
    classified = classify_failure(
        {"error": error}, {"kind": kind, "contract": {"workflow": "search"}}
    )
    assert classified.category == category
    assert classified.failure_class == failure_class


def test_projection_statuses_evidence_and_nonmutation():
    statuses = ["PASSED", "FAILED", "ERROR", "SKIPPED", "NOT_EXECUTED"]
    run = {
        "run_id": "r",
        "artifact_dir": "artifacts/r",
        "records": [
            {"id": status, "name": status, "status": status, "error": "assert mismatch"}
            for status in statuses
        ],
    }
    original = deepcopy(run)
    findings = project_diagnostics(run, {}, {"artifacts/r/pytest.log"})
    assert len(findings) == 3
    assert all(f["evidence"] == ["artifacts/r/pytest.log"] for f in findings)
    payload = project_report({}, run, [], Discovery(), {"cases": {}}, findings, [])
    assert payload["counts"] == dict.fromkeys(statuses, 1)
    assert payload["executed"] == 4
    assert run == original
    assert historical_step_evidence([{"id": "c", "steps": ["one", "two"]}]) == [
        {"case_id": "c", "ordinal": 1, "status": "NOT_RECORDED"},
        {"case_id": "c", "ordinal": 2, "status": "NOT_RECORDED"},
    ]


def test_renderer_escaping_and_empty_execution():
    payload = project_report(
        {"name": "<script>bad()</script>"},
        {"run_id": None, "records": [], "execution_state": "NOT_EXECUTED"},
        [],
        Discovery(),
        {"cases": {}},
        [],
        [],
    )
    html = render_html(payload)
    assert "<script>bad()</script>" not in html
    assert "&lt;script&gt;" in html
    assert payload["run"]["run_id"] is None
    assert payload["executed"] == 0


def test_report_rejects_escaping_run_artifacts(project):
    save_json(project.root / "discovery/workflow-map.json", Discovery().model_dump())
    save_json(project.root / "test-cases/test-matrix.json", [])
    save_json(
        project.root / "reports/latest-run.json",
        {"run_id": "r", "records": [], "artifact_dir": "../outside"},
    )
    with pytest.raises(ValueError, match="project-relative"):
        report(project, "json")
    assert not (project.root / "reports/qa-report.json").exists()


@pytest.mark.parametrize("screenshot", ["test_TC_001-step-1.png", "test_TC_001.png"])
def test_diagnosis_resolves_current_and_legacy_screenshots(project, screenshot):
    run = {
        "run_id": "current",
        "artifact_dir": "artifacts/current",
        "records": [{"id": "TC-001", "name": "test_TC_001", "status": "FAILED", "error": "assert"}],
    }
    if "step" in screenshot:
        run["step_results"] = [{"test_id": "TC-001", "evidence": [screenshot, "test_TC_001.zip"]}]
    for name in (screenshot, "test_TC_001.zip", "pytest.log"):
        project.storage.write_text("artifacts/current/" + name, "evidence")
    project.storage.write_json("reports/latest-run.json", run)
    expected = [
        "artifacts/current/pytest.log",
        "artifacts/current/test_TC_001.zip",
        "artifacts/current/" + screenshot,
    ]
    assert diagnose(project)[0]["evidence"] == expected
    persisted = project.storage.read_json("reports/diagnosis.json")
    assert persisted["run_id"] == "current"
    assert persisted["findings"][0]["evidence"] == expected


def test_diagnosis_omits_missing_step_and_legacy_evidence(project):
    project.storage.write_json(
        "reports/latest-run.json",
        {
            "run_id": "current",
            "artifact_dir": "artifacts/current",
            "records": [
                {"id": "TC-001", "name": "test_TC_001", "status": "FAILED", "error": "assert"}
            ],
            "step_results": [{"test_id": "TC-001", "evidence": ["test_TC_001-step-1.png"]}],
        },
    )
    assert diagnose(project)[0]["evidence"] == []


def test_diagnosis_binds_step_evidence_to_current_run_and_test(project):
    run = {
        "run_id": "current",
        "artifact_dir": "artifacts/current",
        "records": [
            {"id": "TC-001", "name": "test_TC_001", "status": "FAILED", "error": "assert"},
            {"id": "TC-002", "name": "test_TC_002", "status": "FAILED", "error": "assert"},
        ],
        "step_results": [
            {"test_id": "TC-001", "evidence": ["test_TC_001-step-1.png"]},
            {"test_id": "TC-002", "evidence": ["test_TC_002-step-1.png"]},
            {"test_id": "TC-003", "evidence": ["unrelated.png"]},
            {"test_id": "TC-001", "run_id": "old", "evidence": ["stale.png"]},
            {"test_id": "TC-001", "evidence": ["../old/old.png", "/outside.png"]},
            {"test_id": "TC-001", "evidence": ["only-in-old-run.png"]},
        ],
    }
    for name in ("test_TC_001-step-1.png", "test_TC_002-step-1.png", "unrelated.png", "stale.png"):
        project.storage.write_text("artifacts/current/" + name, "evidence")
    for name in ("old.png", "only-in-old-run.png"):
        project.storage.write_text("artifacts/old/" + name, "historical evidence")
    project.storage.write_json("reports/latest-run.json", run)
    findings = diagnose(project)
    assert [(f["test_id"], f["evidence"]) for f in findings] == [
        ("TC-001", ["artifacts/current/test_TC_001-step-1.png"]),
        ("TC-002", ["artifacts/current/test_TC_002-step-1.png"]),
    ]
