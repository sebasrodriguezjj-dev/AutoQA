"""Pure diagnostics/projections and preserved reporting orchestration."""

from copy import deepcopy

import pytest

from autoqa.core import Discovery, save_json
from autoqa.diagnostics import classify_failure, project_diagnostics
from autoqa.report_projection import historical_step_evidence, project_report
from autoqa.report_rendering import render_html
from autoqa.reporting import report


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
