"""Privacy-safe historical invocation scope; never derive expected rows from outcomes."""

import re
from collections import Counter
from typing import Annotated, Literal, NamedTuple

from pydantic import Field, model_validator

from autoqa.v08_contracts import ID, Contract, Digest, digest

RowCount = Annotated[int, Field(strict=True, ge=1, le=1000)]
InvocationIDs = Annotated[list[ID], Field(min_length=1, max_length=1000)]
OUTCOMES = {"PASSED", "FAILED", "ERROR", "SKIPPED", "NOT_EXECUTED", "UNSUPPORTED"}
PRECEDENCE = ["ERROR", "FAILED", "NOT_EXECUTED", "UNSUPPORTED", "SKIPPED", "PASSED"]


class DiagnosticInvocationScope(Contract):
    schema_version: Literal["0.8"] = "0.8"
    run_id: ID
    project_id: ID
    selected_case_ids: list[ID] = Field(min_length=1, max_length=1000)
    parameter_counts: dict[ID, RowCount | None] = Field(max_length=1000)
    expected_invocation_ids: dict[ID, InvocationIDs] = Field(max_length=1000)
    case_signatures: dict[ID, Digest] = Field(max_length=1000)
    plan_digest: Digest

    @model_validator(mode="after")
    def exact_inventory(self):
        selected = set(self.selected_case_ids)
        if len(selected) != len(self.selected_case_ids):
            raise ValueError("Duplicate selected case")
        if set(self.parameter_counts) != selected or set(self.expected_invocation_ids) != selected:
            raise ValueError("Incomplete expected invocation inventory")
        if not self.case_signatures.keys() <= selected:
            raise ValueError("Signature outside selected scope")
        all_ids = []
        for case_id in selected:
            count = self.parameter_counts[case_id]
            expected = [case_id] if count is None else [f"{case_id}--row-{i}" for i in range(count)]
            observed = self.expected_invocation_ids[case_id]
            if len(set(observed)) != len(observed) or set(observed) != set(expected):
                raise ValueError("Expected identities disagree with parameter count")
            all_ids.extend(expected)
        if len(all_ids) > 1000 or len(set(all_ids)) != len(all_ids):
            raise ValueError("Conflicting or oversized expected invocation scope")
        return self


def normalized_plan(plan):
    """The same canonical projection is recorded by the independent runtime."""
    if not isinstance(plan, dict) or set(plan) != {
        "schema_version",
        "project_id",
        "suite_id",
        "pack_ids",
        "selection",
        "case_ids",
        "inventory_digest",
    }:
        raise ValueError("Invalid recorded execution plan")
    if plan["schema_version"] != "0.6" or not isinstance(plan["selection"], dict):
        raise ValueError("Unsupported recorded execution plan")
    selection = plan["selection"]
    if (
        set(selection) != {"schema_version", "mode", "values"}
        or selection["schema_version"] != "0.6"
    ):
        raise ValueError("Invalid recorded selection")
    if selection["mode"] not in {"all", "case", "pack", "suite", "tag"}:
        raise ValueError("Unknown recorded selection")
    for values in (plan["case_ids"], plan["pack_ids"], selection["values"]):
        if (
            not isinstance(values, list)
            or len(values) > 1000
            or any(not isinstance(v, str) for v in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError("Invalid recorded selection identities")
    if selection["mode"] == "all" and selection["values"]:
        raise ValueError("Full selection cannot contain identifiers")
    if selection["mode"] != "all" and not selection["values"]:
        raise ValueError("Selected selection requires identifiers")
    if (
        not isinstance(plan["project_id"], str)
        or not isinstance(plan["suite_id"], str)
        or not isinstance(plan["inventory_digest"], str)
        or not re.fullmatch(r"[a-f0-9]{64}", plan["inventory_digest"])
    ):
        raise ValueError("Invalid recorded plan identity")
    if selection["mode"] == "case" and set(selection["values"]) != set(plan["case_ids"]):
        raise ValueError("Case selection contradicts selected cases")
    if selection["mode"] == "suite" and selection["values"] != [plan["suite_id"]]:
        raise ValueError("Suite selection contradicts selected suite")
    if set(plan["pack_ids"]) != (
        set(selection["values"]) if selection["mode"] == "pack" else set()
    ):
        raise ValueError("Pack selection contradicts selected packs")
    return {
        **plan,
        "case_ids": sorted(plan["case_ids"]),
        "pack_ids": sorted(plan["pack_ids"]),
        "selection": {**selection, "values": sorted(selection["values"])},
    }


class ScopeAssessment(NamedTuple):
    known: bool
    issues: tuple[str, ...]
    fingerprint: str | None


def reconcile_invocations(raw, snapshots, project_id, run_id, steps):
    """Cross-check independent expected metadata, records, plans and summaries.

    The metadata is unsigned historical evidence, not an authenticated manifest.
    Missing older metadata remains uncertainty; it is never reconstructed from rows.
    """
    if "diagnostic_scope" not in raw:
        return ScopeAssessment(
            False,
            (
                "Historical expected invocation scope is unavailable; completeness cannot be established.",
            ),
            None,
        )
    scope = DiagnosticInvocationScope.model_validate(raw["diagnostic_scope"])
    issues = set()
    selected = set(scope.selected_case_ids)
    if scope.run_id != run_id or scope.project_id != project_id:
        issues.add("Historical scope identity differs from the recorded run or project.")
    if set(raw.get("selected_case_ids", [])) != selected:
        issues.add("Recorded selected case IDs differ from historical expected scope.")
    if set(snapshots) != set(scope.case_signatures) or any(
        snapshots.get(case_id, {}).get("signature") != signature
        for case_id, signature in scope.case_signatures.items()
    ):
        issues.add("Historical case signatures differ from the invocation scope.")
    for case_id, snapshot in snapshots.items():
        is_api = snapshot["kind"] in {"API", "api"}
        if case_id not in selected or is_api != (scope.parameter_counts.get(case_id) is not None):
            issues.add("Historical case kind differs from recorded parameterization.")
    expected = {
        identity: case for case, ids in scope.expected_invocation_ids.items() for identity in ids
    }
    records = raw.get("records", [])
    actual_ids = [r.get("id") for r in records if isinstance(r, dict)]
    if len(actual_ids) != len(records) or len(set(actual_ids)) != len(actual_ids):
        issues.add("Recorded invocation identities are malformed or duplicated.")
    if set(actual_ids) != set(expected):
        missing = len(set(expected) - set(actual_ids))
        unexpected = len(set(actual_ids) - set(expected))
        issues.add(
            f"Expected invocation reconciliation is incomplete: missing={missing}, unexpected={unexpected}."
        )
    if any(
        expected.get(r.get("id")) != r.get("case_id", r.get("id"))
        for r in records
        if isinstance(r, dict)
    ):
        issues.add("Invocation-to-case relationships differ from historical scope.")

    # Completeness is run-wide: a missing operation in one expected invocation
    # must qualify every passing observation in the same recorded run.
    by_invocation = {}
    for step in steps:
        identity = step["test_id"]
        if not isinstance(identity, str) or identity not in expected:
            issues.add("Operation evidence contains an unexpected invocation identity.")
            continue
        by_invocation.setdefault(identity, []).append(step)
    for record in records:
        if not isinstance(record, dict):
            continue
        identity = record.get("id")
        observed = by_invocation.get(identity, [])
        snapshot = snapshots.get(expected.get(identity))
        required = snapshot.get("operation_count") if snapshot else None
        status = record.get("status")
        ordered = all(
            type(step["sequence"]) is int
            and step["sequence"] == index
            and step["step_id"] == f"{identity}:step-{index}"
            and step["run_id"] == run_id
            and step["kind"] in {"navigation", "action", "assertion"}
            and step["status"] in OUTCOMES | {"INTERRUPTED"}
            for index, step in enumerate(observed, 1)
        )
        if not ordered or (required is not None and len(observed) > required):
            issues.add("Recorded invocation operations contradict historical identity or ordering.")
        if status == "PASSED" and (
            required is None
            or len(observed) != required
            or not observed
            or any(step["status"] != "PASSED" for step in observed)
        ):
            issues.add("A passing invocation lacks complete historical operation evidence.")
        if status in {"FAILED", "ERROR"} and not any(
            step["status"] in {"FAILED", "ERROR", "INTERRUPTED"} for step in observed
        ):
            issues.add("A failed invocation lacks a recorded failed operation.")

    try:
        outer = normalized_plan(raw["selection_snapshot"])
        execution = raw["execution_run"]
        inner = normalized_plan(execution["plan"])
        if (
            execution.get("schema_version") != "0.6"
            or outer != inner
            or digest(outer) != scope.plan_digest
            or set(outer["case_ids"]) != selected
            or outer["project_id"] != project_id
            or execution["run_id"] != run_id
            or raw.get("suite_id") != outer["suite_id"]
            or raw.get("selection_mode") != outer["selection"]["mode"]
            or set(raw.get("pack_ids", [])) != set(outer["pack_ids"])
            or raw.get("scope")
            != ("FULL_REGRESSION" if outer["selection"]["mode"] == "all" else "SELECTED_SCOPE")
        ):
            issues.add(
                "Recorded execution plan or selection metadata contradicts historical scope."
            )
    except ValueError, KeyError, TypeError:
        issues.add("Recorded execution plan or selection metadata is missing or malformed.")

    statuses = Counter(r.get("status") for r in records if isinstance(r, dict))
    counts = raw.get("counts")
    if (
        not isinstance(counts, dict)
        or any(k not in OUTCOMES or type(v) is not int or v < 0 for k, v in counts.items())
        or {k: v for k, v in counts.items() if v} != dict(statuses)
    ):
        issues.add("Recorded invocation counts contradict actual invocation records.")
    per_case = {}
    for case_id in selected:
        outcomes = {
            r.get("status")
            for r in records
            if isinstance(r, dict) and r.get("case_id", r.get("id")) == case_id
        }
        per_case[case_id] = next(
            (status for status in PRECEDENCE if status in outcomes), "NOT_EXECUTED"
        )
    execution = raw.get("execution_run")
    for values in (
        raw.get("case_results"),
        execution.get("results") if isinstance(execution, dict) else None,
    ):
        if (
            not isinstance(values, list)
            or len(values) > 1000
            or any(
                not isinstance(item, dict)
                or set(item) - {"schema_version", "case_id", "status", "evidence"}
                or item.get("schema_version", "0.6") != "0.6"
                for item in values
            )
        ):
            issues.add("Recorded case-level results are missing or malformed.")
            continue
        identities = [item.get("case_id") for item in values]
        if (
            len(set(identities)) != len(identities)
            or {item.get("case_id"): item.get("status") for item in values} != per_case
        ):
            issues.add("Recorded case-level outcomes contradict invocation scope or outcomes.")
    distribution = Counter(per_case.values())
    executed = sum(
        status in {"PASSED", "FAILED", "ERROR", "SKIPPED"} for status in per_case.values()
    )
    accounting = raw.get("accounting")
    expected_accounting = {
        "selected": len(selected),
        "executed": executed,
        **{status.lower(): distribution[status] for status in OUTCOMES},
    }
    if not isinstance(accounting, dict) or any(
        type(accounting.get(k)) is not int or accounting[k] != value
        for k, value in expected_accounting.items()
    ):
        issues.add("Recorded case accounting contradicts invocation outcomes or selection.")
    elif (
        type(accounting.get("eligible")) is not int
        or accounting["eligible"] < len(selected)
        or (raw.get("selection_mode") == "all" and accounting["eligible"] != len(selected))
        or type(accounting.get("ui")) is not int
        or type(accounting.get("api")) is not int
        or accounting["ui"] < 0
        or accounting["api"] < 0
        or accounting["ui"] + accounting["api"] != len(selected)
        or accounting["api"] < sum(s["kind"] in {"API", "api"} for s in snapshots.values())
        or accounting["ui"] < sum(s["kind"] not in {"API", "api"} for s in snapshots.values())
        or type(accounting.get("coverage_within_selection")) not in {int, float}
        or accounting["coverage_within_selection"] != executed / len(selected)
    ):
        issues.add("Recorded eligible/kind/selected coverage accounting is inconsistent.")
    all_passed = (
        bool(records) and statuses == {"PASSED": len(expected)} and set(actual_ids) == set(expected)
    )
    if raw.get("exit_code") == 0 and not all_passed:
        issues.add("Recorded successful exit contradicts incomplete or unsuccessful invocations.")
    if all_passed and (raw.get("exit_code") != 0 or raw.get("overall_status") != "PASSED"):
        issues.add("Recorded run outcome contradicts a complete passing invocation set.")
    if raw.get("overall_status") == "PASSED" and not (raw.get("exit_code") == 0 and all_passed):
        issues.add("Recorded overall success contradicts invocation outcomes or exit status.")
    if raw.get("exit_code") is None or raw.get("overall_status") not in {
        "PASSED",
        "INCOMPLETE_OR_FAILED",
    }:
        issues.add("Recorded run-level completion metadata is missing or invalid.")
    normalized = scope.model_dump(mode="json")
    normalized["selected_case_ids"] = sorted(selected)
    normalized["expected_invocation_ids"] = {
        case: (
            [case]
            if scope.parameter_counts[case] is None
            else [f"{case}--row-{i}" for i in range(scope.parameter_counts[case])]
        )
        for case in sorted(selected)
    }
    return ScopeAssessment(True, tuple(sorted(issues)), digest(normalized))
