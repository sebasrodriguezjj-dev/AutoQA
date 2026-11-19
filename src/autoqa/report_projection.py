"""Pure report projection, reusable without Jinja or persistence."""

from collections import Counter
from typing import TypedDict

from autoqa.core import Discovery, TestCase
from autoqa.domain import ExecutionStatus


class StepEvidence(TypedDict):
    case_id: str
    ordinal: int
    status: ExecutionStatus


def historical_step_evidence(case_snapshot: list[dict]) -> list[StepEvidence]:
    """Legacy runners captured test outcomes, never individual step outcomes.

    Separate from the compatibility report payload: future consumers may request
    this availability projection without changing legacy JSON/HTML contracts.
    """
    return [
        {"case_id": case["id"], "ordinal": ordinal, "status": ExecutionStatus.NOT_RECORDED}
        for case in case_snapshot
        for ordinal, _ in enumerate(case.get("steps", []), 1)
    ]


class ReportData(TypedDict):
    project: dict
    run: dict
    counts: dict[str, int]
    workflow_count: int
    approved: int
    automated: int
    unautomated: int
    discovery_errors: list[str]
    findings: list[dict]
    pages_analyzed: int
    interactive_elements: int
    proposed: int
    pending: int
    rejected: int
    executed: int
    functional_validated: int
    potential_defects: int
    unverified: list[dict]
    workflow_results: dict[str, dict[str, int]]
    artifacts: list[str]
    discovery_screenshots: list[str]
    blocked_requests: list[dict[str, str]]
    blocked_summary: list[dict]


def project_report(
    config: dict,
    result: dict,
    cases: list[TestCase],
    discovery: Discovery,
    manifest: dict,
    findings: list[dict],
    artifacts: list[str],
) -> ReportData:
    payload: ReportData = {
        "project": config,
        "run": result,
        "counts": dict(Counter(r["status"] for r in result["records"])),
        "workflow_count": len(discovery.workflows),
        "approved": sum(c.review_status == "approved" for c in cases),
        "automated": len(manifest["cases"]),
        "unautomated": sum(c.id not in manifest["cases"] for c in cases),
        "discovery_errors": discovery.errors,
        "findings": findings,
        "pages_analyzed": len(discovery.pages),
        "interactive_elements": sum(
            sum(e.kind in {"a", "button", "input", "select", "textarea"} for e in p.elements)
            for p in discovery.pages
        ),
        "proposed": len(cases),
        "pending": sum(c.review_status == "pending" for c in cases),
        "rejected": sum(c.review_status == "rejected" for c in cases),
        "executed": sum(
            r["status"] in {"PASSED", "FAILED", "SKIPPED", "ERROR"} for r in result["records"]
        ),
        "functional_validated": sum(
            r["status"] == "PASSED"
            and any(c.id == r["id"] and c.kind == "functional" for c in cases)
            for r in result["records"]
        ),
        "potential_defects": sum(
            f.get("failure_class") == "APPLICATION DEFECT CANDIDATE" for f in findings
        ),
        "unverified": [
            c.model_dump() for c in cases if c.review_status != "approved" or not c.feasible
        ],
        "workflow_results": {},
        "artifacts": [],
        "discovery_screenshots": [p.screenshot for p in discovery.pages],
        "blocked_requests": discovery.blocked_requests,
        "blocked_summary": [
            {"origin": origin, "method": method, "count": count}
            for (origin, method), count in Counter(
                (r["origin"], r["method"]) for r in discovery.blocked_requests
            ).items()
        ],
    }
    payload["artifacts"] = artifacts
    if "case_snapshot" in result:
        payload["automated"] = len(result["case_snapshot"])
        payload["unautomated"] = sum(
            c.id not in {s["id"] for s in result["case_snapshot"]} for c in cases
        )
    for record in result["records"]:
        case = next((c for c in cases if c.id == record["id"]), None)
        workflow = case.feature if case else "Unknown"
        group = payload["workflow_results"].setdefault(workflow, {})
        group[record["status"]] = group.get(record["status"], 0) + 1
    return payload
