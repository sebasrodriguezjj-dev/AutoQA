"""Additive bounded V0.8 maintenance/diagnosis contracts; no legacy migration."""

import hashlib
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints, model_validator

from autoqa.domain import ArtifactReference
from autoqa.planning_contracts import Contract as SafeTextContract

Text = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
ID = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$")]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
Alias = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$", max_length=100)
]


def canonical(value):
    """Dictionary order is irrelevant; services explicitly sort unordered collections."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    )


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class Contract(SafeTextContract):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)


class EvidenceReference(Contract):
    id: ID
    source: Literal["RECORDED_RUN", "STATIC_SOURCE", "OBSERVED", "SUPPLIED"]
    reference: ArtifactReference | None = None
    fingerprint: Digest
    suppressed: bool = True
    description: Text


class CauseHypothesis(Contract):
    category: Text
    rationale: Text
    confidence: Literal["POSSIBLE", "UNKNOWN"] = "POSSIBLE"
    next_check: Text


DiagnosticCategory = Literal[
    "APPLICATION_DEFECT_CANDIDATE",
    "AUTOMATION_DEFECT_CANDIDATE",
    "LOCATOR_MISSING",
    "LOCATOR_AMBIGUITY",
    "TIMEOUT_SYMPTOM",
    "ENVIRONMENT_FAILURE",
    "AUTH_FAILURE",
    "TEST_DATA_FAILURE",
    "ASSERTION_MISMATCH",
    "COLLECTION_FAILURE",
    "INCOMPLETE_EXECUTION",
    "EVIDENCE_INTEGRITY_FAILURE",
    "INSUFFICIENT_EVIDENCE",
    "HEALTHY_RECORDED_EXECUTION",
]


class DiagnosticFinding(Contract):
    id: ID
    case_id: ID | None = None
    invocation_id: ID | None = None
    category: DiagnosticCategory
    facts: list[Text] = Field(min_length=1, max_length=20)
    evidence: list[EvidenceReference] = Field(default_factory=list, max_length=20)
    hypotheses: list[CauseHypothesis] = Field(default_factory=list, max_length=10)
    missing_evidence: list[Text] = Field(default_factory=list, max_length=20)
    next_check: Text
    maintenance_appropriate: bool = False
    root_cause_confirmed: Literal[False] = False


class DiagnosticReport(Contract):
    schema_version: Literal["0.8"] = "0.8"
    id: ID
    project_id: ID
    run_id: ID
    run_digest: Digest
    findings: list[DiagnosticFinding] = Field(max_length=1000)
    limitations: list[Text] = Field(default_factory=list, max_length=20)


class SourceFile(Contract):
    path: ArtifactReference
    fingerprint: Digest
    size: int = Field(ge=0, le=1_000_000)


class AutomationRevision(Contract):
    root_binding: Digest
    digest: Digest
    files: list[SourceFile] = Field(max_length=1000)

    @model_validator(mode="after")
    def identities(self):
        if len({f.path.casefold() for f in self.files}) != len(self.files):
            raise ValueError("Conflicting source paths")
        return self


class LocatorSpec(Contract):
    strategy: Literal["role", "label", "placeholder", "test_id"]
    value: Text
    name: str = Field(default="", max_length=200)
    count: Literal[1] = 1


class MaintenanceChange(Contract):
    kind: Literal["locator_replacement", "test_data_reference"]
    element_id: ID | None = None
    locator: LocatorSpec | None = None
    data_alias: Alias | None = None
    description: Text


class MaintenanceProposal(Contract):
    schema_version: Literal["0.8"] = "0.8"
    id: ID
    project_id: ID
    case_id: ID
    case_signature: Digest
    source_revision: AutomationRevision
    manual_revision: AutomationRevision | None = None
    evidence_digest: Digest
    data_digest: Digest | None = None
    original_behavior: Text
    change: MaintenanceChange
    rationale: Text
    risk: Literal["Low", "Medium", "High"] = "Medium"
    limitations: list[Text] = Field(default_factory=list, max_length=20)
    required_validation: list[Text] = Field(min_length=1, max_length=20)
    review_status: Literal["pending"] = "pending"


class MaintenanceDecision(Contract):
    schema_version: Literal["0.8"] = "0.8"
    project_id: ID
    proposal_id: ID
    proposal_digest: Digest
    decision: Literal["accepted", "rejected"]


class ReconciliationFinding(Contract):
    path: ArtifactReference
    state: Literal[
        "UNCHANGED_MANAGED",
        "MODIFIED_MANAGED",
        "MANUAL_CANDIDATE",
        "MOVED_CANDIDATE",
        "REMOVED",
        "ASSERTION_CHANGED",
        "PAGE_OBJECT_CHANGED",
        "DATA_REFERENCE_CHANGED",
        "UNSUPPORTED",
        "INTEGRITY_VIOLATION",
    ]
    case_ids: list[ID] = Field(default_factory=list, max_length=100)
    rationale: Text
    supported: bool = False


class ReconciliationReport(Contract):
    schema_version: Literal["0.8"] = "0.8"
    id: ID
    project_id: ID
    baseline: AutomationRevision
    current: AutomationRevision
    findings: list[ReconciliationFinding] = Field(max_length=1000)
    limitations: list[Text] = Field(default_factory=list, max_length=20)


class ApplicationObject(Contract):
    id: ID
    kind: Literal["route", "control", "component", "api_contract", "validation", "workflow"]
    source_location: ArtifactReference
    semantics: dict[str, Text] = Field(max_length=30)
    provenance: Literal["SOURCE", "OBSERVED", "UNKNOWN"] = "SOURCE"
    case_ids: list[ID] = Field(default_factory=list, max_length=100)
    requirement_ids: list[ID] = Field(default_factory=list, max_length=100)
    page_objects: list[ArtifactReference] = Field(default_factory=list, max_length=100)


class ApplicationInventory(Contract):
    schema_version: Literal["0.8"] = "0.8"
    project_id: ID
    objects: list[ApplicationObject] = Field(max_length=1000)

    @model_validator(mode="after")
    def identities(self):
        if len({o.id for o in self.objects}) != len(self.objects):
            raise ValueError("Conflicting application identities")
        return self


class ImpactFinding(Contract):
    object_id: ID
    kind: Text
    change: Literal["ADDED", "REMOVED", "CHANGED"]
    source_locations: list[ArtifactReference] = Field(max_length=2)
    potential_case_ids: list[ID] = Field(default_factory=list, max_length=100)
    requirement_ids: list[ID] = Field(default_factory=list, max_length=100)
    page_objects: list[ArtifactReference] = Field(default_factory=list, max_length=100)
    rationale: Text
    verified_runtime_impact: Literal[False] = False


class ImpactReport(Contract):
    schema_version: Literal["0.8"] = "0.8"
    id: ID
    project_id: ID
    before_digest: Digest
    after_digest: Digest
    findings: list[ImpactFinding] = Field(max_length=2000)
    unaffected_case_ids: list[ID] = Field(default_factory=list, max_length=1000)
    unknown_impact: list[Text] = Field(default_factory=list, max_length=20)


class TestDataDefinition(Contract):
    alias: Alias
    kind: Literal["value", "json", "csv", "file", "credential"]
    environments: list[ID] = Field(min_length=1, max_length=20)
    sensitivity: Literal["SYNTHETIC", "SECRET_REFERENCE"]
    values: list[dict[str, JsonValue]] = Field(default_factory=list, max_length=100)
    reference: str | None = Field(default=None, max_length=500)
    fingerprint: Digest | None = None


class TestDataInventory(Contract):
    schema_version: Literal["0.8"] = "0.8"
    project_id: ID
    definitions: list[TestDataDefinition] = Field(max_length=100)

    @model_validator(mode="after")
    def identities(self):
        if len({d.alias for d in self.definitions}) != len(self.definitions):
            raise ValueError("Duplicate data alias")
        return self


class ValidationResult(Contract):
    schema_version: Literal["0.8"] = "0.8"
    project_id: ID
    digest: Digest
    valid: bool
    findings: list[Text] = Field(default_factory=list, max_length=100)
    value: dict[str, JsonValue] = Field(default_factory=dict, max_length=30)
