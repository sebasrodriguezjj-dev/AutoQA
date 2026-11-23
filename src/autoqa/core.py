"""Validated contracts, isolated project storage and local metadata."""

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from autoqa.storage import (
    LocalProjectStorage,
    register_project,
    selected_root,
)
from autoqa.storage import (
    load_json as load_json,
)
from autoqa.storage import (
    save_json as save_json,
)


class APIResourceRule(BaseModel):
    """Operator-reviewed exact read-only resources; never grant navigation permission."""

    model_config = ConfigDict(extra="forbid")
    origin: str
    path: str
    methods: list[Literal["GET", "HEAD"]] = Field(
        default_factory=lambda: ["GET"], min_length=1, max_length=2
    )
    query: dict[str, list[str]] = Field(default_factory=dict)
    enabled: bool = False
    approval_reference: str = Field(min_length=5, max_length=200)

    @field_validator("origin")
    @classmethod
    def exact_origin(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or not re.fullmatch(r"[A-Za-z0-9.-]+", parsed.hostname)
            or any(ord(c) < 33 for c in value)
        ):
            raise ValueError(
                "API origin must be an exact HTTP(S) origin without path, credentials or wildcards."
            )
        if parsed.port == 0:
            raise ValueError("API origin requires a valid nonzero port.")
        return value.lower()

    @field_validator("path")
    @classmethod
    def exact_path(cls, value: str) -> str:
        if not re.fullmatch(r"/[A-Za-z0-9/_-]{1,200}", value) or "//" in value:
            raise ValueError(
                "API path must be a literal path without wildcards, encodings or traversal."
            )
        return value

    @field_validator("query")
    @classmethod
    def exact_query_values(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        if len(value) > 10:
            raise ValueError("Too many API query keys.")
        for key, values in value.items():
            if (
                not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,39}", key)
                or re.search(r"token|password|secret|auth|key|session", key, re.I)
                or not 1 <= len(values) <= 20
                or any(len(v) > 200 or any(ord(c) < 32 for c in v) or "*" in v for v in values)
            ):
                raise ValueError(
                    "API queries require non-sensitive keys and bounded exact approved values."
                )
        return value


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    application_url: str | None = None
    repository: str | None = None
    mode: Literal["ui", "repository", "hybrid"] = "ui"
    allowed_domains: list[str] = Field(default_factory=list)
    allow_localhost: bool = False
    max_pages: int = Field(default=10, ge=1, le=100)
    max_depth: int = Field(default=2, ge=0, le=5)
    navigation_timeout_ms: int = Field(default=15000, ge=100, le=60000)
    overall_timeout_seconds: int = Field(default=120, ge=1, le=600)
    headless: bool = True
    slow_mo_ms: int = Field(default=0, ge=0, le=2000)
    screenshot_policy: Literal["every_step", "failures_only", "disabled"] = "failures_only"
    trace_enabled: bool = True
    auth_reference: str | None = None
    ai_provider: Literal["offline", "openai"] = "offline"
    ai_model: str | None = None
    test_preferences: dict[str, str] = Field(default_factory=lambda: {"browser": "chromium"})
    request_interval_ms: int = Field(default=150, ge=0, le=5000)
    excluded_paths: list[str] = Field(default_factory=list, max_length=100)
    api_resources: list[APIResourceRule] = Field(default_factory=list, max_length=20)
    max_requests: int = Field(default=300, ge=1, le=1000)
    spa_readiness_timeout_ms: int = Field(default=3000, ge=50, le=15000)
    spa_quiet_window_ms: int = Field(default=200, ge=16, le=1000)


class LocatorCandidate(BaseModel):
    strategy: Literal["role", "label", "placeholder", "test_id"]
    value: str
    name: str = ""
    count: int = Field(ge=0)


class Element(BaseModel):
    kind: str
    name: str = ""
    href: str | None = None
    input_type: str | None = None
    required: bool = False
    id: str = ""
    role: str = ""
    attributes: dict[str, str] = Field(default_factory=dict)
    locators: list[LocatorCandidate] = Field(default_factory=list)
    options: list[dict[str, str]] = Field(default_factory=list)
    form: str | None = None
    evidence: list[str] = Field(default_factory=list)
    discovered_at: str = ""
    components: list[str] = Field(default_factory=list)


class PageEvidence(BaseModel):
    url: str
    title: str
    headings: list[str]
    elements: list[Element]
    screenshot: str
    depth: int
    status: Literal["OBSERVED"] = "OBSERVED"
    dynamic_signals: list[str] = Field(default_factory=list)
    readiness: dict = Field(default_factory=dict)


class Workflow(BaseModel):
    id: str
    name: str
    page_url: str
    elements: list[str]
    evidence: list[str]
    steps: list[str]
    preconditions: list[str] = Field(
        default_factory=lambda: ["Authorized test environment is available"]
    )
    status: Literal[
        "INFERRED", "OBSERVED", "SOURCE", "REQUIRES_REVIEW", "VERIFIED_REQUIREMENT", "UNKNOWN"
    ]
    review_required: bool = True
    kind: str = "observation"
    expected_behavior: str = "Unknown; requires review"
    required_test_data: dict[str, str] = Field(default_factory=dict)
    feasible: bool = False
    risk: Literal["Low", "Medium", "High"] = "Low"
    element_ids: list[str] = Field(default_factory=list)


class EvidenceReference(BaseModel):
    id: str
    category: Literal["OBSERVED", "SOURCE", "VERIFIED_REQUIREMENT", "INFERRED", "UNKNOWN"]
    description: str
    page_url: str = ""
    artifact: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class Discovery(BaseModel):
    pages: list[PageEvidence] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    evidence_records: list[EvidenceReference] = Field(default_factory=list)
    blocked_requests: list[dict[str, str]] = Field(default_factory=list)


class TestCase(BaseModel):
    id: str = Field(pattern=r"^TC-[A-Za-z0-9_-]+$")
    feature: str
    title: str
    description: str
    preconditions: list[str]
    steps: list[str]
    expected: str
    priority: Literal["Critical", "High", "Medium", "Low"] = "Medium"
    test_type: str = "UI Validation"
    evidence: list[str]
    feasible: bool = True
    review_status: Literal["pending", "approved", "rejected"] = "pending"
    kind: Literal["heading", "link", "manual", "functional", "api"]
    url: str
    target: str = ""
    destination: str | None = None
    test_data: dict[str, str] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    workflow_id: str | None = None
    contract: dict | None = None

    @model_validator(mode="after")
    def api_contract(self):
        if self.kind == "api":
            from autoqa.framework_runtime.contracts import APIScenario

            scenario = APIScenario.model_validate(self.contract)
            env = next(e for e in scenario.environments if e.name == scenario.environment)
            if scenario.id != self.id or self.url != env.origin + scenario.request.path:
                raise ValueError("API case identity/URL differs from its reviewed contract")
        return self


class Project:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.storage = LocalProjectStorage(self.root)
        config_path = self.root / "config.yaml"
        if not config_path.is_file():
            raise ValueError(f"No AutoQA project at {self.root}. Use init or --project PATH.")
        self.config = Config.model_validate(self.storage.read_config())
        for folder in (
            "discovery",
            "test-cases",
            "automation",
            "reports",
            "screenshots",
            "artifacts",
            "logs",
        ):
            if (self.root / folder).is_symlink() or (self.root / folder).is_junction():
                raise ValueError(f"Project artifact directory cannot be a link: {folder}")

    def save_config(self) -> None:
        self.storage.write_config(self.config.model_dump())

    def audit(self, event: str) -> None:
        self.storage.append_event({"time": datetime.now(UTC).isoformat(), "event": event})

    def cases(self) -> list[TestCase]:
        return [
            TestCase.model_validate(item)
            for item in self.storage.read_json("test-cases/test-matrix.json")
        ]

    def discovery(self) -> Discovery:
        return Discovery.model_validate(self.storage.read_json("discovery/workflow-map.json"))


def initialize(name: str, parent: Path) -> Project:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", name):
        raise ValueError("Project names must be 1–64 letters, digits, underscores or hyphens.")
    if name.upper().split(".")[0] in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(10)),
        *(f"LPT{i}" for i in range(10)),
    }:
        raise ValueError("Reserved Windows project name.")
    root = parent.resolve() / name
    root.mkdir(parents=True, exist_ok=False)
    for folder in (
        "discovery",
        "test-cases",
        "automation",
        "reports",
        "screenshots",
        "artifacts",
        "logs",
    ):
        (root / folder).mkdir()
    (root / "config.yaml").write_text(
        yaml.safe_dump(Config(name=name).model_dump()), encoding="utf-8"
    )
    register_project(parent, name, root)
    project = Project(root)
    project.audit("project.initialized")
    return project


def select_project(explicit: Path | None) -> Project:
    return Project(selected_root(explicit))
