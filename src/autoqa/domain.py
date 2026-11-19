"""Versioned data contracts. No runtime adapters or implicit migrations."""

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal, Self
from uuid import uuid4

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, JsonValue, model_validator


def artifact_reference(value: str) -> str:
    if (
        not value
        or "\\" in value
        or PureWindowsPath(value).drive
        or PurePosixPath(value).is_absolute()
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or ":" in value
    ):
        raise ValueError("Artifact references must be project-relative paths without traversal.")
    return value


ArtifactReference = Annotated[str, AfterValidator(artifact_reference)]
Identity = Annotated[str, Field(min_length=1)]


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class GenerationStatus(StrEnum):
    NOT_GENERATED = "NOT_GENERATED"
    GENERATED = "GENERATED"
    UNKNOWN = "UNKNOWN"


class ExecutionStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
    NOT_EXECUTED = "NOT_EXECUTED"
    NOT_RECORDED = "NOT_RECORDED"


class Provenance(StrEnum):
    OBSERVED = "OBSERVED"
    SOURCE = "SOURCE"
    VERIFIED_REQUIREMENT = "VERIFIED_REQUIREMENT"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class Sensitivity(StrEnum):
    UNKNOWN = "UNKNOWN"
    INTERNAL = "INTERNAL"
    SENSITIVE = "SENSITIVE"


class StepKind(StrEnum):
    ACTION = "action"
    ASSERTION = "assertion"
    OBSERVATION = "observation"


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.3"] = "0.3"
    id: Identity = Field(default_factory=lambda: str(uuid4()))
    legacy: dict[str, JsonValue] | None = None


class Project(Contract):
    name: str
    revision: int | None = Field(default=None, ge=1)
    config: dict[str, JsonValue] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def utc_times(self) -> Self:
        for value in (self.created_at, self.updated_at):
            if value is not None and (
                value.tzinfo is None or value.utcoffset().total_seconds() != 0
            ):
                raise ValueError("Timestamps must be UTC-aware.")
        return self


class Evidence(Contract):
    project_id: Identity
    name: str = ""
    provenance: Provenance = Provenance.UNKNOWN
    sensitivity: Sensitivity = Sensitivity.UNKNOWN
    producer: str | None = None
    producer_version: str | None = None
    observed_at: datetime | None = None
    run_id: str | None = None
    case_id: str | None = None
    step_id: str | None = None
    description: str = ""
    artifact: ArtifactReference | None = None
    media_type: str | None = None
    digest: str | None = None

    @model_validator(mode="after")
    def observed_utc(self) -> Self:
        if self.observed_at is not None and self.observed_at.utcoffset() != UTC.utcoffset(None):
            raise ValueError("Observed timestamp must be UTC-aware.")
        return self


class TestStep(Contract):
    case_id: Identity
    ordinal: int = Field(ge=1)
    kind: StepKind = StepKind.OBSERVATION
    description: str
    # Legacy prose and unknown behavior are deliberately not executable.
    supported: Literal[False] = False
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    evidence_ids: list[Identity] = Field(default_factory=list)


class TestCase(Contract):
    suite_id: Identity
    revision: int | None = Field(default=None, ge=1)
    title: str
    feature: str = ""
    test_type: str = ""
    priority: str = "Medium"
    preconditions: list[str] = Field(default_factory=list)
    feasible: bool | None = None
    feasibility_reason: str | None = None
    evidence_ids: list[Identity] = Field(default_factory=list)
    expected: str
    steps: list[TestStep] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.PENDING
    review_actor: str | None = None
    reviewed_at: datetime | None = None
    signature: str | None = None
    review_source: str | None = None

    @model_validator(mode="after")
    def relationships(self) -> Self:
        if any(step.case_id != self.id for step in self.steps):
            raise ValueError("Step belongs to a different case.")
        if len({s.id for s in self.steps}) != len(self.steps) or [
            s.ordinal for s in self.steps
        ] != list(range(1, len(self.steps) + 1)):
            raise ValueError("Steps require unique IDs and contiguous ordinals.")
        if self.reviewed_at is not None and self.reviewed_at.utcoffset() != UTC.utcoffset(None):
            raise ValueError("Review timestamp must be UTC-aware.")
        return self


class TestSuite(Contract):
    project_id: Identity
    revision: int | None = Field(default=None, ge=1)
    derived: bool = False
    case_ids: list[Identity] = Field(default_factory=list)
    generation_status: GenerationStatus = GenerationStatus.NOT_GENERATED
    manifest: ArtifactReference | None = None
    evidence_ids: list[Identity] = Field(default_factory=list)
    generator_version: str | None = None
    runtime_version: str | None = None

    @model_validator(mode="after")
    def unique_cases(self) -> Self:
        if len(self.case_ids) != len(set(self.case_ids)):
            raise ValueError("Suite case identities must be unique.")
        return self


class StepResult(Contract):
    run_id: Identity
    case_id: Identity
    step_id: Identity
    attempt: int = Field(default=1, ge=1)
    status: ExecutionStatus = ExecutionStatus.NOT_RECORDED
    duration: float | None = Field(default=None, ge=0)
    error: str | None = None
    evidence_ids: list[Identity] = Field(default_factory=list)
    started_at: datetime | None = None
    ended_at: datetime | None = None

    @model_validator(mode="after")
    def times(self) -> Self:
        for value in (self.started_at, self.ended_at):
            if value is not None and value.utcoffset() != UTC.utcoffset(None):
                raise ValueError("Step timestamps must be UTC-aware.")
        if self.started_at and self.ended_at and self.ended_at < self.started_at:
            raise ValueError("Step end precedes start.")
        return self


class TestResult(Contract):
    run_id: Identity
    case_id: Identity
    status: ExecutionStatus
    duration: float | None = Field(default=None, ge=0)
    error: str | None = None
    steps: list[StepResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def relationships(self) -> Self:
        if any(s.run_id != self.run_id or s.case_id != self.case_id for s in self.steps):
            raise ValueError("Step result belongs to another execution.")
        return self


class TestRun(Contract):
    project_id: Identity
    suite_id: Identity
    results: list[TestResult]
    snapshot: dict[str, JsonValue]
    artifact_dir: ArtifactReference
    created_at: datetime | None = None
    exit_code: int | None = None

    @model_validator(mode="after")
    def relationships(self) -> Self:
        if any(r.run_id != self.id for r in self.results):
            raise ValueError("Result belongs to a different run.")
        if self.created_at is not None and self.created_at.utcoffset() != UTC.utcoffset(None):
            raise ValueError("Run timestamp must be UTC-aware.")
        return self
