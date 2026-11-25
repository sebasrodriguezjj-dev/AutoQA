"""H03 synthetic reproductions: identities are not semantic review bindings."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_v07_integration import authorization, document, input_file, inventory, tree

from autoqa.intelligent_planning_service import DISCOVERY, IntelligentPlanningService
from autoqa.observation import observe_elements


def observation():
    return {
        "workflows": [
            {
                "id": "WF-001",
                "name": "Inspect amount",
                "page_url": "https://owned.test/a",
                "elements": ["Amount"],
                "element_ids": ["EL-AMOUNT"],
                "evidence": ["old.png"],
                "steps": ["Inspect amount"],
                "status": "OBSERVED",
            }
        ],
        "pages": [
            {
                "url": "https://owned.test/a",
                "title": "Amount",
                "headings": ["Amount"],
                "elements": [
                    {
                        "id": "EL-AMOUNT",
                        "kind": "input",
                        "name": "Amount",
                        "required": False,
                        "attributes": {"min": "1", "max": "10"},
                    }
                ],
                "screenshot": "old.png",
                "depth": 0,
            }
        ],
        "evidence_records": [
            {
                "id": "EV-PAGE-001",
                "category": "OBSERVED",
                "description": "Owned observation",
                "page_url": "https://owned.test/a",
                "artifact": "old.png",
            }
        ],
    }


@pytest.mark.parametrize("drift", ["workflow", "page", "required", "min", "max"])
def test_reused_identity_invalidates_accepted_snapshot(project, tmp_path, drift):
    inventory(project)
    value = observation()
    project.storage.write_json(DISCOVERY, value)
    service = IntelligentPlanningService(project, authorization(project, "plan", "review"))
    service.import_requirements(input_file(tmp_path, document()))
    first = service.analyze()
    accepted = service.review(first.id, [first.proposals[0].id], "accepted")
    assert accepted.review_state == "CURRENT"
    changed = deepcopy(value)
    if drift == "workflow":
        changed["workflows"][0]["name"] = "Inspect unrelated workflow"
        changed["workflows"][0]["page_url"] = "https://owned.test/b"
    elif drift == "page":
        changed["evidence_records"][0]["page_url"] = "https://owned.test/b"
    elif drift == "required":
        changed["pages"][0]["elements"][0]["required"] = True
    else:
        changed["pages"][0]["elements"][0]["attributes"][drift] = "5"
    project.storage.write_json(DISCOVERY, changed)
    before = tree(project)
    current = service.analyze()
    assert current.id != first.id
    assert current.review_state == "STALE"
    assert all(p.review_status == "pending" for p in current.proposals)
    with pytest.raises(ValueError, match="snapshot changed"):
        service.review(first.id, [first.proposals[0].id], "accepted")
    assert tree(project) == before


def test_conflicting_same_id_semantics_rejected(project, tmp_path):
    value = observation()
    value["evidence_records"].append(
        value["evidence_records"][0] | {"page_url": "https://owned.test/b"}
    )
    project.storage.write_json(DISCOVERY, value)
    source = input_file(tmp_path, document())
    before = tree(project)
    with pytest.raises(ValueError, match="Invalid current planning context"):
        IntelligentPlanningService(project).analyze(source)
    assert tree(project) == before


def test_legacy_element_id_reused_when_validation_changes():
    # Exercise the existing identity generator without a browser or network.
    item = {"kind": "input", "name": "Amount", "required": False, "attributes": {"min": "1"}}
    page = SimpleNamespace(
        evaluate=lambda _: [item], get_by_label=lambda *a, **k: SimpleNamespace(count=lambda: 0)
    )
    first = observe_elements(page, "https://owned.test/a", "first.png")[0]
    item["required"] = True
    item["attributes"]["min"] = "5"
    second = observe_elements(page, "https://owned.test/a", "second.png")[0]
    assert first.id == second.id
    assert first.required != second.required
    assert first.attributes != second.attributes


def ui_finding(plan):
    return next(f for f in plan.findings if f.requirement_id == "REQ-UI")


def bind(value, context):
    req = value["requirements"][0]
    req["workflow_ids"] = ["WF-001"]
    req["observed_evidence_ids"] = ["EV-PAGE-001", "EL-AMOUNT"]
    req["workflow_bindings"] = {
        key: context.workflow_fingerprints[key] for key in req["workflow_ids"]
    }
    req["evidence_bindings"] = {
        key: context.evidence_fingerprints[key] for key in req["observed_evidence_ids"]
    }


def test_review_disposition_cannot_rebind_drifted_observation(project, tmp_path):
    cases = inventory(project)
    value = observation()
    project.storage.write_json(DISCOVERY, value)
    service = IntelligentPlanningService(project, authorization(project, "plan", "review"))
    requirements = document(cases)
    bind(requirements, service._context())
    source = input_file(tmp_path, requirements)
    historical = tree(project)
    service.import_requirements(source)
    first = service.analyze()
    assert ui_finding(first).confirmed_case_ids == ["TC-UI"]
    service.review(first.id, [first.proposals[0].id], "accepted")
    value["pages"][0]["elements"][0]["required"] = True
    project.storage.write_json(DISCOVERY, value)
    stale = service.analyze()
    assert stale.review_state == "STALE"
    assert ui_finding(stale).confirmed_case_ids == []
    assert {"STALE_MAPPING", "INSUFFICIENT_EVIDENCE"} <= set(ui_finding(stale).states)
    assert ui_finding(stale).risk.factors["observed_functionality"] == 0
    accepted = service.review(stale.id, [stale.proposals[0].id], "accepted")
    assert accepted.review_state == "CURRENT"
    assert accepted.findings == stale.findings  # disposition does not review a relationship
    assert accepted.requirements == stale.requirements
    for name, contents in historical.items():
        if name != DISCOVERY:
            assert tree(project)[name] == contents  # existing receipts/cases/suite untouched
    # Only an explicit owner-supplied review of the new relationship restores mapping.
    bind(requirements, accepted.context)
    rebound = service.analyze(input_file(tmp_path, requirements))
    assert ui_finding(rebound).confirmed_case_ids == ["TC-UI"]
    assert rebound.review_state == "STALE"


def test_ids_and_observed_category_without_reviewed_bindings_are_insufficient(project, tmp_path):
    cases = inventory(project)
    project.storage.write_json(DISCOVERY, observation())
    value = document(cases)
    value["requirements"][0]["workflow_ids"] = ["WF-001"]
    plan = IntelligentPlanningService(project).analyze(input_file(tmp_path, value))
    assert ui_finding(plan).confirmed_case_ids == []
    assert "INSUFFICIENT_EVIDENCE" in ui_finding(plan).states
    assert ui_finding(plan).risk.factors["observed_functionality"] == 0


def test_equivalent_order_duplicates_and_volatile_metadata_do_not_drift(project, tmp_path):
    value = observation()
    page = value["pages"][0]
    page["headings"].append("Synthetic heading")
    page["elements"].append({"id": "EL-OTHER", "kind": "heading", "name": "Other"})
    value["workflows"][0]["element_ids"].append("EL-OTHER")
    project.storage.write_json(DISCOVERY, value)
    source = input_file(tmp_path, document())
    service = IntelligentPlanningService(project)
    first = service.analyze(source)
    value["created_at"] = "future timestamp"
    page["screenshot"] = "disposable-new.png"
    page["depth"] = 3
    page["readiness"] = {"elapsed": 500}
    page["dynamic_signals"] = ["transient"]
    page["elements"][0]["discovered_at"] = "later"
    page["elements"][0]["evidence"] = ["new.png"]
    page["elements"].reverse()
    page["headings"].reverse()
    value["workflows"][0]["element_ids"].reverse()
    value["workflows"][0]["evidence"] = ["different.png"]
    value["evidence_records"][0]["artifact"] = "new.png"
    value["evidence_records"][0]["timestamp"] = "later"
    value["evidence_records"].append(dict(value["evidence_records"][0]))
    project.storage.write_json(DISCOVERY, value)
    before = tree(project)
    assert service.analyze(source).model_dump() == first.model_dump()
    assert tree(project) == before


@pytest.mark.parametrize("collision", ["element", "page", "record-element"])
def test_conflicting_associations_fail_without_content_echo(project, tmp_path, collision):
    value = observation()
    if collision == "element":
        element = value["pages"][0]["elements"][0]
        value["pages"][0]["elements"].append(element | {"required": True})
    elif collision == "page":
        value["pages"].append(value["pages"][0] | {"title": "private-semantic-sentinel"})
    else:
        value["evidence_records"].append(
            {
                "id": "EL-AMOUNT",
                "category": "OBSERVED",
                "description": "private-semantic-sentinel",
                "page_url": "https://owned.test/b",
            }
        )
    project.storage.write_json(DISCOVERY, value)
    source = input_file(tmp_path, document())
    before = tree(project)
    with pytest.raises(ValueError) as caught:
        IntelligentPlanningService(project).analyze(source)
    assert str(caught.value) == "Invalid current planning context"
    assert tree(project) == before


def test_hash_only_context_and_meaningful_step_order(project, tmp_path):
    value = observation()
    value["workflows"][0]["steps"] = ["Private semantic sentinel", "Second step"]
    project.storage.write_json(DISCOVERY, value)
    source = input_file(tmp_path, document())
    service = IntelligentPlanningService(project)
    first = service.analyze(source)
    assert "Private semantic sentinel" not in first.model_dump_json()
    assert all(len(v) == 64 for v in first.context.workflow_fingerprints.values())
    value["workflows"][0]["steps"].reverse()
    project.storage.write_json(DISCOVERY, value)
    assert service.analyze(source).id != first.id


def test_existing_workflow_generator_reuses_id_across_pages():
    from autoqa.core import Discovery
    from autoqa.exploration import extract_workflows

    value = observation()
    first = extract_workflows(Discovery.model_validate(value))[0]
    value["pages"][0]["url"] = "https://owned.test/b"
    second = extract_workflows(Discovery.model_validate(value))[0]
    assert first.id == second.id == "WF-001"
    assert first.status == second.status == "OBSERVED"
    assert first.page_url != second.page_url


@pytest.mark.parametrize("field", ["workflow_bindings", "evidence_bindings"])
@pytest.mark.parametrize("digest", ["invalid", "a" * 63, "A" * 64])
def test_reviewed_bindings_require_known_ids_and_sha256(field, digest):
    from autoqa.planning_contracts import RequirementsDocument

    value = document()
    value["requirements"][0][field] = {"ABSENT": digest}
    with pytest.raises(ValueError):
        RequirementsDocument.model_validate(value)
