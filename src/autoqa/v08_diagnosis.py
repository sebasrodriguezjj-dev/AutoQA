"""Deterministic, suppressed diagnosis of recorded scope and historical evidence."""

import re

from autoqa.core import TestCase
from autoqa.planning import case_signature
from autoqa.v08_contracts import (
    CauseHypothesis,
    DiagnosticFinding,
    DiagnosticReport,
    EvidenceReference,
    digest,
)
from autoqa.v08_io import read_json

STATUSES = {"PASSED", "FAILED", "ERROR", "NOT_EXECUTED", "SKIPPED", "UNSUPPORTED", "INTERRUPTED"}
IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$")


def _identity(value):
    if not isinstance(value, str) or IDENTITY.fullmatch(value) is None:
        raise ValueError("Invalid recorded identity")
    return value


def _snapshots(raw):
    result = {}
    values = raw.get("diagnostic_snapshot", raw.get("case_snapshot", []))
    if not isinstance(values, list) or len(values) > 1000:
        raise ValueError("Invalid historical snapshot")
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("Invalid historical snapshot")
        identity = _identity(value.get("id"))
        if identity in result:
            raise ValueError("Duplicate historical case identity")
        if "diagnostic_snapshot" in raw:
            if set(value) - {"id", "kind", "signature", "operation_count", "review_status"}:
                raise ValueError("Unexpected diagnostic snapshot field")
            signature = value.get("signature")
            count = value.get("operation_count")
            if not isinstance(signature, str) or not re.fullmatch(r"[a-f0-9]{64}", signature):
                raise ValueError("Missing historical signature")
            if count is not None and (type(count) is not int or not 1 <= count <= 100):
                raise ValueError("Invalid historical operation count")
            if value.get("kind") not in {
                "UI",
                "API",
                "heading",
                "link",
                "functional",
                "api",
                "manual",
            } or value.get("review_status") not in {"approved", "pending", "rejected"}:
                raise ValueError("Invalid historical snapshot kind or review state")
            result[identity] = {
                "id": identity,
                "kind": value.get("kind"),
                "signature": signature,
                "operation_count": count,
                "review_status": value.get("review_status"),
            }
        else:
            case = TestCase.model_validate(value)
            result[identity] = {
                "id": identity,
                "kind": case.kind,
                "signature": case_signature(case),
                "operation_count": None,
                "review_status": case.review_status,
            }
    return result


def _step_projection(step):
    if not isinstance(step, dict):
        raise ValueError("Invalid operation record")
    return {
        key: step.get(key) for key in ("run_id", "test_id", "step_id", "sequence", "kind", "status")
    }


def _symptom(error, steps, status):
    """Messages are hints only and never enter output or authorize product claims."""
    text = error.lower()
    failed = [step for step in steps if step["status"] in {"FAILED", "ERROR", "INTERRUPTED"}]
    failed_kind = failed[0].get("kind", "") if failed else ""
    if status in {"NOT_EXECUTED", "INTERRUPTED", "SKIPPED", "UNSUPPORTED"}:
        return "INCOMPLETE_EXECUTION", "Recorded invocation did not complete approved execution."
    if "strict mode violation" in text or "multiple elements" in text:
        return "LOCATOR_AMBIGUITY", "Recorded locator symptom indicates ambiguous selection."
    if "waiting for locator" in text or "locator not found" in text:
        return "LOCATOR_MISSING", "Recorded locator symptom indicates a missing match."
    if any(word in text for word in ("timeout", "timed out")):
        return "TIMEOUT_SYMPTOM", "Recorded operation has a timeout symptom; its cause is unknown."
    if any(
        word in text
        for word in ("authentication", "authorization", "credential", "unauthorized", "forbidden")
    ):
        return (
            "AUTH_FAILURE",
            "Recorded failure mentions authentication or authorization; credential values are withheld.",
        )
    if any(word in text for word in ("fixture", "test data", "missing value", "dataset")):
        return "TEST_DATA_FAILURE", "Recorded failure suggests a data or fixture verification step."
    if any(
        word in text
        for word in (
            "modulenotfound",
            "importerror",
            "connection refused",
            "dns",
            "executable doesn't exist",
            "browser executable",
        )
    ):
        return (
            "ENVIRONMENT_FAILURE",
            "Recorded failure suggests an environment or dependency verification step.",
        )
    if failed_kind == "assertion" or "assert" in text:
        return (
            "ASSERTION_MISMATCH",
            "An assertion mismatch was recorded; application versus automation cause is not established.",
        )
    if failed_kind in {"action", "navigation"}:
        return (
            "AUTOMATION_DEFECT_CANDIDATE",
            "A recorded navigation or action failed; inspect automation and environment before changing behavior.",
        )
    return (
        "INSUFFICIENT_EVIDENCE",
        "Recorded failure has insufficient structured evidence for a narrower symptom.",
    )


class DiagnosisService:
    def __init__(self, project):
        self.project = project

    def analyze(self, run_path):
        try:
            return self._analyze(read_json(run_path))
        except ValueError, TypeError, KeyError, OSError, RecursionError, OverflowError:
            raise ValueError("Invalid bounded recorded-run input") from None

    def _analyze(self, raw):
        if not isinstance(raw, dict):
            raise ValueError("Invalid recorded run")
        if "schema_version" in raw and raw["schema_version"] not in {"0.3", "0.5", "0.6"}:
            raise ValueError("Unsupported recorded run schema")
        if "exit_code" in raw and (
            type(raw["exit_code"]) is not int or not 0 <= raw["exit_code"] <= 255
        ):
            raise ValueError("Invalid recorded exit code")
        project_id = self.project.root.name
        if "project_id" in raw and raw["project_id"] != project_id:
            raise ValueError("Wrong recorded project")
        run_id = _identity(raw.get("run_id"))
        snapshots = _snapshots(raw)
        records, steps = raw.get("records", []), raw.get("steps", raw.get("step_results", []))
        if (
            not isinstance(records, list)
            or len(records) > 1000
            or not isinstance(steps, list)
            or len(steps) > 10000
        ):
            raise ValueError("Recorded evidence exceeds bounds")
        steps = [_step_projection(step) for step in steps]
        legacy = "step_results" in raw and "steps" not in raw
        if legacy:
            for step in steps:
                if step["run_id"] is None:
                    step["run_id"] = run_id
                if step["kind"] is None:
                    step["kind"] = "scenario"
        projected, seen = [], set()
        selected = raw.get("selected_case_ids", list(snapshots))
        if (
            not isinstance(selected, list)
            or len(selected) > 1000
            or len(set(selected)) != len(selected)
        ):
            raise ValueError("Invalid recorded selected scope")
        selected = {_identity(identity) for identity in selected}
        explicit_scope = "selected_case_ids" in raw or bool(snapshots)
        recorded_cases = set()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Invalid invocation record")
            identity = _identity(record.get("id"))
            case_id = _identity(record.get("case_id", identity))
            if (
                identity != case_id
                and re.fullmatch(re.escape(case_id) + r"--row-\d+", identity) is None
            ):
                raise ValueError("Conflicting case and invocation identity")
            recorded_cases.add(case_id)
            status = record.get("status")
            if identity in seen or status not in STATUSES:
                raise ValueError("Conflicting invocation record")
            seen.add(identity)
            error = record.get("error", "")
            if not isinstance(error, str) or len(error) > 20000:
                raise ValueError("Invalid recorded error")
            invocation_steps = [step for step in steps if step["test_id"] == identity]
            snapshot = snapshots.get(case_id)
            foreign = explicit_scope and case_id not in selected
            integrity = foreign or any(step["run_id"] != run_id for step in invocation_steps)
            sequences = [step["sequence"] for step in invocation_steps]
            integrity |= sequences != list(range(1, len(invocation_steps) + 1))
            integrity |= any(type(sequence) is not int for sequence in sequences)
            integrity |= any(step["status"] not in STATUSES for step in invocation_steps)
            step_ids = [step["step_id"] for step in invocation_steps]
            integrity |= len(set(step_ids)) != len(step_ids)
            integrity |= any(
                step["step_id"]
                not in {
                    f"{identity}:step-{index}",
                    f"{record.get('name', identity)}:step-{index}",
                }
                or step["kind"] not in {"navigation", "action", "assertion", "scenario"}
                for index, step in enumerate(invocation_steps, 1)
            )
            complete = bool(invocation_steps) and not integrity
            if snapshot and snapshot["operation_count"] is not None:
                integrity |= len(invocation_steps) > snapshot["operation_count"]
                if status == "PASSED":
                    complete &= len(invocation_steps) == snapshot["operation_count"]
            if status == "PASSED":
                integrity |= not complete or any(
                    step["status"] != "PASSED" for step in invocation_steps
                )
            if integrity:
                category, fact = (
                    "EVIDENCE_INTEGRITY_FAILURE",
                    "Recorded scope, identity, operation ordering or passing evidence is inconsistent.",
                )
            elif not invocation_steps or (
                status == "PASSED" and (snapshot is None or snapshot["review_status"] != "approved")
            ):
                category, fact = (
                    "INSUFFICIENT_EVIDENCE",
                    "Invocation lacks sufficient historical snapshot or operation evidence.",
                )
            elif status == "PASSED":
                category, fact = (
                    "HEALTHY_RECORDED_EXECUTION",
                    "Selected invocation and available operation records report a completed pass.",
                )
            else:
                category, fact = _symptom(error, invocation_steps, status)
            missing = []
            if snapshot is None:
                missing.append(
                    "Historical approved case snapshot is unavailable; latest project cases were not substituted."
                )
            elif snapshot["review_status"] != "approved":
                missing.append("Historical case is not recorded as approved.")
            if not complete:
                missing.append("A complete consistent ordered operation sequence is unavailable.")
            next_check = "Review the original selected run and approved snapshot locally; verify the symptom independently before repair or defect attribution."
            semantic = {
                "run_id": run_id,
                "case_id": case_id,
                "invocation_id": identity,
                "status": status,
                "snapshot": snapshot,
                "steps": invocation_steps,
                "category": category,
            }
            evidence = EvidenceReference(
                id="EV-" + digest(semantic)[:32],
                source="RECORDED_RUN",
                fingerprint=digest(semantic),
                suppressed=True,
                description="Run-bound structured identity and operation summary; raw errors and capture references are suppressed.",
            )
            hypotheses = (
                []
                if category == "HEALTHY_RECORDED_EXECUTION"
                else [
                    CauseHypothesis(
                        category=category,
                        rationale="The category describes a recorded symptom, not a confirmed root cause.",
                        confidence="UNKNOWN" if missing or integrity else "POSSIBLE",
                        next_check=next_check,
                    )
                ]
            )
            if category == "ASSERTION_MISMATCH" and not missing:
                hypotheses.extend(
                    [
                        CauseHypothesis(
                            category="APPLICATION_DEFECT_CANDIDATE",
                            rationale="Recorded behavior may differ from the reviewed expectation; independently reproduce before confirming an application defect.",
                            next_check=next_check,
                        ),
                        CauseHypothesis(
                            category="AUTOMATION_DEFECT_CANDIDATE",
                            rationale="The oracle, locator, fixture or environment may also explain a mismatch; do not repair by changing assertions to obtain a pass.",
                            next_check=next_check,
                        ),
                    ]
                )
            facts = [
                fact,
                "Raw failure content, expected-value text and sensitive artifact references are withheld.",
            ]
            if snapshot:
                facts.append("Historical case signature: " + snapshot["signature"])
            projected.append(
                DiagnosticFinding(
                    id="DIA-" + digest(semantic),
                    case_id=case_id,
                    invocation_id=identity,
                    category=category,
                    facts=facts,
                    evidence=[evidence],
                    hypotheses=hypotheses,
                    missing_evidence=missing,
                    next_check=next_check,
                    maintenance_appropriate=category in {"LOCATOR_MISSING", "LOCATOR_AMBIGUITY"}
                    and not missing,
                )
            )
        orphan = any(step["test_id"] not in seen for step in steps)
        if (
            not records
            or orphan
            or selected - recorded_cases
            or raw.get("reconciliation_errors")
            or raw.get("status") == "INCOMPLETE"
        ):
            category = (
                "COLLECTION_FAILURE"
                if raw.get("status") == "INCOMPLETE" or not records
                else "EVIDENCE_INTEGRITY_FAILURE"
            )
            projected.append(
                DiagnosticFinding(
                    id="DIA-" + digest([run_id, category, "scope"]),
                    category=category,
                    facts=[
                        "Collection, recorded invocation scope or evidence reconciliation is incomplete."
                    ],
                    missing_evidence=[
                        "Complete current-run invocation and operation evidence is required."
                    ],
                    next_check="Inspect collection and scope reconciliation before attributing any application defect.",
                )
            )
        projected.sort(
            key=lambda finding: (finding.case_id or "", finding.invocation_id or "", finding.id)
        )
        run_digest = digest(
            ["autoqa-diagnosis-input-v1", run_id, [f.model_dump() for f in projected]]
        )
        return DiagnosticReport(
            id="RUN-" + run_digest,
            project_id=project_id,
            run_id=run_id,
            run_digest=run_digest,
            findings=projected,
            limitations=[
                "Imported records are local claims, not authenticated proof of execution or confirmed root cause.",
                "Only historical recorded scope is considered; latest scenario state is never used to reinterpret old failures.",
                "Suppressed evidence remains suppressed; no universal secret or PII redaction is claimed.",
            ],
        )
