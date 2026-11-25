"""Synthetic V0.7 traceability acceptance; no browser, API request or client source execution."""

import json
import tempfile
from pathlib import Path

from autoqa.api_service import plan_api
from autoqa.authorization import AuthorizationContext
from autoqa.core import TestCase, initialize
from autoqa.intelligent_planning_service import IntelligentPlanningService
from autoqa.planning import approve, case_signature, save_cases


def main():
    work = Path(".test-work")
    work.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="v07-planning-example-", dir=work)).resolve()
    project = initialize("synthetic-planning", output / "projects")
    auth = AuthorizationContext(project.root, frozenset({"plan", "review"}))
    common = dict(
        feature="Owned fixture",
        description="Synthetic declared fixture baseline",
        preconditions=["Authorized synthetic data only"],
        steps=["Review fixture expectation"],
        expected="Owned fixture baseline",
        evidence=[],
        url="http://127.0.0.1:9/",
    )
    ui = TestCase(id="TC-UI", title="Owned UI heading", kind="heading", **common)
    manual = TestCase(
        id="TC-MANUAL", title="Manual accessibility review", kind="manual", feasible=False, **common
    )
    save_cases(project, [ui, manual], authorization=auth)
    api_input = output / "api.json"
    api_input.write_text(
        json.dumps(
            [
                {
                    "id": "TC-API",
                    "title": "Owned API health",
                    "request": {"path": "/health"},
                    "expect": {"status": 200},
                    "environments": [
                        {"name": "local", "origin": "http://127.0.0.1:9", "allow_localhost": True}
                    ],
                    "environment": "local",
                }
            ]
        ),
        encoding="utf-8",
    )
    plan_api(project, api_input, auth)
    approve(project, ["TC-UI", "TC-API", "TC-MANUAL"], authorization=auth)
    current = {c.id: c for c in project.cases()}
    source = {
        "id": "SRC-OWNER",
        "reference": "Synthetic owner-approved fixture specification",
        "description": "No external target or unobserved business rule",
    }
    rows = []
    for identity, title, kind, expected, review in [
        ("REQ-UI", "Owned UI heading", "UI", "Owned fixture heading", "approved"),
        ("REQ-API", "Owned API health", "API", "Reviewed synthetic healthy status", "approved"),
        (
            "REQ-MISSING",
            "Uncovered owned workflow",
            "UI",
            "Explicit owner baseline to implement",
            "approved",
        ),
        ("REQ-MANUAL", "Accessibility review", "UI", "Human assessment required", "approved"),
        ("REQ-UNKNOWN", "Unspecified behavior", "GENERAL", None, "pending"),
    ]:
        rows.append(
            {
                "id": identity,
                "title": title,
                "kind": kind,
                "description": title,
                "source_id": source["id"],
                "review_status": review,
                "expected_behavior": expected,
            }
        )
    rows[1]["design_hints"] = [
        {
            "kind": "negative",
            "condition": "Review invalid response handling against the supplied contract",
        },
        {
            "kind": "boundary",
            "condition": "Ask the owner for applicable field boundaries before choosing values",
        },
    ]
    mappings = [
        {
            "requirement_id": r,
            "case_id": c,
            "case_signature": case_signature(current[c]),
            "review_status": "approved",
            "rationale": "Explicit fixture-owner mapping",
        }
        for r, c in [("REQ-UI", "TC-UI"), ("REQ-API", "TC-API"), ("REQ-MANUAL", "TC-MANUAL")]
    ]
    requirements = output / "requirements.json"
    requirements.write_text(
        json.dumps({"sources": [source], "requirements": rows, "mappings": mappings}),
        encoding="utf-8",
    )
    service = IntelligentPlanningService(project, auth)
    protected = {p: p.read_bytes() for p in project.root.rglob("*") if p.is_file()}
    snapshot = service.analyze(requirements)
    assert all(p.read_bytes() == data for p, data in protected.items())
    assert snapshot == service.analyze(requirements)
    assert snapshot.summary.confirmed_mapped_requirements == 2
    assert snapshot.summary.missing_requirements == 2
    assert snapshot.summary.unsupported_requirements == 1
    assert snapshot.summary.uncertain_requirements == 1
    assert snapshot.execution_coverage == "NOT_ASSESSED"
    assert len(snapshot.proposals) == 25
    service.import_requirements(requirements)
    reviewed = service.review(snapshot.id, [snapshot.proposals[0].id], "accepted")
    assert any(p.review_status == "accepted" for p in reviewed.proposals)
    assert all(p.read_bytes() == data for p, data in protected.items())
    (output / "plan.json").write_text(reviewed.model_dump_json(indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "plan_id": snapshot.id,
                "summary": snapshot.summary.model_dump(),
                "proposal_count": len(snapshot.proposals),
                "execution_coverage": snapshot.execution_coverage,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
