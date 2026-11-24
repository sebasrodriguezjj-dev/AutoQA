"""Additive suite review sidecar. Historical matrices and receipts remain unchanged."""

from autoqa.authorization import require_authorization
from autoqa.framework_runtime.management import TestCase, TestPack, TestSuite, digest
from autoqa.planning import case_signature, verify_approval_binding

REFERENCE = "test-cases/management.json"


def propose(project):
    cases = [
        TestCase(
            id=c.id,
            signature=case_signature(c),
            kind="API" if c.kind == "api" else "UI",
            priority=c.priority,
            review_status=c.review_status,
            supported=c.feasible,
        )
        for c in project.cases()
    ]
    # Only factual type and explicit critical priority support automatic proposals.
    packs = [TestPack(id=name, case_ids=[]) for name in ["SMOKE", "SANITY", "REGRESSION"]] + [
        TestPack(id="API", case_ids=[c.id for c in cases if c.kind == "API"]),
        TestPack(id="CRITICAL_PATH", case_ids=[c.id for c in cases if c.priority == "Critical"]),
    ]
    return TestSuite(project_id=project.root.name, cases=cases, packs=packs)


def approve_suite(project, suite, authorization):
    require_authorization(authorization, project.root, "review")
    current = {c.id: c for c in project.cases()}
    if suite.project_id != project.root.name or {c.id for c in suite.cases} != current.keys():
        raise ValueError("Suite must describe the current project's entire inventory")
    for entry in suite.cases:
        case = current[entry.id]
        if (
            entry.signature != case_signature(case)
            or entry.review_status != case.review_status
            or entry.kind != ("API" if case.kind == "api" else "UI")
        ):
            raise ValueError("Suite cannot change scenario identity, type or approval")
        if case.review_status == "approved":
            verify_approval_binding(project, case)
    suite = suite.model_copy(update={"review_status": "approved"})
    project.storage.append_event(
        {
            "event": "Suite membership approval",
            "snapshot": suite.model_dump(),
            "digest": digest(suite),
        }
    )
    project.storage.write_json(REFERENCE, suite.model_dump())
    project.storage.write_json("test-cases/management-receipt.json", {"digest": digest(suite)})
    project.audit("Approved suite membership snapshot " + digest(suite))
    return suite


def export_inventory(project, cases, unsupported):
    if project.storage.path(REFERENCE).exists():
        suite = TestSuite.model_validate(project.storage.read_json(REFERENCE))
        receipt = project.storage.read_json("test-cases/management-receipt.json")
        if suite.review_status != "approved" or receipt != {"digest": digest(suite)}:
            raise ValueError("Suite changed after membership approval")
        current = {c.id: c for c in project.cases()}
        if {c.id for c in suite.cases} != current.keys() or any(
            e.signature != case_signature(current[e.id])
            or e.review_status != current[e.id].review_status
            for e in suite.cases
        ):
            raise ValueError("Scenario inventory changed; review suite again")
    else:
        suite = propose(project).model_copy(update={"review_status": "approved", "packs": []})
    executable = {c.id for c in cases}
    suite = suite.model_copy(
        update={
            "cases": [c.model_copy(update={"supported": c.id in executable}) for c in suite.cases]
        }
    )
    return suite
