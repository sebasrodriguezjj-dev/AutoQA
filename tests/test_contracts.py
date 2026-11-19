import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from autoqa.core import (
    Discovery,
    Element,
    EvidenceReference,
    LocatorCandidate,
    PageEvidence,
    save_json,
)
from autoqa.core import TestCase as Case
from autoqa.functional import (
    BehaviorContract,
    functional_case,
    render_functional,
    validate_contract,
)
from autoqa.reporting import report


@pytest.fixture
def contract_evidence():
    field = Element(
        id="EL-search",
        kind="input",
        name="Find",
        input_type="search",
        locators=[LocatorCandidate(strategy="label", value="Find", count=1)],
    )
    results = Element(
        id="EL-results",
        kind="a",
        name="Observed item",
        locators=[LocatorCandidate(strategy="test_id", value="observed-title", count=3)],
    )
    page = PageEvidence(
        url="http://127.0.0.1:8001/inventory",
        title="Inventory",
        headings=["Inventory"],
        elements=[field, results],
        screenshot="page.png",
        depth=0,
    )
    discovery = Discovery(
        pages=[page],
        evidence_records=[
            EvidenceReference(id=e.id, category="OBSERVED", description=e.name)
            for e in page.elements
        ],
    )
    raw = {
        "id": "search-fixture",
        "title": "Search fixture",
        "page_url": page.url,
        "workflow": "search",
        "test_type": "Positive",
        "basis": "VERIFIED_REQUIREMENT",
        "source": "Controlled test requirement",
        "evidence_ids": [field.id, results.id],
        "steps": [{"action": "fill", "element_id": field.id, "value": "Approved query"}],
        "assertions": [{"check": "texts", "element_id": results.id, "expected": ["Observed item"]}],
    }
    return discovery, raw


def test_ambiguous_action_locator_rejected(contract_evidence):
    discovery, raw = contract_evidence
    discovery.pages[0].elements[0].locators[0].count = 2
    with pytest.raises(ValueError, match="unique"):
        validate_contract(BehaviorContract.model_validate(raw), discovery, local=True)


def test_unknown_selection_rejected(contract_evidence):
    discovery, raw = contract_evidence
    field = discovery.pages[0].elements[0]
    field.kind, field.input_type = "select", None
    field.options = [{"value": "known", "label": "Known"}]
    raw["steps"] = [{"action": "select", "element_id": field.id, "value": "invented"}]
    with pytest.raises(ValueError, match="option evidence"):
        validate_contract(BehaviorContract.model_validate(raw), discovery, local=True)


@pytest.mark.parametrize("name", ["Password", "API key", "Access token", "Checkout", "Delete item"])
def test_sensitive_or_dangerous_controls_rejected(contract_evidence, name):
    discovery, raw = contract_evidence
    discovery.pages[0].elements[0].name = name
    with pytest.raises(ValueError):
        validate_contract(BehaviorContract.model_validate(raw), discovery, local=True)


def test_generic_visibility_cannot_validate_search(contract_evidence):
    discovery, raw = contract_evidence
    raw["assertions"] = [{"check": "visible", "element_id": "EL-search", "expected": ""}]
    with pytest.raises(ValueError, match="behavioral result"):
        validate_contract(BehaviorContract.model_validate(raw), discovery, local=True)


def test_unknown_actions_and_unsafe_ids_rejected(contract_evidence):
    _, raw = contract_evidence
    raw["steps"][0]["action"] = "shell"
    with pytest.raises(ValidationError):
        BehaviorContract.model_validate(raw)
    with pytest.raises(ValidationError):
        Case(
            id="TC-1():\n import os",
            feature="x",
            title="x",
            description="x",
            preconditions=[],
            steps=[],
            expected="x",
            evidence=[],
            kind="heading",
            url="http://example.test",
        )


def test_user_text_remains_data_and_contract_drift_rejected(contract_evidence):
    discovery, raw = contract_evidence
    raw["steps"][0]["value"] = "'); __import__('os').system('unsafe'); #"
    contract = BehaviorContract.model_validate(raw)
    case = functional_case(contract, discovery, local=True)
    source = render_functional(case, discovery, local=True)
    module = ast.parse("def test_case(page):\n" + source)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "__import__"
        for node in ast.walk(module)
    )
    case.expected = "An unrelated expectation"
    with pytest.raises(ValueError, match="differs"):
        render_functional(case, discovery, local=True)


def test_report_uses_run_snapshot_after_plan_changes(project, contract_evidence):
    discovery, raw = contract_evidence
    case = functional_case(BehaviorContract.model_validate(raw), discovery, local=True)
    case.review_status = "approved"
    save_json(project.root / "discovery/workflow-map.json", discovery.model_dump())
    save_json(project.root / "test-cases/test-matrix.json", [])
    result = {
        "run_id": "snapshot-fixture",
        "created_at": "2026-11-18",
        "duration": 1,
        "exit_code": 0,
        "base_url": case.url,
        "artifact_dir": "artifacts/snapshot-fixture",
        "records": [
            {
                "id": case.id,
                "name": "test_TC_F_search_fixture",
                "status": "PASSED",
                "error": "",
                "duration": 1,
            }
        ],
        "planning_snapshot": [case.model_dump()],
        "case_snapshot": [case.model_dump()],
        "discovery_snapshot": discovery.model_dump(),
    }
    save_json(project.root / "reports/latest-run.json", result)
    from autoqa.core import load_json

    payload = load_json(Path(report(project, "json")))
    assert payload["approved"] == payload["proposed"] == payload["functional_validated"] == 1
    assert payload["pages_analyzed"] == 1


def test_report_before_execution_is_explicit(project, contract_evidence):
    discovery, _ = contract_evidence
    discovery.blocked_requests = [
        {"origin": "https://example.test", "method": "GET", "reason": "Out of scope"}
    ] * 2
    save_json(project.root / "discovery/workflow-map.json", discovery.model_dump())
    save_json(project.root / "test-cases/test-matrix.json", [])
    html = Path(report(project, "html")).read_text(encoding="utf-8")
    assert "NOT_EXECUTED" in html
    assert "zero counts are not passing results" in html
    assert not (project.root / "reports/latest-run.json").exists()
    assert "junit.xml" not in html
    from autoqa.core import load_json

    payload = load_json(Path(report(project, "json")))
    assert payload["blocked_summary"] == [
        {"origin": "https://example.test", "method": "GET", "count": 2}
    ]
