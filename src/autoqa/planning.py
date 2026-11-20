"""Deterministic scenario planning; persisted approvals bind exact scenario content."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from autoqa.authorization import AuthorizationContext, require_authorization
from autoqa.core import Project, TestCase, save_json
from autoqa.security import Scope


def case_signature(case: TestCase) -> str:
    excluded = {"review_status"}
    if case.kind != "functional":
        excluded.update({"test_data", "evidence_refs", "workflow_id", "contract"})
    data = case.model_dump(exclude=excluded)
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def save_cases(
    project: Project, cases: list[TestCase], *, authorization: AuthorizationContext | None = None
) -> None:
    """Persist reviewed cases only with explicit review authorization."""
    require_authorization(authorization, project.root, "review")
    _save_cases(project, cases)


def _approval_receipts(project: Project) -> dict:
    path = project.root / "test-cases/approval-receipts.json"
    if not path.exists():
        return {}
    value = project.storage.read_json("test-cases/approval-receipts.json")
    if not isinstance(value, dict):
        raise ValueError("Approval receipt store is invalid.")
    return value


def approval_receipt(project: Project, case: TestCase) -> dict | None:
    """Return the separately persisted approval receipt for a case, if present."""
    return _approval_receipts(project).get(case.id)


def verify_approval_binding(project: Project, case: TestCase) -> None:
    """Require an approval receipt bound to the current reviewed scenario."""
    receipt = approval_receipt(project, case)
    if receipt is None:
        raise ValueError(
            f"Legacy approved scenario {case.id} has no approval receipt; explicit reapproval is required."
        )
    if not isinstance(receipt, dict) or receipt.get("schema") != "autoqa.approval-receipt.v1":
        raise ValueError(f"Invalid approval receipt for {case.id}.")
    expected = case_signature(case)
    if (
        receipt.get("case_id") != case.id
        or receipt.get("status") != "approved"
        or receipt.get("scenario_signature") != expected
        or receipt.get("case_revision") != expected
        or not isinstance(receipt.get("approved_at"), str)
    ):
        raise ValueError(
            f"Approval binding changed for {case.id}; explicit reapproval is required."
        )


def _save_cases(project: Project, cases: list[TestCase]) -> None:
    project.storage.write_json("test-cases/test-matrix.json", [case.model_dump() for case in cases])
    lines = [
        "# Test matrix",
        "",
        "Expected results are observation-based regression baselines, not confirmed requirements.",
        "",
    ]
    for case in cases:
        lines += [
            f"## {case.id}: {case.title}",
            f"Status: {case.review_status}; priority: {case.priority}; automated: {case.feasible}",
            case.description,
            "",
            "Steps:",
        ]
        lines += [f"{i}. {step}" for i, step in enumerate(case.steps, 1)]
        lines += [f"Expected: {case.expected}", f"Evidence: {', '.join(case.evidence)}", ""]
        if case.test_data:
            lines += [f"Test data: {json.dumps(case.test_data, ensure_ascii=False)}", ""]
    project.storage.write_text("test-cases/test-matrix.md", "\n".join(lines))


def plan(
    project: Project,
    requirements: Path | None = None,
    *,
    authorization: AuthorizationContext | None = None,
) -> list[TestCase]:
    require_authorization(authorization, project.root, "plan")
    discovery = project.discovery()
    cases: list[TestCase] = []
    seen = set()
    previous = project.cases() if (project.root / "test-cases/test-matrix.json").exists() else []
    reviews = {
        case_signature(case): case.review_status
        for case in previous
        if case.review_status != "pending"
    }
    scope = (
        Scope(project.config.application_url, project.config)
        if project.config.application_url
        else None
    )
    for page in discovery.pages:
        common = dict(
            feature="Observed UI",
            description="Regression baseline from visible browser evidence; review before approval.",
            preconditions=[
                "Authorized application is running",
                "Recorded UI remains the intended baseline",
            ],
            evidence=[page.screenshot],
            url=page.url,
        )
        if page.headings:
            heading = page.headings[0]
            cases.append(
                TestCase(
                    id=f"TC-{len(cases) + 1:03}",
                    title=f"Display {heading}",
                    steps=[f"Open {page.url}", f"Inspect heading {heading}"],
                    expected=f"Heading {heading!r} is visible",
                    kind="heading",
                    target=heading,
                    **common,
                )
            )
        for element in page.elements:
            if element.kind != "a" or not element.name or not element.href or not scope:
                continue
            edge = (page.url, element.href, element.name)
            if edge in seen or not scope.allows(element.href):
                continue
            destination = next((p for p in discovery.pages if p.url == element.href), None)
            # Only generate links whose destination heading was actually observed.
            if destination and destination.headings:
                seen.add(edge)
                cases.append(
                    TestCase(
                        id=f"TC-{len(cases) + 1:03}",
                        title=f"Navigate via {element.name}",
                        steps=[f"Open {page.url}", f"Follow link {element.name}"],
                        expected=f"Destination heading {destination.headings[0]!r} is visible",
                        kind="link",
                        target=element.name,
                        destination=destination.url,
                        **common,
                    )
                )
        fields = [
            element.name
            for element in page.elements
            if element.kind in {"input", "select", "textarea"}
        ]
        if fields:
            cases.append(
                TestCase(
                    id=f"TC-{len(cases) + 1:03}",
                    title="Review form/search behavior",
                    steps=[
                        "Confirm business requirements",
                        "Define validation and search expectations",
                    ],
                    expected="Unknown; requires human requirements review",
                    feasible=False,
                    kind="manual",
                    test_type="Negative",
                    **common,
                )
            )
    if not discovery.pages:
        for workflow in discovery.workflows:
            cases.append(
                TestCase(
                    id=f"TC-{len(cases) + 1:03}",
                    feature="Source route review",
                    title=workflow.name,
                    description="Static source evidence only; no browser behavior verified.",
                    preconditions=[
                        "Running authorized test environment and confirmed requirements"
                    ],
                    steps=workflow.steps,
                    expected="Unknown; confirm route behavior with application owner",
                    test_type="Functional",
                    evidence=workflow.evidence,
                    feasible=False,
                    kind="manual",
                    url=workflow.page_url,
                )
            )
    from autoqa.core import EvidenceReference, load_json
    from autoqa.functional import BehaviorContract, functional_case

    contracts_path = project.root / "test-cases/behavior-contracts.json"
    raw_contracts = []
    if requirements:
        if requirements.stat().st_size > 256_000:
            raise ValueError("Behavior requirements file exceeds 256 KB.")
        raw_contracts = load_json(requirements)
    elif contracts_path.exists():
        raw_contracts = load_json(contracts_path)
    if not isinstance(raw_contracts, list) or len(raw_contracts) > 100:
        raise ValueError("Requirements must be an array of at most 100 behavior contracts.")
    contracts = [BehaviorContract.model_validate(c) for c in raw_contracts]
    if len({c.id for c in contracts}) != len(contracts):
        raise ValueError("Duplicate behavior contract IDs.")
    local = urlsplit(project.config.application_url or "").hostname in {
        "localhost",
        "127.0.0.1",
        "::1",
    }
    for contract in contracts:
        cases.append(
            functional_case(contract, discovery, local=local and project.config.allow_localhost)
        )
    for workflow in discovery.workflows:
        if workflow.kind in {"search", "filter", "sorting", "form"} and not any(
            c.page_url == workflow.page_url and c.workflow == workflow.kind for c in contracts
        ):
            for polarity in (
                ["Positive", "Negative"] if workflow.kind in {"search", "form"} else ["Positive"]
            ):
                cases.append(
                    TestCase(
                        id=f"TC-{len(cases) + 1:03}",
                        feature=workflow.kind.title(),
                        title=f"{polarity}: review {workflow.kind} outcome",
                        description="Inferred interaction; expected behavior and test data have not been verified.",
                        preconditions=workflow.preconditions,
                        steps=workflow.steps,
                        expected="UNKNOWN: supply a reviewed behavior contract grounded in the observed controls.",
                        test_type=polarity,
                        evidence=workflow.evidence,
                        evidence_refs=workflow.element_ids,
                        workflow_id=workflow.id,
                        feasible=False,
                        kind="manual",
                        url=workflow.page_url,
                    )
                )
    for case in cases:
        case.review_status = reviews.get(case_signature(case), "pending")
    if requirements:
        save_json(contracts_path, [c.model_dump() for c in contracts])
        for contract in contracts:
            reference = EvidenceReference(
                id="REQ-" + contract.id,
                category=contract.basis,
                description=contract.source,
                page_url=contract.page_url,
                artifact="test-cases/behavior-contracts.json",
            )
            discovery.evidence_records = [
                e for e in discovery.evidence_records if e.id != reference.id
            ]
            discovery.evidence_records.append(reference)
        save_json(project.root / "discovery/workflow-map.json", discovery.model_dump())
    _save_cases(project, cases)
    project.audit(f"Planned {len(cases)} scenarios (offline deterministic mode)")
    return cases


def reject(
    project: Project, ids: list[str], *, authorization: AuthorizationContext | None = None
) -> list[TestCase]:
    require_authorization(authorization, project.root, "review")
    cases = project.cases()
    if set(ids) - {c.id for c in cases}:
        raise ValueError("Unknown test IDs.")
    for case in cases:
        if case.id in ids:
            case.review_status = "rejected"
    _save_cases(project, cases)
    project.audit(f"Rejected scenarios: {', '.join(ids)}")
    return cases


def approve(
    project: Project, ids: list[str], *, authorization: AuthorizationContext | None = None
) -> list[TestCase]:
    require_authorization(authorization, project.root, "review")
    cases = project.cases()
    unknown = set(ids) - {case.id for case in cases}
    if unknown:
        raise ValueError(f"Unknown test IDs: {', '.join(sorted(unknown))}")
    for case in cases:
        if case.id in ids:
            case.review_status = "approved"
    _save_cases(project, cases)
    receipts = _approval_receipts(project)
    for case in cases:
        if case.id in ids:
            signature = case_signature(case)
            receipts[case.id] = {
                "schema": "autoqa.approval-receipt.v1",
                "case_id": case.id,
                "scenario_signature": signature,
                "case_revision": signature,
                "approved_at": datetime.now(UTC).isoformat(),
                "source": "manual-review",
                "status": "approved",
            }
    project.storage.write_json("test-cases/approval-receipts.json", receipts)
    project.audit(f"Approved scenarios: {', '.join(ids)}")
    return cases
