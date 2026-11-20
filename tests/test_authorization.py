from pathlib import Path

import pytest

from autoqa.authorization import AuthorizationContext, require_authorization


def test_authorization_is_explicit_project_and_operation_bound(tmp_path: Path):
    context = AuthorizationContext(tmp_path, frozenset({"plan"}))
    require_authorization(context, tmp_path, "plan")
    with pytest.raises(ValueError, match="Explicit"):
        require_authorization(None, tmp_path, "plan")
    with pytest.raises(ValueError, match="Explicit"):
        require_authorization(context, tmp_path / "other", "plan")
    with pytest.raises(ValueError, match="Explicit"):
        require_authorization(context, tmp_path, "review")


def test_direct_operations_reject_missing_authorization(project):
    from autoqa import planning, testing
    from autoqa.planning_service import PlanningService

    operations = [
        lambda: planning.plan(project),
        lambda: planning.save_cases(project, []),
        lambda: planning.approve(project, ["TC-001"]),
        lambda: planning.reject(project, ["TC-001"]),
        lambda: testing.generate(project),
        lambda: testing.run(project),
        lambda: PlanningService(project, None).plan(),
    ]
    for operation in operations:
        with pytest.raises(ValueError, match="Explicit"):
            operation()


def test_service_review_persists_and_replanning_detects_drift(project):
    from autoqa.core import Discovery, PageEvidence
    from autoqa.planning import case_signature
    from autoqa.planning_service import PlanningService

    page = PageEvidence(
        url="http://127.0.0.1:8000/",
        title="Example",
        headings=["Before"],
        elements=[],
        screenshot="screenshots/example.png",
        depth=0,
    )
    project.storage.write_json("discovery/workflow-map.json", Discovery(pages=[page]).model_dump())
    project.config.application_url = page.url
    project.config.allow_localhost = True
    project.save_config()
    context = AuthorizationContext(project.root, frozenset({"plan", "review"}))
    service = PlanningService(project, context)
    original = service.plan()[0]
    signature = case_signature(original)
    service.approve([original.id])
    assert project.cases()[0].review_status == "approved"
    assert case_signature(project.cases()[0]) == signature
    assert service.plan()[0].review_status == "approved"
    service.reject([original.id])
    assert project.cases()[0].review_status == "rejected"
    with pytest.raises(ValueError, match="Unknown test"):
        service.approve(["TC-NOT-FOUND"])
    page.headings = ["After"]
    project.storage.write_json("discovery/workflow-map.json", Discovery(pages=[page]).model_dump())
    assert service.plan()[0].review_status == "pending"


def test_approval_receipt_binds_reviewed_signature_and_requires_reapproval(project):
    from autoqa.core import Discovery, PageEvidence
    from autoqa.planning import case_signature
    from autoqa.testing import generate

    page = PageEvidence(
        url="http://127.0.0.1:8000/",
        title="Example",
        headings=["Before"],
        elements=[],
        screenshot="screenshots/example.png",
        depth=0,
    )
    project.storage.write_json("discovery/workflow-map.json", Discovery(pages=[page]).model_dump())
    project.config.application_url = page.url
    project.config.allow_localhost = True
    project.save_config()
    context = AuthorizationContext(project.root, frozenset({"plan", "review", "generate"}))
    from autoqa.planning_service import PlanningService

    service = PlanningService(project, context)
    case = service.plan()[0]
    service.approve([case.id])
    receipt_path = project.root / "test-cases/approval-receipts.json"
    receipt = project.storage.read_json("test-cases/approval-receipts.json")[case.id]
    assert receipt["scenario_signature"] == case_signature(case)
    assert receipt["case_revision"] == case_signature(case)

    receipt_path.unlink()
    with pytest.raises(ValueError, match="no approval receipt"):
        generate(project, authorization=context)

    service.approve([case.id])
    receipt = project.storage.read_json("test-cases/approval-receipts.json")
    receipt[case.id]["scenario_signature"] = "wrong"
    project.storage.write_json("test-cases/approval-receipts.json", receipt)
    with pytest.raises(ValueError, match="Approval binding changed"):
        generate(project, authorization=context)

    service.approve([case.id])
    assert generate(project, authorization=context) == [case.id]
