"""Independent V0.7 acceptance: planning truthfulness, review isolation and hostile data."""

import copy
import json
import socket
import subprocess
from pathlib import Path

import pytest

from autoqa.authorization import AuthorizationContext
from autoqa.core import Discovery, EvidenceReference, Workflow
from autoqa.core import TestCase as LegacyCase
from autoqa.management import approve_suite, propose
from autoqa.planning import approve, case_signature, save_cases, verify_approval_binding
from autoqa.planning_contracts import MAX_INPUT_BYTES, PlanningContext, RequirementsDocument
from autoqa.qa_planning import build_plan, parse_requirements


def planning_service(project, authorization=None):
    # Pure planning tests can run before the independently owned adapter is integrated.
    from autoqa.intelligent_planning_service import IntelligentPlanningService

    return IntelligentPlanningService(project, authorization)


def supplied_requirements():
    return {
        "sources": [
            {"id": "SRC-UI", "reference": "synthetic-spec/ui", "description": "Owned UI spec"},
            {"id": "SRC-API", "reference": "synthetic-spec/api", "description": "Owned API spec"},
        ],
        "evidence": [
            {"id": "SUP-UI", "source_id": "SRC-UI", "description": "Reviewed UI requirement"},
            {"id": "SUP-API", "source_id": "SRC-API", "description": "Reviewed API requirement"},
        ],
        "requirements": [
            {
                "id": "REQ-UI",
                "title": "Approved product heading",
                "description": "The owned product screen has the reviewed heading.",
                "source_id": "SRC-UI",
                "review_status": "approved",
                "kind": "UI",
                "expected_behavior": "Owned product heading is shown",
                "priority": "Critical",
                "business_criticality": 5,
                "user_impact": 5,
                "evidence_ids": ["SUP-UI"],
                "workflow_ids": ["WF-UI"],
                "observed_evidence_ids": ["OBS-UI"],
                "related_ids": ["REQ-API"],
                "design_hints": [
                    {"kind": "negative", "condition": "Review an invalid owned input"},
                    {
                        "kind": "boundary",
                        "condition": "Review the declared minimum fixture quantity",
                        "expected_behavior": "The supplied minimum is accepted",
                    },
                ],
            },
            {
                "id": "REQ-API",
                "title": "Approved health response",
                "description": "The owned API contract returns the declared healthy status.",
                "source_id": "SRC-API",
                "review_status": "approved",
                "kind": "API",
                "expected_behavior": "Reviewed healthy response",
                "evidence_ids": ["SUP-API"],
                "workflow_ids": ["WF-API"],
                "observed_evidence_ids": ["OBS-API"],
            },
        ],
        "mappings": [
            {
                "requirement_id": "REQ-UI",
                "case_id": "TC-UI",
                "case_signature": "a" * 64,
                "review_status": "approved",
                "rationale": "Explicit reviewed UI mapping",
            },
            {
                "requirement_id": "REQ-API",
                "case_id": "TC-API",
                "case_signature": "b" * 64,
                "review_status": "approved",
                "rationale": "Explicit reviewed API mapping",
            },
        ],
    }


def supplied_context():
    return {
        "project_id": "owned",
        "cases": [
            {
                "id": "TC-UI",
                "signature": "a" * 64,
                "review_status": "approved",
                "receipt_valid": True,
                "supported": True,
                "kind": "heading",
                "title": "Owned heading",
                "pack_ids": ["SMOKE", "REGRESSION"],
                "tags": ["critical", "ui"],
            },
            {
                "id": "TC-API",
                "signature": "b" * 64,
                "review_status": "approved",
                "receipt_valid": True,
                "supported": True,
                "kind": "api",
                "title": "Owned health response",
                "pack_ids": ["API", "REGRESSION"],
                "tags": ["service", "healthy"],
            },
        ],
        "workflow_ids": ["WF-UI", "WF-API"],
        "evidence_ids": ["OBS-UI", "OBS-API"],
        "suite_id": "REVIEWED",
        "suite_state": "CURRENT",
        "suite_digest": "c" * 64,
    }


def snapshot(document=None, context=None):
    return build_plan(
        RequirementsDocument.model_validate(document or supplied_requirements()),
        PlanningContext.model_validate(context or supplied_context()),
    )


def finding(plan, requirement="REQ-UI"):
    return next(row for row in plan.findings if row.requirement_id == requirement)


def test_reviewed_ui_api_mapping_is_never_claimed_as_executed_coverage():
    plan = snapshot()
    assert plan.coverage_scope == "SUPPLIED_REQUIREMENTS_ONLY"
    assert plan.execution_coverage == "NOT_ASSESSED"
    assert plan.summary.total_requirements == plan.summary.confirmed_mapped_requirements == 2
    assert finding(plan).confirmed_case_ids == ["TC-UI"]
    assert finding(plan, "REQ-API").confirmed_case_ids == ["TC-API"]
    assert all("CONFIRMED_REVIEWED_MAPPING" in f.states for f in plan.findings)
    assert plan.limitations
    payload = plan.model_dump()
    assert not {"execution_results", "pass_percentage", "application_coverage"} & payload.keys()
    assert not any(
        p.review_status != "pending" or p.automation != "MANUAL_REVIEW" for p in plan.proposals
    )


def test_risk_is_explained_by_the_agreed_factors_not_a_fabricated_measurement():
    risk = finding(snapshot()).risk
    assert risk.factors == {
        "business_criticality": 20,
        "user_impact": 20,
        "priority": 15,
        "coverage_gap": 0,
        "observed_functionality": 10,
        "execution_feasibility": 10,
        "uncertainty": 0,
    }
    assert risk.score == 75 and risk.level == "High" and risk.reasons


def test_missing_mapping_and_unknown_observations_stay_visible():
    document = supplied_requirements()
    document["mappings"] = []
    document["requirements"][0]["workflow_ids"] = ["WF-NOT-OBSERVED"]
    document["requirements"][0]["observed_evidence_ids"] = ["OBS-NOT-OBSERVED"]
    plan = snapshot(document)
    ui = finding(plan)
    assert {"MISSING_MAPPING", "INSUFFICIENT_EVIDENCE"} <= set(ui.states)
    assert not ui.confirmed_case_ids
    assert ui.risk.factors["coverage_gap"] == 15
    assert ui.risk.factors["observed_functionality"] == 0
    assert ui.risk.factors["uncertainty"] == 10
    assert plan.summary.missing_requirements == 2
    assert plan.summary.uncertain_requirements >= 1


@pytest.mark.parametrize(
    "change,expected",
    [
        ("missing_case", "STALE_MAPPING"),
        ("signature_drift", "STALE_MAPPING"),
        ("invalid_receipt", "STALE_MAPPING"),
        ("rejected_case", "STALE_MAPPING"),
        ("pending_case", "PROPOSED_MAPPING"),
        ("pending_requirement", "PROPOSED_MAPPING"),
        ("pending_mapping", "PROPOSED_MAPPING"),
        ("unsupported", "UNSUPPORTED_AUTOMATION"),
        ("unknown_evidence", "INSUFFICIENT_EVIDENCE"),
        ("unknown_expectation", "INSUFFICIENT_EVIDENCE"),
    ],
)
def test_invalid_relationships_cannot_become_confirmed_automation(change, expected):
    document, context = supplied_requirements(), supplied_context()
    requirement, mapping, case = (
        document["requirements"][0],
        document["mappings"][0],
        context["cases"][0],
    )
    if change == "missing_case":
        context["cases"].pop(0)
    elif change == "signature_drift":
        case["signature"] = "d" * 64
    elif change == "invalid_receipt":
        case["receipt_valid"] = False
    elif change == "rejected_case":
        case["review_status"] = "rejected"
    elif change == "pending_case":
        case["review_status"] = "pending"
    elif change == "pending_requirement":
        requirement["review_status"] = "pending"
    elif change == "pending_mapping":
        mapping["review_status"] = "pending"
    elif change == "unsupported":
        case["supported"] = False
    elif change == "unknown_evidence":
        requirement["observed_evidence_ids"] = ["OBS-MISSING"]
    elif change == "unknown_expectation":
        requirement["expected_behavior"] = None
    row = finding(snapshot(document, context))
    assert expected in row.states
    assert row.confirmed_case_ids == []
    assert "CONFIRMED_REVIEWED_MAPPING" not in row.states


def test_rejected_requirement_is_excluded_and_generates_no_recommendation():
    document = supplied_requirements()
    document["requirements"][0]["review_status"] = "rejected"
    plan = snapshot(document)
    assert "EXCLUDED_REJECTED" in finding(plan).states
    assert not finding(plan).confirmed_case_ids
    assert all(p.requirement_id != "REQ-UI" for p in plan.proposals)
    assert plan.summary.excluded_rejected_requirements == 1


def test_scenario_design_uses_supplied_expectations_only():
    document = supplied_requirements()
    document["mappings"] = []
    plan = snapshot(document)
    ui = [p for p in plan.proposals if p.requirement_id == "REQ-UI"]
    assert {p.kind for p in ui} == {
        "positive",
        "negative",
        "boundary",
        "regression",
        "error_handling",
    }
    assert all(p.assumptions and p.evidence_ids and p.review_status == "pending" for p in ui)
    for proposal in ui:
        if proposal.kind == "positive":
            assert proposal.expected_behavior == "Owned product heading is shown"
        elif proposal.kind == "boundary":
            assert proposal.expected_behavior == "The supplied minimum is accepted"
        else:
            assert proposal.expected_behavior is None
        assert proposal.automation == "MANUAL_REVIEW"
    assert all(not hasattr(p, "selector") and not hasattr(p, "request") for p in ui)


def test_semantically_reordered_inputs_produce_identical_full_logical_plans():
    document, context = supplied_requirements(), supplied_context()
    original = snapshot(document, context).model_dump()
    document["sources"].reverse()
    document["evidence"].reverse()
    document["requirements"].reverse()
    document["mappings"].reverse()
    for requirement in document["requirements"]:
        for key in [
            "related_ids",
            "evidence_ids",
            "workflow_ids",
            "observed_evidence_ids",
            "design_hints",
        ]:
            requirement.get(key, []).reverse()
    context["cases"].reverse()
    context["workflow_ids"].reverse()
    context["evidence_ids"].reverse()
    for case in context["cases"]:
        case["pack_ids"].reverse()
        case["tags"].reverse()
    assert snapshot(document, context).model_dump() == original


def test_plan_changes_when_review_receipt_or_membership_state_changes():
    original = snapshot()
    for target, value in [
        ("receipt_valid", False),
        ("enabled", False),
        ("pack_ids", ["NEW-PACK"]),
        ("tags", ["new-tag"]),
    ]:
        context = supplied_context()
        context["cases"][0][target] = value
        assert snapshot(context=context).id != original.id
    context = supplied_context()
    context["suite_state"] = "STALE"
    assert snapshot(context=context).id != original.id


@pytest.mark.parametrize(
    "payload",
    [
        b"[]",
        b"null",
        b"true",
        b"42",
        b'"arbitrary text"',
        b"{",
        b"\xff",
        b'{"sources": [], "sources": []}',
        b'{"requirements": [{"id": "REQ-A", "id": "REQ-B"}]}',
        b'{"value": NaN}',
        b'{"value": Infinity}',
        b'{"value": -Infinity}',
        b'{"value": 1e9999}',
        b'{"unrecognized": "PRIVATE_INPUT_SENTINEL"}',
        b'{"unrecognized": ' + b"[" * 1500 + b"0" + b"]" * 1500 + b"}",
        b" " * (MAX_INPUT_BYTES + 1),
    ],
    ids=[
        "array",
        "null",
        "boolean",
        "number",
        "string",
        "broken-json",
        "invalid-utf8",
        "duplicate-root",
        "duplicate-nested",
        "nan",
        "infinity",
        "negative-infinity",
        "overflow-float",
        "unknown-secret-input",
        "deep-json",
        "oversize",
    ],
)
def test_untrusted_parser_inputs_fail_generically_without_echoing_payload(payload):
    with pytest.raises(ValueError) as caught:
        parse_requirements(payload)
    assert "PRIVATE_INPUT_SENTINEL" not in str(caught.value)
    assert len(str(caught.value)) < 500


@pytest.mark.parametrize(
    "change",
    [
        "unknown_source",
        "unknown_evidence",
        "duplicate_requirement",
        "duplicate_mapping",
        "self_relation",
        "unknown_relation",
        "approved_without_signature",
        "boolean_impact",
        "unknown_field",
        "oversized_text",
    ],
)
def test_invalid_declared_contracts_are_rejected_before_planning(change):
    document = supplied_requirements()
    requirement = document["requirements"][0]
    if change == "unknown_source":
        requirement["source_id"] = "SRC-ABSENT"
    elif change == "unknown_evidence":
        requirement["evidence_ids"] = ["SUP-ABSENT"]
    elif change == "duplicate_requirement":
        document["requirements"].append(copy.deepcopy(requirement))
    elif change == "duplicate_mapping":
        document["mappings"].append(copy.deepcopy(document["mappings"][0]))
    elif change == "self_relation":
        requirement["related_ids"] = [requirement["id"]]
    elif change == "unknown_relation":
        requirement["related_ids"] = ["REQ-ABSENT"]
    elif change == "approved_without_signature":
        document["mappings"][0].pop("case_signature")
    elif change == "boolean_impact":
        requirement["user_impact"] = True
    elif change == "unknown_field":
        requirement["execute_python"] = "PRIVATE_INPUT_SENTINEL"
    elif change == "oversized_text":
        requirement["description"] = "PRIVATE_INPUT_SENTINEL" * 200
    with pytest.raises(ValueError) as caught:
        parse_requirements(json.dumps(document).encode())
    assert "PRIVATE_INPUT_SENTINEL" not in str(caught.value)


def test_build_plan_never_mutates_inputs_or_performs_network_or_subprocess(monkeypatch):
    document = RequirementsDocument.model_validate(supplied_requirements())
    context = PlanningContext.model_validate(supplied_context())
    before = document.model_dump(), context.model_dump()

    def forbidden(*args, **kwargs):
        pytest.fail("Review-only planning attempted execution/network")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    plan = build_plan(document, context)
    assert (document.model_dump(), context.model_dump()) == before
    assert plan.execution_coverage == "NOT_ASSESSED"


def file_snapshot(root):
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.fixture
def reviewed_planning_project(project, tmp_path):
    authorization = AuthorizationContext(project.root, frozenset({"plan", "review"}))
    ui = LegacyCase(
        id="TC-UI",
        feature="Owned screen",
        title="Owned heading",
        description="Synthetic UI baseline",
        preconditions=["Owned demo only"],
        steps=["Observe heading"],
        expected="Owned heading",
        evidence=["synthetic page observation"],
        kind="heading",
        url="http://127.0.0.1:1/",
        target="Owned heading",
    )
    api = LegacyCase(
        id="TC-API",
        feature="Owned API",
        title="Owned health",
        description="Synthetic API baseline",
        preconditions=["Owned API only"],
        steps=["Read owned health"],
        expected="Reviewed status",
        evidence=[],
        kind="api",
        url="http://127.0.0.1:1/health",
        contract={
            "id": "TC-API",
            "title": "Owned health",
            "request": {"path": "/health"},
            "expect": {"status": 200},
            "environments": [
                {"name": "local", "origin": "http://127.0.0.1:1", "allow_localhost": True}
            ],
            "environment": "local",
        },
    )
    save_cases(project, [ui, api], authorization=authorization)
    approve(project, [ui.id, api.id], authorization=authorization)
    project.storage.write_json(
        "discovery/workflow-map.json",
        Discovery(
            workflows=[
                Workflow(
                    id="WF-UI",
                    name="Owned screen",
                    page_url=ui.url,
                    elements=[],
                    evidence=[],
                    steps=[],
                    status="OBSERVED",
                ),
                Workflow(
                    id="WF-API",
                    name="Owned API",
                    page_url=api.url,
                    elements=[],
                    evidence=[],
                    steps=[],
                    status="SOURCE",
                ),
            ],
            evidence_records=[
                EvidenceReference(id="OBS-UI", category="OBSERVED", description="Owned screen"),
                EvidenceReference(
                    id="OBS-API", category="SOURCE", description="Owned API declaration"
                ),
            ],
        ).model_dump(),
    )
    suite = propose(project)
    suite.cases[0].tags = [" business critical ", ""]
    suite.packs[0].case_ids = ["TC-UI"]
    approve_suite(project, suite, authorization)
    document = supplied_requirements()
    cases = {c.id: c for c in project.cases()}
    for mapping in document["mappings"]:
        mapping["case_signature"] = case_signature(cases[mapping["case_id"]])
    document["requirements"].append(
        {
            "id": "REQ-GAP",
            "title": "Unmapped reviewed requirement",
            "description": "A deliberately unmapped synthetic requirement for proposal review.",
            "source_id": "SRC-UI",
            "review_status": "approved",
            "expected_behavior": "Reviewed behavior still needs a reviewed test mapping",
        }
    )
    source = tmp_path / "owned-requirements.json"
    source.write_text(json.dumps(document), encoding="utf-8")
    return project, authorization, source


def test_analyze_is_readonly_and_ignores_fake_run_claims(reviewed_planning_project):
    project, authorization, source = reviewed_planning_project
    project.storage.write_json(
        "reports/latest-run.json", {"counts": {"PASSED": 999}, "coverage": 100}
    )
    before = file_snapshot(project.root)
    entries_before = {p.relative_to(project.root).as_posix() for p in project.root.rglob("*")}
    source_before = source.read_bytes(), source.stat().st_mtime_ns
    service = planning_service(project, authorization)
    first = service.analyze(source)
    assert first.summary.confirmed_mapped_requirements == 2
    assert first.execution_coverage == "NOT_ASSESSED"
    assert first.summary.missing_requirements == 1
    assert sorted(next(c for c in first.context.cases if c.id == "TC-UI").tags) == [
        "",
        " business critical ",
    ]
    assert file_snapshot(project.root) == before
    assert {
        p.relative_to(project.root).as_posix() for p in project.root.rglob("*")
    } == entries_before
    assert (source.read_bytes(), source.stat().st_mtime_ns) == source_before
    assert not (project.root / "test-cases/requirements-v07.json").exists()
    assert service.analyze(source).model_dump() == first.model_dump()


def test_absent_requirements_fail_without_inventing_inventory(project):
    before = file_snapshot(project.root)
    with pytest.raises(ValueError):
        planning_service(project).analyze()
    assert file_snapshot(project.root) == before


@pytest.mark.parametrize("context_kind", ["none", "wrong-project", "wrong-operation"])
def test_import_rejects_unauthorized_intent_before_io(
    reviewed_planning_project, context_kind, monkeypatch
):
    project, _, source = reviewed_planning_project
    authorization = {
        "none": None,
        "wrong-project": AuthorizationContext(project.root / "other", frozenset({"plan"})),
        "wrong-operation": AuthorizationContext(project.root, frozenset({"review"})),
    }[context_kind]
    before = file_snapshot(project.root)

    def forbidden_read(*args, **kwargs):
        pytest.fail("Unauthorized import read its external requirements")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    with pytest.raises(ValueError, match="Explicit"):
        planning_service(project, authorization).import_requirements(source)
    monkeypatch.undo()
    assert file_snapshot(project.root) == before


def test_planning_review_never_grants_scenario_approval_and_stales_on_case_drift(
    reviewed_planning_project,
):
    project, authorization, source = reviewed_planning_project
    service = planning_service(project, authorization)
    before = file_snapshot(project.root)
    service.import_requirements(source)
    plan = service.analyze()
    assert plan.proposals, "The acceptance requires reviewable design proposals"
    accepted_id = plan.proposals[0].id
    reviewed = service.review(plan.id, [accepted_id], "accepted")
    assert reviewed.review_state == "CURRENT"
    assert reviewed.id == plan.id
    assert reviewed.summary == plan.summary and reviewed.findings == plan.findings
    assert service.analyze().model_dump() == reviewed.model_dump()
    assert next(p for p in reviewed.proposals if p.id == accepted_id).review_status == "accepted"
    after = file_snapshot(project.root)
    assert {name for name in after if name not in before} == {
        "test-cases/requirements-v07.json",
        "test-cases/planning-review-v07.json",
    }
    assert all(after[name] == value for name, value in before.items())
    for case in project.cases():
        verify_approval_binding(project, case)
    cases = project.cases()
    cases[0].expected = "Legitimately changed reviewed behavior"
    save_cases(project, cases, authorization=authorization)
    before_stale = file_snapshot(project.root)
    stale = service.analyze()
    assert stale.id != plan.id and stale.review_state == "STALE"
    assert all(p.review_status == "pending" for p in stale.proposals)
    assert "STALE_MAPPING" in finding(stale).states
    assert file_snapshot(project.root) == before_stale
    with pytest.raises(ValueError):
        service.review(plan.id, [accepted_id], "accepted")
    assert file_snapshot(project.root) == before_stale
    with pytest.raises(ValueError):
        verify_approval_binding(project, project.cases()[0])


@pytest.mark.parametrize(
    "mode", ["empty", "duplicate", "unknown", "invalid-decision", "unauthorized"]
)
def test_invalid_plan_review_is_atomic_and_preserves_historical_data(
    reviewed_planning_project, mode
):
    project, authorization, source = reviewed_planning_project
    service = planning_service(project, authorization)
    service.import_requirements(source)
    plan = service.analyze()
    ids, decision = [plan.proposals[0].id], "accepted"
    if mode == "empty":
        ids = []
    elif mode == "duplicate":
        ids *= 2
    elif mode == "unknown":
        ids = ["PROP-" + "0" * 20]
    elif mode == "invalid-decision":
        decision = "approved"
    else:
        service = planning_service(project, AuthorizationContext(project.root, frozenset({"plan"})))
    before = file_snapshot(project.root)
    with pytest.raises(ValueError):
        service.review(plan.id, ids, decision)
    assert file_snapshot(project.root) == before


@pytest.mark.parametrize(
    "inventory", ["test-cases/test-matrix.json", "discovery/workflow-map.json"]
)
def test_present_malformed_legacy_inventory_fails_without_writes(
    reviewed_planning_project, inventory
):
    project, authorization, source = reviewed_planning_project
    path = project.root / inventory
    path.write_bytes(b'{"private": "PRIVATE_INPUT_SENTINEL", "private": 2}')
    before = file_snapshot(project.root)
    with pytest.raises(ValueError) as caught:
        planning_service(project, authorization).analyze(source)
    assert "PRIVATE_INPUT_SENTINEL" not in str(caught.value)
    assert file_snapshot(project.root) == before


def test_failed_requirement_import_preserves_existing_sidecar_and_legacy_data(
    reviewed_planning_project,
):
    project, authorization, source = reviewed_planning_project
    service = planning_service(project, authorization)
    service.import_requirements(source)
    before = file_snapshot(project.root)
    source.write_bytes(b'{"PRIVATE_INPUT_SENTINEL": NaN}')
    with pytest.raises(ValueError) as caught:
        service.import_requirements(source)
    assert "PRIVATE_INPUT_SENTINEL" not in str(caught.value)
    assert file_snapshot(project.root) == before


@pytest.mark.parametrize("mode", ["oversize", "symlink", "junction"])
def test_requirements_file_bounds_and_links_fail_before_sidecar_write(
    reviewed_planning_project, mode, monkeypatch
):
    project, authorization, source = reviewed_planning_project
    service = planning_service(project, authorization)
    before = file_snapshot(project.root)
    if mode == "oversize":
        source.write_bytes(b" " * (MAX_INPUT_BYTES + 1))
    else:
        method = "is_symlink" if mode == "symlink" else "is_junction"
        original = getattr(Path, method)
        monkeypatch.setattr(Path, method, lambda self: self == source or original(self))
    with pytest.raises(ValueError):
        service.import_requirements(source)
    assert file_snapshot(project.root) == before


@pytest.mark.parametrize(
    "inventory,limit",
    [
        ("test-cases/test-matrix.json", 5_000_000),
        ("discovery/workflow-map.json", 5_000_000),
        ("test-cases/management.json", 1_000_000),
        ("test-cases/planning-review-v07.json", 1_000_000),
    ],
)
def test_oversized_current_inventory_fails_before_writes(
    reviewed_planning_project, inventory, limit
):
    project, authorization, source = reviewed_planning_project
    (project.root / inventory).write_bytes(b" " * (limit + 1))
    before = file_snapshot(project.root)
    with pytest.raises(ValueError):
        planning_service(project, authorization).analyze(source)
    assert file_snapshot(project.root) == before


def test_invalid_current_receipt_is_reported_without_repair_or_approval(reviewed_planning_project):
    project, authorization, source = reviewed_planning_project
    receipts = project.storage.read_json("test-cases/approval-receipts.json")
    receipts["TC-UI"]["scenario_signature"] = "d" * 64
    project.storage.write_json("test-cases/approval-receipts.json", receipts)
    before = file_snapshot(project.root)
    plan = planning_service(project, authorization).analyze(source)
    assert "STALE_MAPPING" in finding(plan).states
    assert not finding(plan).confirmed_case_ids
    assert next(c for c in plan.context.cases if c.id == "TC-UI").receipt_valid is False
    assert file_snapshot(project.root) == before


def test_stale_suite_never_supplies_current_reviewed_membership(reviewed_planning_project):
    project, authorization, source = reviewed_planning_project
    suite = project.storage.read_json("test-cases/management.json")
    suite["cases"][0]["tags"] = ["unreviewed-tag"]
    project.storage.write_json("test-cases/management.json", suite)
    before = file_snapshot(project.root)
    plan = planning_service(project, authorization).analyze(source)
    assert plan.context.suite_state == "STALE"
    assert all("unreviewed-tag" not in c.tags for c in plan.context.cases)
    assert file_snapshot(project.root) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("description", "ghp_" + "A" * 36),
        ("description", "-----BEGIN " + "PRIVATE KEY-----"),
        ("description", "synthetic\x00control"),
        ("user_impact", -1),
        ("business_criticality", 6),
    ],
)
def test_credential_control_and_out_of_range_input_is_rejected_generically(field, value):
    document = supplied_requirements()
    document["requirements"][0][field] = value
    with pytest.raises(ValueError) as caught:
        parse_requirements(json.dumps(document).encode())
    assert str(value) not in str(caught.value)


def test_python_and_markup_in_requirements_remain_inert_data(tmp_path):
    marker = tmp_path / "MUST-NOT-BE-CREATED"
    payload = f"__import__('pathlib').Path({str(marker)!r}).write_text('executed')"
    document = supplied_requirements()
    document["requirements"][0]["expected_behavior"] = payload
    document["requirements"][0]["description"] = (
        "[red]synthetic[/red] <script>never_execute()</script>"
    )
    parsed = parse_requirements(json.dumps(document).encode())
    plan = build_plan(parsed, PlanningContext.model_validate(supplied_context()))
    assert (
        plan.requirements.requirements[
            1 if plan.requirements.requirements[0].id != "REQ-UI" else 0
        ].expected_behavior
        == payload
    )
    assert not marker.exists()


@pytest.mark.parametrize(
    "kind", ["duplicate-cases", "too-many-cases", "too-many-workflows", "too-many-evidence"]
)
def test_current_inventory_identity_and_count_bounds_are_enforced(reviewed_planning_project, kind):
    project, authorization, source = reviewed_planning_project
    if kind in {"duplicate-cases", "too-many-cases"}:
        data = project.storage.read_json("test-cases/test-matrix.json")
        if kind == "duplicate-cases":
            data.append(copy.deepcopy(data[0]))
        else:
            data = [{**data[0], "id": f"TC-N{index}"} for index in range(1001)]
        project.storage.write_json("test-cases/test-matrix.json", data)
    else:
        data = project.storage.read_json("discovery/workflow-map.json")
        field, count = (
            ("workflows", 2001) if kind == "too-many-workflows" else ("evidence_records", 5001)
        )
        template = data[field][0]
        data[field] = [{**template, "id": f"ITEM-{index}"} for index in range(count)]
        project.storage.write_json("discovery/workflow-map.json", data)
    before = file_snapshot(project.root)
    with pytest.raises(ValueError):
        planning_service(project, authorization).analyze(source)
    assert file_snapshot(project.root) == before


def test_repeated_observed_ids_are_deduplicated_without_touching_discovery(
    reviewed_planning_project,
):
    project, authorization, source = reviewed_planning_project
    discovery = project.storage.read_json("discovery/workflow-map.json")
    discovery["evidence_records"] *= 2
    project.storage.write_json("discovery/workflow-map.json", discovery)
    before = file_snapshot(project.root)
    plan = planning_service(project, authorization).analyze(source)
    assert plan.context.workflow_ids == ["WF-API", "WF-UI"]
    assert plan.context.evidence_ids == ["OBS-API", "OBS-UI"]
    assert plan.summary.confirmed_mapped_requirements == 2
    assert file_snapshot(project.root) == before


def test_duplicate_workflow_inventory_is_rejected_atomically(reviewed_planning_project):
    project, authorization, source = reviewed_planning_project
    discovery = project.storage.read_json("discovery/workflow-map.json")
    discovery["workflows"] *= 2
    project.storage.write_json("discovery/workflow-map.json", discovery)
    before = file_snapshot(project.root)
    with pytest.raises(ValueError):
        planning_service(project, authorization).analyze(source)
    assert file_snapshot(project.root) == before


def test_import_serialization_cannot_leave_an_unreadable_requirements_sidecar(
    reviewed_planning_project,
):
    project, authorization, source = reviewed_planning_project
    document = {
        "sources": [
            {"id": f"SRC-{i}", "reference": "r" * 2000, "description": "s" * 2000}
            for i in range(10)
        ],
        "requirements": [
            {"id": f"REQ-{i}", "title": "Owned", "description": "q" * 2000, "source_id": "SRC-0"}
            for i in range(100)
        ],
    }
    payload = json.dumps(document, separators=(",", ":")).encode()
    assert len(payload) < MAX_INPUT_BYTES
    parsed = parse_requirements(payload)
    assert len(json.dumps(parsed.model_dump(), indent=2).encode()) > MAX_INPUT_BYTES
    source.write_bytes(payload)
    before = file_snapshot(project.root)
    service = planning_service(project, authorization)
    try:
        service.import_requirements(source)
    except ValueError:
        assert file_snapshot(project.root) == before
    else:
        # Compact storage is also valid, provided the imported document remains readable.
        assert service.analyze().requirements == parsed


def test_proposal_identity_changes_only_with_its_requirement_or_hint_content():
    document = supplied_requirements()
    document["mappings"] = []
    first = snapshot(document)
    document["requirements"][0]["title"] = "Changed reviewed requirement wording"
    second = snapshot(document)
    assert second.id != first.id
    before_ui = {p.id for p in first.proposals if p.requirement_id == "REQ-UI"}
    after_ui = {p.id for p in second.proposals if p.requirement_id == "REQ-UI"}
    assert before_ui.isdisjoint(after_ui)
    assert {p.id for p in first.proposals if p.requirement_id == "REQ-API"} == {
        p.id for p in second.proposals if p.requirement_id == "REQ-API"
    }
    assert all(p.review_status == "pending" for p in second.proposals)
