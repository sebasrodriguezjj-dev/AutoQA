"""Additive V0.7 planning DTOs; no legacy migration or executable test contracts."""

import json
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Label = Annotated[str, Field(max_length=2000)]
Identity = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")]
RequirementID = Annotated[str, Field(pattern=r"^REQ-[A-Za-z0-9_-]{1,60}$")]
CaseID = Annotated[str, Field(pattern=r"^TC-[A-Za-z0-9_-]{1,60}$")]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
ReviewStatus = Literal["pending", "approved", "rejected"]
ProposalDecision = Literal["pending", "accepted", "rejected"]
Polarity = Literal["positive", "negative", "boundary", "regression", "error_handling"]
CoverageState = Literal[
    "CONFIRMED_REVIEWED_MAPPING",
    "PROPOSED_MAPPING",
    "MISSING_MAPPING",
    "UNSUPPORTED_AUTOMATION",
    "INSUFFICIENT_EVIDENCE",
    "STALE_MAPPING",
    "EXCLUDED_REJECTED",
]
MAX_INPUT_BYTES = 256_000


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)

    @model_validator(mode="after")
    def safe_text(self):
        # Conventional material only; not universal secret/PII detection.
        def check(value):
            if isinstance(value, str):
                if any(ord(c) < 32 and c not in "\n\r\t" for c in value) or re.search(
                    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{35,}|AKIA[A-Z0-9]{16}",
                    value,
                ):
                    raise ValueError(
                        "Unsafe control characters or conventional credential material"
                    )
            elif isinstance(value, dict):
                for key, item in value.items():
                    check(key)
                    check(item)
            elif isinstance(value, list):
                for item in value:
                    check(item)

        check(self.model_dump())
        return self


def unique(values, label):
    if len(values) != len(set(values)):
        raise ValueError("Duplicate " + label)


class RequirementSource(Contract):
    id: Identity
    reference: Text
    description: Text


class PlanningEvidence(Contract):
    id: Identity
    source_id: Identity
    description: Text


class DesignHint(Contract):
    kind: Polarity
    condition: Text
    expected_behavior: Text | None = None


class Requirement(Contract):
    id: RequirementID
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    description: Text
    source_id: Identity
    review_status: ReviewStatus = "pending"
    kind: Literal["UI", "API", "GENERAL"] = "GENERAL"
    expected_behavior: Text | None = None
    priority: Literal["Critical", "High", "Medium", "Low"] = "Medium"
    business_criticality: int = Field(default=3, ge=1, le=5)
    user_impact: int = Field(default=3, ge=1, le=5)
    related_ids: list[RequirementID] = Field(default_factory=list, max_length=20)
    evidence_ids: list[Identity] = Field(default_factory=list, max_length=20)
    workflow_ids: list[Identity] = Field(default_factory=list, max_length=20)
    observed_evidence_ids: list[Identity] = Field(default_factory=list, max_length=20)
    workflow_bindings: dict[Identity, Digest] = Field(default_factory=dict, max_length=20)
    evidence_bindings: dict[Identity, Digest] = Field(default_factory=dict, max_length=20)
    design_hints: list[DesignHint] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def unique_hints(self):
        if not self.workflow_bindings.keys() <= set(
            self.workflow_ids
        ) or not self.evidence_bindings.keys() <= set(self.observed_evidence_ids):
            raise ValueError("Reviewed bindings must reference declared observations")
        unique(
            [json.dumps(h.model_dump(), sort_keys=True) for h in self.design_hints], "design hints"
        )
        return self


class RequirementMapping(Contract):
    requirement_id: RequirementID
    case_id: CaseID
    case_signature: Digest | None = None
    review_status: ReviewStatus = "pending"
    rationale: Text

    @model_validator(mode="after")
    def approved_signature(self):
        if self.review_status == "approved" and self.case_signature is None:
            raise ValueError("Reviewed mapping requires an explicit case signature")
        return self


class RequirementsDocument(Contract):
    schema_version: Literal["0.7"] = "0.7"
    inventory_scope: Literal["SUPPLIED_REQUIREMENTS_ONLY"] = "SUPPLIED_REQUIREMENTS_ONLY"
    sources: list[RequirementSource] = Field(min_length=1, max_length=100)
    evidence: list[PlanningEvidence] = Field(default_factory=list, max_length=1000)
    requirements: list[Requirement] = Field(min_length=1, max_length=100)
    mappings: list[RequirementMapping] = Field(default_factory=list, max_length=2000)

    @model_validator(mode="after")
    def relationships(self):
        source_ids = [x.id for x in self.sources]
        evidence_ids = [x.id for x in self.evidence]
        requirement_ids = [x.id for x in self.requirements]
        unique(source_ids, "source IDs")
        unique(evidence_ids, "evidence IDs")
        unique(requirement_ids, "requirement IDs")
        unique([(m.requirement_id, m.case_id) for m in self.mappings], "mapping pairs")
        for evidence in self.evidence:
            if evidence.source_id not in source_ids:
                raise ValueError("Unknown evidence source")
        for requirement in self.requirements:
            if requirement.source_id not in source_ids:
                raise ValueError("Unknown requirement source")
            if not set(requirement.evidence_ids) <= set(evidence_ids):
                raise ValueError("Unknown supplied evidence")
            if (
                not set(requirement.related_ids) <= set(requirement_ids)
                or requirement.id in requirement.related_ids
            ):
                raise ValueError("Unknown or self requirement relationship")
            for name in ["related_ids", "evidence_ids", "workflow_ids", "observed_evidence_ids"]:
                unique(getattr(requirement, name), name)
        if any(m.requirement_id not in requirement_ids for m in self.mappings):
            raise ValueError("Unknown mapping requirement")
        return self


class PlanningCase(Contract):
    id: CaseID
    signature: Digest
    review_status: ReviewStatus
    receipt_valid: bool
    supported: bool
    kind: Literal["heading", "link", "manual", "functional", "api"]
    title: Text
    enabled: bool = True
    pack_ids: list[Label] = Field(default_factory=list, max_length=100)
    tags: list[Label] = Field(default_factory=list, max_length=100)


class PlanningContext(Contract):
    project_id: Identity
    cases: list[PlanningCase] = Field(default_factory=list, max_length=1000)
    workflow_ids: list[Identity] = Field(default_factory=list, max_length=2000)
    evidence_ids: list[Identity] = Field(default_factory=list, max_length=5000)
    workflow_fingerprints: dict[Identity, Digest] = Field(default_factory=dict, max_length=2000)
    evidence_fingerprints: dict[Identity, Digest] = Field(default_factory=dict, max_length=5000)
    workflow_provenance: dict[
        Identity,
        Literal[
            "OBSERVED", "SOURCE", "INFERRED", "VERIFIED_REQUIREMENT", "REQUIRES_REVIEW", "UNKNOWN"
        ],
    ] = Field(default_factory=dict, max_length=2000)
    evidence_provenance: dict[
        Identity, Literal["OBSERVED", "SOURCE", "INFERRED", "VERIFIED_REQUIREMENT", "UNKNOWN"]
    ] = Field(default_factory=dict, max_length=5000)
    suite_id: Label | None = None
    suite_state: Literal["ABSENT", "CURRENT", "STALE"] = "ABSENT"
    suite_digest: Digest | None = None

    @model_validator(mode="after")
    def identities(self):
        if not self.workflow_fingerprints.keys() <= set(
            self.workflow_ids
        ) or not self.evidence_fingerprints.keys() <= set(self.evidence_ids):
            raise ValueError("Fingerprints must reference known inventory identities")
        unique([c.id for c in self.cases], "case IDs")
        unique(self.workflow_ids, "workflow IDs")
        unique(self.evidence_ids, "observed evidence IDs")
        if not self.workflow_provenance.keys() <= set(
            self.workflow_ids
        ) or not self.evidence_provenance.keys() <= set(self.evidence_ids):
            raise ValueError("Provenance must reference known inventory identities")
        return self


class RiskAssessment(Contract):
    score: int = Field(ge=0, le=100)
    level: Literal["Low", "Medium", "High"]
    factors: dict[str, int] = Field(min_length=7, max_length=7)
    reasons: list[Text] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def explained_score(self):
        limits = {
            "business_criticality": 20,
            "user_impact": 20,
            "priority": 15,
            "coverage_gap": 15,
            "observed_functionality": 10,
            "execution_feasibility": 10,
            "uncertainty": 10,
        }
        if (
            self.factors.keys() != limits.keys()
            or any(type(v) is not int or not 0 <= v <= limits[k] for k, v in self.factors.items())
            or sum(self.factors.values()) != self.score
        ):
            raise ValueError("Risk score must match the bounded named factors")
        if self.level != ("High" if self.score >= 70 else "Medium" if self.score >= 40 else "Low"):
            raise ValueError("Risk level differs from score")
        return self


class CoverageFinding(Contract):
    requirement_id: RequirementID
    states: list[CoverageState] = Field(min_length=1, max_length=7)
    confirmed_case_ids: list[CaseID] = Field(default_factory=list, max_length=1000)
    proposed_case_ids: list[CaseID] = Field(default_factory=list, max_length=1000)
    stale_case_ids: list[CaseID] = Field(default_factory=list, max_length=1000)
    unsupported_case_ids: list[CaseID] = Field(default_factory=list, max_length=1000)
    reasons: list[Text] = Field(min_length=1, max_length=20)
    risk: RiskAssessment


class ProposedScenario(Contract):
    id: Annotated[str, Field(pattern=r"^PROP-[a-f0-9]{20}$")]
    requirement_id: RequirementID
    kind: Polarity
    title: Text
    intent: Text
    expected_behavior: Text | None = None
    assumptions: list[Text] = Field(min_length=1, max_length=10)
    evidence_ids: list[Identity] = Field(default_factory=list, max_length=20)
    automation: Literal["MANUAL_REVIEW"] = "MANUAL_REVIEW"
    review_status: ProposalDecision = "pending"
    risk: RiskAssessment


class CoverageSummary(Contract):
    total_requirements: int = Field(ge=1, le=100)
    reviewed_requirements: int = Field(ge=0, le=100)
    confirmed_mapped_requirements: int = Field(ge=0, le=100)
    proposed_mapped_requirements: int = Field(ge=0, le=100)
    missing_requirements: int = Field(ge=0, le=100)
    unsupported_requirements: int = Field(ge=0, le=100)
    uncertain_requirements: int = Field(ge=0, le=100)
    stale_requirements: int = Field(ge=0, le=100)
    excluded_rejected_requirements: int = Field(ge=0, le=100)


class PlanningSnapshot(Contract):
    schema_version: Literal["0.7"] = "0.7"
    id: Annotated[str, Field(pattern=r"^PLAN-[a-f0-9]{64}$")]
    project_id: Identity
    input_digest: Digest
    coverage_scope: Literal["SUPPLIED_REQUIREMENTS_ONLY"] = "SUPPLIED_REQUIREMENTS_ONLY"
    execution_coverage: Literal["NOT_ASSESSED"] = "NOT_ASSESSED"
    requirements: RequirementsDocument
    context: PlanningContext
    findings: list[CoverageFinding] = Field(min_length=1, max_length=100)
    proposals: list[ProposedScenario] = Field(default_factory=list, max_length=1500)
    summary: CoverageSummary
    review_state: Literal["UNREVIEWED", "CURRENT", "STALE"] = "UNREVIEWED"
    limitations: list[Text] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def snapshot_links(self):
        ids = {r.id for r in self.requirements.requirements}
        if (
            self.id != "PLAN-" + self.input_digest
            or self.project_id != self.context.project_id
            or {f.requirement_id for f in self.findings} != ids
            or len(self.findings) != len(ids)
            or any(p.requirement_id not in ids for p in self.proposals)
        ):
            raise ValueError("Inconsistent planning snapshot relationships")
        unique([p.id for p in self.proposals], "proposal IDs")
        return self


class PlanningReview(Contract):
    schema_version: Literal["0.7"] = "0.7"
    plan_id: Annotated[str, Field(pattern=r"^PLAN-[a-f0-9]{64}$")]
    decisions: dict[str, Literal["accepted", "rejected"]] = Field(max_length=1500)

    @model_validator(mode="after")
    def proposal_keys(self):
        if any(not re.fullmatch(r"PROP-[a-f0-9]{20}", key) for key in self.decisions):
            raise ValueError("Invalid proposal review identity")
        return self
