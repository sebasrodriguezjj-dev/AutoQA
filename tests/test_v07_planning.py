"""Pure V0.7 requirement planning acceptance and deterministic review boundaries."""

import copy
import json

import pytest

from autoqa.planning_contracts import MAX_INPUT_BYTES, PlanningContext, RequirementsDocument
from autoqa.qa_planning import build_plan, parse_requirements

SIGNATURE = "a" * 64


def requirement(id="REQ-UI", **changes):
    value = {
        "id": id,
        "title": "Owned catalog lookup",
        "description": "The supplied fixture requirement",
        "source_id": "SRC-OWNER",
        "review_status": "approved",
        "expected_behavior": "Return the explicitly reviewed fixture item",
    }
    value.update(changes)
    return value


def document(requirements=None, mappings=None, **changes):
    value = {
        "sources": [
            {
                "id": "SRC-OWNER",
                "reference": "Synthetic owner specification",
                "description": "Owned fixture",
            }
        ],
        "requirements": requirements or [requirement()],
        "mappings": mappings or [],
    }
    value.update(changes)
    return RequirementsDocument.model_validate(value)


def mapping(requirement_id="REQ-UI", case_id="TC-UI", **changes):
    value = {
        "requirement_id": requirement_id,
        "case_id": case_id,
        "case_signature": SIGNATURE,
        "review_status": "approved",
        "rationale": "The owner explicitly reviewed this relationship",
    }
    value.update(changes)
    return value


def case(id="TC-UI", **changes):
    value = {
        "id": id,
        "signature": SIGNATURE,
        "review_status": "approved",
        "receipt_valid": True,
        "supported": True,
        "kind": "functional",
        "title": "Existing owned case",
    }
    value.update(changes)
    return value


def context(cases=None, **changes):
    value = {"project_id": "owned", "cases": cases or []}
    value.update(changes)
    return PlanningContext.model_validate(value)


def test_reviewed_ui_api_missing_and_unsupported_are_separate_from_execution():
    requirements = [
        requirement(),
        requirement("REQ-API", kind="API"),
        requirement("REQ-MISSING"),
        requirement("REQ-MANUAL"),
    ]
    mappings = [mapping(), mapping("REQ-API", "TC-API"), mapping("REQ-MANUAL", "TC-MANUAL")]
    ctx = context(
        [case(), case("TC-API", kind="api"), case("TC-MANUAL", kind="manual", supported=False)]
    )
    plan = build_plan(document(requirements, mappings), ctx)
    rows = {row.requirement_id: row for row in plan.findings}
    assert rows["REQ-UI"].confirmed_case_ids == ["TC-UI"]
    assert rows["REQ-API"].confirmed_case_ids == ["TC-API"]
    assert rows["REQ-MISSING"].states == ["MISSING_MAPPING"]
    assert rows["REQ-MANUAL"].states == ["UNSUPPORTED_AUTOMATION"]
    assert rows["REQ-MANUAL"].confirmed_case_ids == []
    assert plan.summary.confirmed_mapped_requirements == 2
    assert plan.summary.total_requirements == 4
    assert plan.summary.missing_requirements == plan.summary.unsupported_requirements == 1
    assert plan.coverage_scope == "SUPPLIED_REQUIREMENTS_ONLY"
    assert plan.execution_coverage == "NOT_ASSESSED"
    output = plan.model_dump()
    assert "percentage" not in output and "execution_results" not in output


@pytest.mark.parametrize(
    "requirement_changes,mapping_changes,case_changes,expected_state",
    [
        ({"review_status": "pending"}, {}, {}, "PROPOSED_MAPPING"),
        ({}, {"review_status": "pending", "case_signature": None}, {}, "PROPOSED_MAPPING"),
        ({}, {}, {"review_status": "pending", "receipt_valid": False}, "PROPOSED_MAPPING"),
        ({}, {}, {"receipt_valid": False}, "STALE_MAPPING"),
        ({}, {"case_signature": "b" * 64}, {}, "STALE_MAPPING"),
        ({}, {}, {"review_status": "rejected"}, "STALE_MAPPING"),
        ({"expected_behavior": None}, {}, {}, "PROPOSED_MAPPING"),
        ({"workflow_ids": ["WF-UNKNOWN"]}, {}, {}, "PROPOSED_MAPPING"),
        ({"observed_evidence_ids": ["OBS-MISSING"]}, {}, {}, "PROPOSED_MAPPING"),
    ],
)
def test_unreviewed_stale_unknown_relationships_never_confirm(
    requirement_changes, mapping_changes, case_changes, expected_state
):
    plan = build_plan(
        document([requirement(**requirement_changes)], [mapping(**mapping_changes)]),
        context([case(**case_changes)]),
    )
    row = plan.findings[0]
    assert row.confirmed_case_ids == []
    assert expected_state in row.states
    assert plan.summary.confirmed_mapped_requirements == 0
    if requirement_changes:
        assert "INSUFFICIENT_EVIDENCE" in row.states


def test_unknown_case_and_rejected_mapping_fail_closed():
    missing = build_plan(document(mappings=[mapping()]), context())
    assert missing.findings[0].states == ["STALE_MAPPING"]
    rejected = build_plan(document(mappings=[mapping(review_status="rejected")]), context([case()]))
    assert rejected.findings[0].states == ["MISSING_MAPPING"]
    assert rejected.summary.confirmed_mapped_requirements == 0


def test_rejected_requirement_excluded_without_proposals():
    plan = build_plan(
        document([requirement(review_status="rejected")], [mapping()]), context([case()])
    )
    assert plan.findings[0].states == ["EXCLUDED_REJECTED"]
    assert plan.proposals == []
    assert plan.summary.excluded_rejected_requirements == 1
    assert plan.summary.reviewed_requirements == plan.summary.confirmed_mapped_requirements == 0


def test_risk_is_exact_explainable_and_unknown_expectations_are_not_invented():
    req = requirement(
        business_criticality=5,
        user_impact=5,
        priority="Critical",
        workflow_ids=["WF-1"],
        review_status="pending",
    )
    plan = build_plan(
        document([req], [mapping(review_status="pending")]),
        context([case()], workflow_ids=["WF-1"], workflow_provenance={"WF-1": "OBSERVED"}),
    )
    risk = plan.findings[0].risk
    assert risk.factors == {
        "business_criticality": 20,
        "user_impact": 20,
        "priority": 15,
        "coverage_gap": 15,
        "observed_functionality": 10,
        "execution_feasibility": 10,
        "uncertainty": 10,
    }
    assert risk.score == 100 and risk.level == "High" and risk.reasons
    assert {p.kind for p in plan.proposals} == {
        "positive",
        "negative",
        "boundary",
        "regression",
        "error_handling",
    }
    for proposal in plan.proposals:
        assert proposal.automation == "MANUAL_REVIEW" and proposal.review_status == "pending"
        assert proposal.assumptions
        if proposal.kind != "positive":
            assert proposal.expected_behavior is None
            assert any("UNKNOWN" in assumption for assumption in proposal.assumptions)


def test_design_hints_preserve_only_explicit_expected_behavior_and_source_refs():
    req = requirement(
        evidence_ids=["EVD-1"],
        design_hints=[
            {
                "kind": "negative",
                "condition": "Owner supplied invalid code",
                "expected_behavior": "Owner-defined rejection",
            },
            {
                "kind": "boundary",
                "condition": "Owner-specified minimum value",
                "expected_behavior": None,
            },
        ],
    )
    plan = build_plan(
        document(
            [req],
            evidence=[
                {"id": "EVD-1", "source_id": "SRC-OWNER", "description": "Reviewed source record"}
            ],
        ),
        context(),
    )
    proposals = {p.kind: p for p in plan.proposals}
    assert proposals["negative"].intent == "Owner supplied invalid code"
    assert proposals["negative"].expected_behavior == "Owner-defined rejection"
    assert proposals["boundary"].expected_behavior is None
    assert all(p.evidence_ids == ["EVD-1"] for p in plan.proposals)
    assert all(p.review_status == "pending" for p in plan.proposals)


def test_logically_identical_reordered_inputs_produce_identical_snapshot_without_mutation():
    reqs = [
        requirement(),
        requirement(
            "REQ-API",
            related_ids=["REQ-UI"],
            kind="API",
            workflow_ids=["WF-2", "WF-1"],
            design_hints=[
                {"kind": "boundary", "condition": "Lower owner boundary"},
                {"kind": "negative", "condition": "Invalid owner input"},
            ],
        ),
    ]
    doc = document(reqs, [mapping(), mapping("REQ-API", "TC-API")])
    ctx = context(
        [
            case(pack_ids=["Regression Pack", "Smoke Pack"], tags=["UI tag", "Owner tag"]),
            case("TC-API", kind="api"),
        ],
        workflow_ids=["WF-2", "WF-1"],
        evidence_ids=["OBS-2", "OBS-1"],
        workflow_provenance={"WF-2": "OBSERVED", "WF-1": "OBSERVED"},
        evidence_provenance={"OBS-2": "OBSERVED", "OBS-1": "OBSERVED"},
        suite_id="Owner Suite",
        suite_state="CURRENT",
        suite_digest="d" * 64,
    )
    before = (doc.model_dump(), ctx.model_dump())
    doc_data, ctx_data = copy.deepcopy(before)
    doc_data["requirements"].reverse()
    doc_data["mappings"].reverse()
    doc_data["requirements"][0]["workflow_ids"].reverse()
    doc_data["requirements"][0]["design_hints"].reverse()
    ctx_data["cases"].reverse()
    ctx_data["cases"][1]["pack_ids"].reverse()
    ctx_data["cases"][1]["tags"].reverse()
    ctx_data["workflow_ids"].reverse()
    ctx_data["evidence_ids"].reverse()
    first = build_plan(doc, ctx)
    second = build_plan(
        RequirementsDocument.model_validate(doc_data), PlanningContext.model_validate(ctx_data)
    )
    assert first.model_dump() == second.model_dump()
    assert first.id == "PLAN-" + first.input_digest
    assert before == (doc.model_dump(), ctx.model_dump())


@pytest.mark.parametrize(
    "changes",
    [
        {"title": "Changed owner requirement"},
        {"expected_behavior": "Changed owner expectation"},
        {"priority": "High"},
    ],
)
def test_changed_requirement_has_new_plan_and_proposal_identities(changes):
    first = build_plan(document(), context())
    second = build_plan(document([requirement(**changes)]), context())
    assert first.id != second.id
    assert {p.id for p in first.proposals}.isdisjoint({p.id for p in second.proposals})


@pytest.mark.parametrize(
    "changes",
    [
        {"receipt_valid": False},
        {"signature": "b" * 64},
        {"review_status": "pending"},
        {"enabled": False},
        {"tags": ["new tag"]},
    ],
)
def test_changed_current_case_state_invalidates_plan_review_identity(changes):
    first = build_plan(document(mappings=[mapping()]), context([case()]))
    second = build_plan(document(mappings=[mapping()]), context([case(**changes)]))
    assert first.id != second.id


def test_stale_suite_is_disclosed_and_current_membership_is_not_invented():
    plan = build_plan(document(), context(suite_state="STALE", suite_digest="c" * 64))
    assert plan.context.suite_state == "STALE"
    assert any("Suite membership is stale" in value for value in plan.limitations)
    assert plan.context.cases == []


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"null",
        b"[]",
        b"{}",
        b"{broken",
        b"\xff",
        b'{"a":1,"a":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b"[" * 2000 + b"]" * 2000,
        b" " * (MAX_INPUT_BYTES + 1),
    ],
)
def test_parser_refuses_invalid_or_resource_exhausting_payload_without_echo(payload):
    with pytest.raises(ValueError) as error:
        parse_requirements(payload)
    assert str(error.value) in {
        "Invalid V0.7 requirements document",
        "Requirements input must be 1-256000 UTF-8 JSON bytes",
    }


def test_parser_accepts_bom_and_never_executes_requirement_text(tmp_path):
    marker = tmp_path / "never-created"
    supplied = document(
        [requirement(description=f"__import__('pathlib').Path({str(marker)!r}).touch()")]
    ).model_dump()
    plan = build_plan(
        parse_requirements(b"\xef\xbb\xbf" + json.dumps(supplied).encode()), context()
    )
    assert (
        plan.requirements.requirements[0].description == supplied["requirements"][0]["description"]
    )
    assert not marker.exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate-requirement",
        "unknown-source",
        "unknown-evidence",
        "unknown-related",
        "unknown-mapping",
        "unexpected-field",
        "strict-integer",
        "duplicate-mapping",
    ],
)
def test_parser_enforces_relationships_and_strict_contracts(mutation):
    payload = document(mappings=[mapping()]).model_dump()
    if mutation == "duplicate-requirement":
        payload["requirements"] *= 2
    elif mutation == "unknown-source":
        payload["requirements"][0]["source_id"] = "SRC-MISSING"
    elif mutation == "unknown-evidence":
        payload["requirements"][0]["evidence_ids"] = ["EVD-MISSING"]
    elif mutation == "unknown-related":
        payload["requirements"][0]["related_ids"] = ["REQ-MISSING"]
    elif mutation == "unknown-mapping":
        payload["mappings"][0]["requirement_id"] = "REQ-MISSING"
    elif mutation == "unexpected-field":
        payload["requirements"][0]["execute"] = "untrusted"
    elif mutation == "strict-integer":
        payload["requirements"][0]["user_impact"] = True
    else:
        payload["mappings"] *= 2
    with pytest.raises(ValueError, match="Invalid V0.7 requirements document"):
        parse_requirements(json.dumps(payload).encode())


def test_stale_unsupported_mapping_keeps_both_limitations_visible():
    plan = build_plan(
        document(mappings=[mapping()]),
        context([case(kind="manual", supported=False, receipt_valid=False)]),
    )
    row = plan.findings[0]
    assert set(row.states) == {"STALE_MAPPING", "UNSUPPORTED_AUTOMATION"}
    assert row.stale_case_ids == row.unsupported_case_ids == ["TC-UI"]
    assert row.confirmed_case_ids == []
    assert plan.summary.stale_requirements == plan.summary.unsupported_requirements == 1


def test_rejected_relationship_is_not_execution_feasibility_evidence():
    plan = build_plan(document(mappings=[mapping(review_status="rejected")]), context([case()]))
    assert plan.findings[0].risk.factors["execution_feasibility"] == 0


@pytest.mark.parametrize("reference_kind", ["workflow", "evidence"])
@pytest.mark.parametrize(
    "provenance", ["SOURCE", "INFERRED", "VERIFIED_REQUIREMENT", "UNKNOWN", None]
)
def test_declared_reference_without_observed_provenance_never_confirms(reference_kind, provenance):
    reference = "WF-1" if reference_kind == "workflow" else "OBS-1"
    requirement_field = "workflow_ids" if reference_kind == "workflow" else "observed_evidence_ids"
    context_field = "workflow_ids" if reference_kind == "workflow" else "evidence_ids"
    provenance_field = (
        "workflow_provenance" if reference_kind == "workflow" else "evidence_provenance"
    )
    fields = {context_field: [reference]}
    if provenance is not None:
        fields[provenance_field] = {reference: provenance}
    plan = build_plan(
        document([requirement(**{requirement_field: [reference]})], [mapping()]),
        context([case()], **fields),
    )
    finding = plan.findings[0]
    assert finding.confirmed_case_ids == []
    assert set(finding.states) == {"PROPOSED_MAPPING", "INSUFFICIENT_EVIDENCE"}
    assert finding.risk.factors["observed_functionality"] == 0
    assert finding.risk.factors["uncertainty"] == 10
    assert plan.summary.confirmed_mapped_requirements == 0
    assert plan.summary.uncertain_requirements == 1


def test_only_actual_observed_references_support_mapping_and_risk():
    req = requirement(workflow_ids=["WF-1"], observed_evidence_ids=["OBS-1"])
    actual = context(
        [case()],
        workflow_ids=["WF-1"],
        evidence_ids=["OBS-1"],
        workflow_provenance={"WF-1": "OBSERVED"},
        evidence_provenance={"OBS-1": "OBSERVED"},
    )
    observed_plan = build_plan(document([req], [mapping()]), actual)
    assert observed_plan.findings[0].confirmed_case_ids == ["TC-UI"]
    assert observed_plan.findings[0].risk.factors["observed_functionality"] == 10
    for field in ["workflow_provenance", "evidence_provenance"]:
        values = actual.model_dump()
        values[field] = {key: "SOURCE" for key in values[field]}
        source_plan = build_plan(
            document([req], [mapping()]), PlanningContext.model_validate(values)
        )
        assert source_plan.id != observed_plan.id
        assert source_plan.findings[0].confirmed_case_ids == []
        assert "INSUFFICIENT_EVIDENCE" in source_plan.findings[0].states
        assert source_plan.findings[0].risk.factors["observed_functionality"] == 0
