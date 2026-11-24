"""Additive planning adapters/CLI preserve reviewed cases and genuine coverage scope."""

import json

import pytest
from typer.testing import CliRunner

from autoqa.application import ApplicationEngine
from autoqa.authorization import AuthorizationContext
from autoqa.cli import app
from autoqa.core import TestCase as Case
from autoqa.framework_runtime.contracts import APIScenario
from autoqa.intelligent_planning_service import (
    REQUIREMENTS,
    REVIEWS,
    IntelligentPlanningService,
)
from autoqa.management import approve_suite, propose
from autoqa.planning import _save_cases, approve, case_signature


def authorization(project, *operations):
    return AuthorizationContext(project.root, frozenset(operations))


def inventory(project):
    api = APIScenario.model_validate(
        {
            "id": "TC-API",
            "title": "Synthetic API health",
            "request": {"path": "/health"},
            "expect": {"status": 200},
            "environments": [
                {"name": "local", "origin": "http://127.0.0.1:8123", "allow_localhost": True}
            ],
            "environment": "local",
        }
    )
    cases = [
        Case(
            id="TC-UI",
            feature="Synthetic UI",
            title="Reviewed heading",
            description="Owned UI",
            preconditions=[],
            steps=["Inspect heading"],
            expected="Synthetic heading",
            evidence=[],
            kind="heading",
            url="http://127.0.0.1:8123",
            target="Synthetic heading",
        ),
        Case(
            id=api.id,
            feature="Synthetic API",
            title=api.title,
            description="Owned API",
            preconditions=[],
            steps=["GET /health"],
            expected="Reviewed status",
            evidence=[],
            kind="api",
            url="http://127.0.0.1:8123/health",
            contract=api.model_dump(),
        ),
    ]
    _save_cases(project, cases)
    approve(project, [case.id for case in cases], authorization=authorization(project, "review"))
    return project.cases()


def document(cases=()):
    requirements = [
        {
            "id": "REQ-UI",
            "title": "Owned heading",
            "description": "Synthetic UI requirement",
            "source_id": "SRC-OWNER",
            "review_status": "approved",
            "kind": "UI",
            "expected_behavior": "Synthetic heading is displayed",
        },
        {
            "id": "REQ-API",
            "title": "Owned API",
            "description": "Synthetic API requirement",
            "source_id": "SRC-OWNER",
            "review_status": "approved",
            "kind": "API",
            "expected_behavior": "Reviewed synthetic health status",
        },
        {
            "id": "REQ-MISSING",
            "title": "[red]Revisión de límite[/red]",
            "description": "Unknown expected outcome",
            "source_id": "SRC-OWNER",
        },
    ]
    return {
        "sources": [
            {
                "id": "SRC-OWNER",
                "reference": "Owned fixture specification",
                "description": "Synthetic owner requirement",
            }
        ],
        "requirements": requirements,
        "mappings": [
            {
                "requirement_id": "REQ-API" if c.kind == "api" else "REQ-UI",
                "case_id": c.id,
                "case_signature": case_signature(c),
                "review_status": "approved",
                "rationale": "Explicitly reviewed fixture relationship",
            }
            for c in cases
        ],
    }


def input_file(tmp_path, value):
    path = tmp_path / "requirements.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def tree(project):
    return {
        p.relative_to(project.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in project.root.rglob("*")
        if p.is_file()
    }


def test_analysis_maps_ui_api_without_writes_or_execution(project, tmp_path):
    cases = inventory(project)
    source = input_file(tmp_path, document(cases))
    before = tree(project)
    engine = ApplicationEngine(project)
    plan = engine.intelligent_plan(source)
    assert plan.coverage_scope == "SUPPLIED_REQUIREMENTS_ONLY"
    assert plan.execution_coverage == "NOT_ASSESSED"
    assert plan.summary.confirmed_mapped_requirements == 2
    assert plan.summary.missing_requirements == 1
    assert plan.summary.uncertain_requirements == 1
    assert {c.kind for c in plan.context.cases} == {"heading", "api"}
    assert all(c.receipt_valid for c in plan.context.cases)
    assert all(p.automation == "MANUAL_REVIEW" for p in plan.proposals)
    assert tree(project) == before
    assert engine.intelligent_plan(source).model_dump() == plan.model_dump()
    report = engine.coverage_report(source)
    assert report["id"] == plan.id
    assert report["execution_coverage"] == "NOT_ASSESSED"
    assert "proposals" not in report
    assert tree(project) == before


def test_import_and_review_write_only_new_sidecars_and_preserve_approvals(project, tmp_path):
    cases = inventory(project)
    source = input_file(tmp_path, document(cases))
    before = tree(project)
    engine = ApplicationEngine(project, authorization(project, "plan", "review"))
    engine.import_requirements(source)
    imported = tree(project)
    assert imported.keys() - before.keys() == {REQUIREMENTS}
    assert all(imported[key] == value for key, value in before.items())
    pending = engine.intelligent_plan()
    first, second = pending.proposals[:2]
    accepted = engine.review_plan(pending.id, [first.id], "accepted")
    assert accepted.id == pending.id and accepted.review_state == "CURRENT"
    assert next(p for p in accepted.proposals if p.id == first.id).review_status == "accepted"
    assert all(p.review_status == "pending" for p in accepted.proposals if p.id != first.id)
    rejected = engine.review_plan(pending.id, [second.id], "rejected")
    assert {p.id: p.review_status for p in rejected.proposals}[first.id] == "accepted"
    assert {p.id: p.review_status for p in rejected.proposals}[second.id] == "rejected"
    after = tree(project)
    assert after.keys() - before.keys() == {REQUIREMENTS, REVIEWS}
    assert all(after[key] == value for key, value in before.items())
    assert [c.review_status for c in project.cases()] == ["approved", "approved"]
    assert all(p.automation == "MANUAL_REVIEW" for p in rejected.proposals)


def test_case_drift_invalidates_plan_review_without_reapproving_case(project, tmp_path):
    cases = inventory(project)
    source = input_file(tmp_path, document(cases))
    engine = ApplicationEngine(project, authorization(project, "plan", "review"))
    engine.import_requirements(source)
    initial = engine.intelligent_plan()
    engine.review_plan(initial.id, [initial.proposals[0].id], "accepted")
    receipt = (project.root / "test-cases/approval-receipts.json").read_bytes()
    updated = project.cases()
    updated[0].expected = "Changed expectation requiring renewed scenario review"
    _save_cases(project, updated)
    before = tree(project)
    current = engine.intelligent_plan()
    assert current.id != initial.id and current.review_state == "STALE"
    assert all(p.review_status == "pending" for p in current.proposals)
    assert any("STALE_MAPPING" in finding.states for finding in current.findings)
    with pytest.raises(ValueError, match="snapshot changed"):
        engine.review_plan(initial.id, [initial.proposals[0].id], "accepted")
    assert (project.root / "test-cases/approval-receipts.json").read_bytes() == receipt
    assert tree(project) == before


def test_current_suite_labels_preserved_and_stale_membership_disclosed(project, tmp_path):
    cases = inventory(project)
    suite = propose(project)
    suite.id = "Reviewed_suite"
    suite.cases[0].tags = ["critical path", " trailing "]
    suite.packs[0].id = "SMOKE_pack"
    suite.packs[0].case_ids = [cases[0].id]
    approve_suite(project, suite, authorization(project, "review"))
    source = input_file(tmp_path, document(cases))
    before = tree(project)
    service = IntelligentPlanningService(project)
    current = service.analyze(source)
    assert current.context.suite_state == "CURRENT"
    assert current.context.suite_id == "Reviewed_suite"
    case = next(c for c in current.context.cases if c.id == cases[0].id)
    assert case.tags == [" trailing ", "critical path"]
    assert "SMOKE_pack" in case.pack_ids
    assert tree(project) == before
    changed = project.storage.read_json("test-cases/management.json")
    changed["cases"][0]["enabled"] = False
    project.storage.write_json("test-cases/management.json", changed)
    before = tree(project)
    stale = service.analyze(source)
    assert stale.context.suite_state == "STALE"
    assert stale.id != current.id
    assert all(not c.tags and not c.pack_ids for c in stale.context.cases)
    assert tree(project) == before


@pytest.mark.parametrize("operation", ["import", "review"])
def test_mutation_requires_project_bound_authorization(project, tmp_path, operation):
    source = input_file(tmp_path, document())
    before = tree(project)
    wrong = AuthorizationContext(tmp_path / "foreign", frozenset({"plan", "review"}))
    for context in [None, wrong, authorization(project, "execute")]:
        service = IntelligentPlanningService(project, context)
        with pytest.raises(ValueError, match="authorization"):
            if operation == "import":
                service.import_requirements(source)
            else:
                service.review("PLAN-" + "0" * 64, ["PROP-" + "0" * 20], "accepted")
    assert tree(project) == before


def test_cli_additive_json_and_explicit_review_workflow(project, tmp_path):
    source = input_file(tmp_path, document())
    runner = CliRunner()
    before = tree(project)
    read = runner.invoke(
        app, ["intelligent-plan", "--requirements", str(source), "--project", str(project.root)]
    )
    assert read.exit_code == 0, read.output
    payload = json.loads(read.stdout)
    assert "[red]Revisión de límite[/red]" in read.stdout
    assert tree(project) == before
    imported = runner.invoke(
        app, ["requirements-import", str(source), "--project", str(project.root)]
    )
    assert imported.exit_code == 0, imported.output
    assert json.loads(imported.stdout)["schema_version"] == "0.7"
    review = runner.invoke(
        app,
        [
            "plan-review",
            payload["id"],
            "--accept",
            payload["proposals"][0]["id"],
            "--project",
            str(project.root),
        ],
    )
    assert review.exit_code == 0, review.output
    assert json.loads(review.stdout)["review_state"] == "CURRENT"
    coverage = runner.invoke(app, ["coverage-report", "--project", str(project.root)])
    assert coverage.exit_code == 0, coverage.output
    assert json.loads(coverage.stdout)["execution_coverage"] == "NOT_ASSESSED"
    conflict = runner.invoke(
        app,
        [
            "plan-review",
            payload["id"],
            "--accept",
            payload["proposals"][0]["id"],
            "--reject",
            payload["proposals"][1]["id"],
            "--project",
            str(project.root),
        ],
    )
    assert conflict.exit_code == 1
    empty = runner.invoke(app, ["plan-review", payload["id"], "--project", str(project.root)])
    assert empty.exit_code == 1


@pytest.mark.parametrize(
    "reference",
    ["test-cases/test-matrix.json", "discovery/workflow-map.json", "test-cases/management.json"],
)
def test_malformed_present_project_data_is_generic_failure(project, tmp_path, reference):
    source = input_file(tmp_path, document())
    project.storage.write_text(reference, '{"sensitive-context":"must-not-echo",')
    before = tree(project)
    result = CliRunner().invoke(
        app, ["intelligent-plan", "--requirements", str(source), "--project", str(project.root)]
    )
    assert result.exit_code == 1
    assert "must-not-echo" not in result.stdout
    assert "Invalid current planning context" in result.stdout
    assert tree(project) == before


def test_empty_project_is_read_only_and_missing_requirements_fail(project, tmp_path):
    source = input_file(tmp_path, document())
    before = tree(project)
    service = IntelligentPlanningService(project)
    assert service.analyze(source).context.cases == []
    with pytest.raises(ValueError, match="requirements"):
        service.analyze()
    assert tree(project) == before


def test_import_rejects_normalized_document_that_exceeds_stored_read_bound(project, tmp_path):
    from autoqa.planning_contracts import MAX_INPUT_BYTES, RequirementsDocument

    value = document()
    template = value["requirements"][0]
    value["requirements"] = [
        template | {"id": f"REQ-{i}", "title": "T" * 200, "description": "x" * 1950}
        for i in range(100)
    ]
    raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
    normalized = RequirementsDocument.model_validate(value).model_dump(mode="json")
    assert len(raw) < MAX_INPUT_BYTES
    assert (
        len(json.dumps(normalized, indent=2, ensure_ascii=False).encode("utf-8")) > MAX_INPUT_BYTES
    )
    source = tmp_path / "bounded-input.json"
    source.write_bytes(raw)
    before = tree(project)
    service = IntelligentPlanningService(project, authorization(project, "plan"))
    with pytest.raises(ValueError, match="Serialized planning input exceeds"):
        service.import_requirements(source)
    assert tree(project) == before
