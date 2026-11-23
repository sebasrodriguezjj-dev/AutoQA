"""Versioned inventory and deterministic, reviewed selection; no source execution."""

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    schema_version: Literal["0.6"] = "0.6"


class TestCase(Contract):
    id: str = Field(pattern=r"^TC-[A-Za-z0-9_-]+$")
    signature: str
    kind: Literal["UI", "API"]
    priority: Literal["Critical", "High", "Medium", "Low"] = "Medium"
    tags: list[str] = Field(default_factory=list)
    enabled: bool = True
    review_status: Literal["approved", "pending", "rejected"] = "approved"
    supported: bool = True


class TestPack(Contract):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")
    case_ids: list[str]


class TestSuite(Contract):
    project_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    id: str = Field(default="DEFAULT", pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")
    cases: list[TestCase]
    packs: list[TestPack] = Field(default_factory=list)
    review_status: Literal["pending", "approved"] = "pending"

    @model_validator(mode="after")
    def relationships(self):
        ids = [c.id for c in self.cases]
        packs = [p.id for p in self.packs]
        if len(ids) != len(set(ids)) or len(packs) != len(set(packs)):
            raise ValueError("Duplicate inventory identity")
        for pack in self.packs:
            if len(pack.case_ids) != len(set(pack.case_ids)) or not set(pack.case_ids) <= set(ids):
                raise ValueError("Invalid pack membership")
        return self


class TestSelection(Contract):
    mode: Literal["case", "pack", "suite", "all", "tag"] = "all"
    values: list[str] = Field(default_factory=list)


class ExecutionPlan(Contract):
    project_id: str
    suite_id: str
    pack_ids: list[str]
    selection: TestSelection
    case_ids: list[str]
    inventory_digest: str


class ExecutionResult(Contract):
    case_id: str
    status: Literal["PASSED", "FAILED", "ERROR", "SKIPPED", "NOT_EXECUTED", "UNSUPPORTED"]
    evidence: list[str] = Field(default_factory=list)


class ExecutionRun(Contract):
    run_id: str
    plan: ExecutionPlan
    started_at: str
    completed_at: str
    results: list[ExecutionResult]


def digest(suite):
    return hashlib.sha256(json.dumps(suite.model_dump(), sort_keys=True).encode()).hexdigest()


def select(suite, selection):
    if suite.review_status != "approved":
        raise ValueError("Suite membership requires explicit approval")
    cases = {c.id: c for c in suite.cases}
    values = selection.values
    if selection.mode == "all":
        if values:
            raise ValueError("Full regression takes no identifiers")
        selected = {c.id for c in suite.cases if c.enabled and c.review_status == "approved"}
    elif not values:
        raise ValueError("Selection requires identifiers")
    elif selection.mode == "case":
        selected = set(values)
        if not selected <= cases.keys():
            raise ValueError("Unknown case")
    elif selection.mode == "pack":
        packs = {p.id: p for p in suite.packs}
        if not set(values) <= packs.keys():
            raise ValueError("Unknown pack")
        if any(not packs[v].case_ids for v in values):
            raise ValueError("Empty pack")
        selected = {c for v in values for c in packs[v].case_ids}
    elif selection.mode == "suite":
        if values != [suite.id]:
            raise ValueError("Unknown suite")
        selected = {c.id for c in suite.cases if c.enabled and c.review_status == "approved"}
    else:
        selected = {c.id for c in suite.cases if set(values) & set(c.tags)}
    if not selected:
        raise ValueError("Empty selection")
    if any(not cases[c].enabled for c in selected):
        raise ValueError("Disabled case: NOT_EXECUTED")
    if any(cases[c].review_status != "approved" for c in selected):
        raise ValueError("Unauthorized case: NOT_EXECUTED")
    return ExecutionPlan(
        project_id=suite.project_id,
        suite_id=suite.id,
        pack_ids=values if selection.mode == "pack" else [],
        selection=selection,
        case_ids=sorted(selected),
        inventory_digest=digest(suite),
    )


def load_inventory(root, manifest):
    path = root / "review/management.json"
    if path.exists():
        if "review/management.json" not in manifest["files"]:
            raise ValueError("Unmanaged selection metadata")
        suite = TestSuite.model_validate_json(path.read_text(encoding="utf-8"))
        executable = {c.id: c.signature for c in suite.cases if c.supported}
        if executable != manifest["cases"]:
            raise ValueError("Management inventory differs from approved export")
        return suite
    # Read-only adapter for historical exports; never rewrites legacy data.
    return TestSuite(
        project_id="legacy",
        review_status="approved",
        cases=[
            TestCase(id=i, signature=s, kind="API" if i in manifest.get("parameters", {}) else "UI")
            for i, s in manifest["cases"].items()
        ],
    )
