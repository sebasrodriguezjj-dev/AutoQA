"""Pure bounded requirements intelligence; proposals never authorize execution."""

import hashlib
import json

from pydantic import ValidationError

from autoqa.planning_contracts import (
    MAX_INPUT_BYTES,
    CoverageFinding,
    CoverageSummary,
    PlanningContext,
    PlanningSnapshot,
    ProposedScenario,
    RequirementsDocument,
    RiskAssessment,
)


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


def _constant(_value):
    raise ValueError("Non-finite JSON constant")


def parse_requirements(payload: bytes) -> RequirementsDocument:
    """Decode bounded JSON without executing/fetching provenance or echoing bad input."""
    if type(payload) is not bytes or not 1 <= len(payload) <= MAX_INPUT_BYTES:
        raise ValueError("Requirements input must be 1-256000 UTF-8 JSON bytes")
    try:
        value = json.loads(
            payload.decode("utf-8-sig"), object_pairs_hook=_object, parse_constant=_constant
        )
        return RequirementsDocument.model_validate(value)
    except ValueError, UnicodeError, RecursionError, OverflowError, MemoryError:
        raise ValueError("Invalid V0.7 requirements document") from None


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical(value):
    """All input collection orders are declarative sets, not ordered test steps."""
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return sorted((_canonical(item) for item in value), key=_encoded)
    return value


def _digest(value):
    return hashlib.sha256(_encoded(value).encode("utf-8")).hexdigest()


def _observed(requirement, context):
    known = set(requirement.workflow_ids) <= set(context.workflow_ids) and set(
        requirement.observed_evidence_ids
    ) <= set(context.evidence_ids)
    actual_observed = all(
        context.workflow_provenance.get(identity) == "OBSERVED"
        for identity in requirement.workflow_ids
    ) and all(
        context.evidence_provenance.get(identity) == "OBSERVED"
        for identity in requirement.observed_evidence_ids
    )
    declared = bool(requirement.workflow_ids or requirement.observed_evidence_ids)
    sufficient = known and actual_observed
    return sufficient, declared and sufficient


def _risk(requirement, *, confirmed, observed, feasible, uncertain):
    factors = {
        "business_criticality": requirement.business_criticality * 4,
        "user_impact": requirement.user_impact * 4,
        "priority": {"Critical": 15, "High": 12, "Medium": 8, "Low": 4}[requirement.priority],
        "coverage_gap": 0 if confirmed else 15,
        "observed_functionality": 10 if observed else 0,
        "execution_feasibility": 10 if feasible else 0,
        "uncertainty": 10 if uncertain else 0,
    }
    score = sum(factors.values())
    return RiskAssessment(
        score=score,
        level="High" if score >= 70 else "Medium" if score >= 40 else "Low",
        factors=factors,
        reasons=[
            "Business criticality and user impact are supplied owner assessments, not measurements.",
            "Priority follows the supplied requirement, with higher score for missing reviewed mappings.",
            "Observed references and existing mapped support affect priority, not proof of execution.",
            "Pending expectations, insufficient observations or stale mappings increase uncertainty.",
        ],
    )


def _finding(requirement, mappings, context):
    cases = {case.id: case for case in context.cases}
    confirmed, proposed, stale, unsupported = [], [], [], []
    known_observations, observed = _observed(requirement, context)
    uncertain = (
        requirement.review_status == "pending"
        or requirement.expected_behavior is None
        or not known_observations
    )
    active = [mapping for mapping in mappings if mapping.review_status != "rejected"]
    feasible = any(m.case_id in cases and cases[m.case_id].supported for m in active)
    if requirement.review_status == "rejected":
        return CoverageFinding(
            requirement_id=requirement.id,
            states=["EXCLUDED_REJECTED"],
            reasons=["The supplied requirement is rejected and excluded from proposed coverage."],
            risk=_risk(
                requirement,
                confirmed=False,
                observed=observed,
                feasible=feasible,
                uncertain=uncertain,
            ),
        )
    for mapping in active:
        case = cases.get(mapping.case_id)
        unsupported_case = case is not None and (not case.supported or case.kind == "manual")
        if unsupported_case:
            unsupported.append(case.id)
        if (
            case is None
            or (mapping.case_signature is not None and mapping.case_signature != case.signature)
            or case.review_status == "rejected"
            or (case.review_status == "approved" and not case.receipt_valid)
        ):
            stale.append(mapping.case_id)
            continue
        if unsupported_case:
            continue
        if (
            requirement.review_status == "approved"
            and requirement.expected_behavior is not None
            and known_observations
            and mapping.review_status == "approved"
            and mapping.case_signature == case.signature
            and case.review_status == "approved"
            and case.receipt_valid
        ):
            confirmed.append(case.id)
        else:
            proposed.append(case.id)
    states, reasons = [], []
    for ids, state, reason in [
        (
            confirmed,
            "CONFIRMED_REVIEWED_MAPPING",
            "Exact reviewed mappings match current approved case signatures and receipts; this is not executed coverage.",
        ),
        (
            proposed,
            "PROPOSED_MAPPING",
            "Mappings require requirement, expectation, relationship or case review before confirmation.",
        ),
        (
            stale,
            "STALE_MAPPING",
            "Referenced case is missing, changed, rejected or lacks a valid current approval receipt.",
        ),
        (
            unsupported,
            "UNSUPPORTED_AUTOMATION",
            "Mapped cases are manual or unsupported; no executable automation is inferred.",
        ),
    ]:
        if ids:
            states.append(state)
            reasons.append(reason)
    if not active:
        states.append("MISSING_MAPPING")
        reasons.append("No active explicit requirement-to-case mapping was supplied.")
    if uncertain:
        states.append("INSUFFICIENT_EVIDENCE")
        reasons.append(
            "Requirement is pending, expected behavior is unknown, or declared observed references are unavailable or lack OBSERVED provenance."
        )
    if any(case_id in cases and not cases[case_id].enabled for case_id in confirmed + proposed):
        reasons.append(
            "A mapped case is disabled in current membership; mapping is not execution eligibility or outcome."
        )
    return CoverageFinding(
        requirement_id=requirement.id,
        states=states,
        confirmed_case_ids=sorted(confirmed),
        proposed_case_ids=sorted(proposed),
        stale_case_ids=sorted(stale),
        unsupported_case_ids=sorted(unsupported),
        reasons=reasons,
        risk=_risk(
            requirement,
            confirmed=bool(confirmed),
            observed=observed,
            feasible=feasible,
            uncertain=uncertain or bool(stale),
        ),
    )


_DEFAULT_INTENTS = {
    "positive": "Review the declared successful path and its expected behavior against the supplied source.",
    "negative": "Review whether missing or invalid inputs apply; obtain explicit expected behavior before designing automation.",
    "boundary": "Identify applicable input or state boundaries with the owner; no limits or validation outcome are inferred.",
    "regression": "Review a stable expected baseline and select regression cases only after requirement and scenario approval.",
    "error_handling": "Review applicable error conditions and their expected handling; no status, message or recovery rule is inferred.",
}


def _proposals(requirement, risk):
    if requirement.review_status == "rejected":
        return []
    proposals = []
    for kind, default_intent in _DEFAULT_INTENTS.items():
        hints = [hint for hint in requirement.design_hints if hint.kind == kind]
        for hint in hints or [None]:
            hint_data = hint.model_dump() if hint else None
            identity = _digest(
                {
                    "requirement": _canonical(requirement.model_dump()),
                    "kind": kind,
                    "hint": hint_data,
                }
            )[:20]
            expected = (
                hint.expected_behavior
                if hint is not None
                else requirement.expected_behavior
                if kind == "positive"
                else None
            )
            assumptions = [
                "Applicability and source semantics require human review; no endpoint, selector or business rule is inferred.",
                "Planning acceptance does not approve a test case, suite membership or execution.",
            ]
            if expected is None:
                assumptions.append(
                    "Expected behavior is UNKNOWN; obtain an explicit reviewed expectation."
                )
            proposals.append(
                ProposedScenario(
                    id="PROP-" + identity,
                    requirement_id=requirement.id,
                    kind=kind,
                    title=f"{kind.replace('_', ' ').title()}: {requirement.title}",
                    intent=hint.condition if hint else default_intent,
                    expected_behavior=expected,
                    assumptions=assumptions,
                    evidence_ids=sorted(requirement.evidence_ids),
                    risk=risk,
                )
            )
    return proposals


def build_plan(document: RequirementsDocument, context: PlanningContext) -> PlanningSnapshot:
    """Return a deterministic reviewed-mapping plan, with no IO or approval writes."""
    if not isinstance(document, RequirementsDocument) or not isinstance(context, PlanningContext):
        raise ValueError("Planning requires validated V0.7 requirements and context")
    try:
        document = RequirementsDocument.model_validate(_canonical(document.model_dump()))
        context = PlanningContext.model_validate(_canonical(context.model_dump()))
    except ValidationError, ValueError, RecursionError:
        raise ValueError("Invalid V0.7 planning inputs") from None
    input_digest = _digest({"requirements": document.model_dump(), "context": context.model_dump()})
    grouped = {requirement.id: [] for requirement in document.requirements}
    for mapping in document.mappings:
        grouped[mapping.requirement_id].append(mapping)
    findings = [
        _finding(requirement, grouped[requirement.id], context)
        for requirement in document.requirements
    ]
    by_id = {finding.requirement_id: finding for finding in findings}
    proposals = [
        proposal
        for requirement in document.requirements
        for proposal in _proposals(requirement, by_id[requirement.id].risk)
    ]
    proposals.sort(
        key=lambda proposal: (
            -proposal.risk.score,
            proposal.requirement_id,
            proposal.kind,
            proposal.id,
        )
    )
    counts = {
        "confirmed_mapped_requirements": "CONFIRMED_REVIEWED_MAPPING",
        "proposed_mapped_requirements": "PROPOSED_MAPPING",
        "missing_requirements": "MISSING_MAPPING",
        "unsupported_requirements": "UNSUPPORTED_AUTOMATION",
        "uncertain_requirements": "INSUFFICIENT_EVIDENCE",
        "stale_requirements": "STALE_MAPPING",
        "excluded_rejected_requirements": "EXCLUDED_REJECTED",
    }
    summary = CoverageSummary(
        total_requirements=len(document.requirements),
        reviewed_requirements=sum(r.review_status == "approved" for r in document.requirements),
        **{
            name: sum(state in finding.states for finding in findings)
            for name, state in counts.items()
        },
    )
    limitations = [
        "Coverage describes explicit mappings within the supplied partial requirements inventory only, not complete application coverage.",
        "No test execution, collection, pass rate or executed coverage is assessed; observed controls do not establish requirements coverage.",
        "All proposals require manual review; accepting one changes neither existing scenario approvals nor suite membership or executable frameworks.",
        "Sources, expectations and risk inputs are supplied declarations under the trusted-local single-writer model, not authenticated evidence.",
    ]
    if context.suite_state == "STALE":
        limitations.append(
            "Suite membership is stale or invalid; no current reviewed pack/tag membership is asserted."
        )
    return PlanningSnapshot(
        id="PLAN-" + input_digest,
        project_id=context.project_id,
        input_digest=input_digest,
        requirements=document,
        context=context,
        findings=findings,
        proposals=proposals,
        summary=summary,
        limitations=limitations,
    )
