"""Read-only legacy projections; original payloads remain available verbatim."""

from copy import deepcopy

from autoqa import domain


def check_version(payload: dict) -> None:
    version = payload.get("schema_version")
    if version not in (None, "0.1", "0.1.0", "0.2", "0.2.0"):
        raise ValueError(f"Unsupported legacy schema version: {version}")


def case_from_legacy(payload: dict, *, suite_id: str) -> domain.TestCase:
    check_version(payload)
    return domain.TestCase(
        id=payload["id"],
        suite_id=suite_id,
        title=payload["title"],
        expected=payload["expected"],
        feature=payload.get("feature", ""),
        test_type=payload.get("test_type", ""),
        priority=payload.get("priority", "Medium"),
        preconditions=payload.get("preconditions", []),
        feasible=payload.get("feasible"),
        evidence_ids=payload.get("evidence_refs", []),
        review_status=payload.get("review_status", "pending"),
        review_source="legacy",
        legacy=deepcopy(payload),
        steps=[
            domain.TestStep(
                id=f"{payload['id']}:step:{i}", case_id=payload["id"], ordinal=i, description=text
            )
            for i, text in enumerate(payload["steps"], 1)
        ],
    )


def suite_from_legacy(cases: list[dict], *, project_id: str, suite_id: str) -> domain.TestSuite:
    return domain.TestSuite(
        id=suite_id,
        project_id=project_id,
        derived=True,
        case_ids=[case["id"] for case in cases],
        generation_status=domain.GenerationStatus.UNKNOWN,
    )


def run_from_legacy(payload: dict, *, project_id: str, suite_id: str) -> domain.TestRun:
    check_version(payload)
    cases = {
        c["id"]: case_from_legacy(c, suite_id=suite_id) for c in payload.get("case_snapshot", [])
    }
    run_id = payload["run_id"]
    return domain.TestRun(
        id=run_id,
        project_id=project_id,
        suite_id=suite_id,
        snapshot=deepcopy(payload),
        legacy=deepcopy(payload),
        artifact_dir=payload["artifact_dir"],
        created_at=payload.get("created_at"),
        exit_code=payload.get("exit_code"),
        results=[
            domain.TestResult(
                id=f"{run_id}:result:{i}",
                run_id=run_id,
                case_id=r["id"],
                status=r["status"],
                duration=r.get("duration"),
                error=r.get("error"),
                legacy=deepcopy(r),
                steps=[
                    domain.StepResult(
                        id=f"{run_id}:{s.id}", run_id=run_id, case_id=r["id"], step_id=s.id
                    )
                    for s in cases[r["id"]].steps
                ]
                if r["id"] in cases
                else [],
            )
            for i, r in enumerate(payload["records"])
        ],
    )
