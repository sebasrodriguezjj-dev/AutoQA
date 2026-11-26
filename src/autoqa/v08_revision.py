"""Trusted-local maintenance identity enforced before review, compilation and execution.

Only hashes of expanded trusted compiler operations are persisted, never inspected code.
The baseline must remain available; historical independent exports need no source access.
"""

import ast
from pathlib import Path

from pydantic import Field

from autoqa.core import Discovery
from autoqa.planning_identity import discovery_identity
from autoqa.security import Scope
from autoqa.v08_contracts import (
    ID,
    Contract,
    Digest,
    MaintenanceDecision,
    MaintenanceProposal,
    digest,
)
from autoqa.v08_io import read_json, source_revision


class MaintenanceRevision(Contract):
    schema_version: str = Field(default="0.8", pattern=r"^0\.8$")
    proposal: MaintenanceProposal
    source_root: str = Field(min_length=1, max_length=4096)
    manual_root: str | None = Field(default=None, max_length=4096)
    context: Digest
    case_revisions: dict[ID, Digest] = Field(min_length=1, max_length=1000)
    operations: dict[ID, list[Digest]] = Field(min_length=1, max_length=1000)


class ActiveRevisions(Contract):
    cases: dict[ID, Digest] = Field(min_length=1, max_length=1000)


ACTIVE = "maintenance/v08/active-revisions.json"


def active_revisions(project):
    path = project.storage.path(ACTIVE)
    return ActiveRevisions.model_validate(read_json(path)).cases if path.exists() else {}


def persist_revision(project, record, revised):
    current = {
        c.id: c.maintenance_revision for c in project.cases() if c.maintenance_revision is not None
    }
    if active_revisions(project) != current:
        raise ValueError("Maintenance revision index changed")
    revised.maintenance_revision = digest(record)
    project.storage.write_json(
        revision_path(revised.maintenance_revision), record.model_dump(mode="json")
    )
    project.storage.write_json(
        ACTIVE,
        ActiveRevisions(cases=current | {revised.id: revised.maintenance_revision}).model_dump(),
    )


def revision_path(identity):
    return "maintenance/v08/revision-" + identity + ".json"


def content_revision(case):
    return digest(case.model_dump(exclude={"review_status", "maintenance_revision"}))


def context_identity(project):
    discovery = Discovery.model_validate(
        read_json(project.storage.path("discovery/workflow-map.json"))
    )
    return digest(
        {
            "domain": "v08-maintenance-revision-context",
            "observations": discovery_identity(discovery),
            "config": project.config.model_dump(),
            "stored_config": project.storage.read_config(),
            "data": [
                read_json(project.storage.path(path))
                if project.storage.path(path).exists()
                else None
                for path in (
                    "test-cases/test-data-v08.json",
                    "test-cases/test-data-bindings-v08.json",
                )
            ],
        }
    )


class Expand(ast.NodeTransformer):
    def __init__(self, locators):
        self.locators = locators

    def visit_Attribute(self, node):
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and node.attr in self.locators
        ):
            return ast.parse(self.locators[node.attr], mode="eval").body
        return self.generic_visit(node)


def operation_identity(kind, source):
    return digest({"kind": kind, "ast": ast.dump(ast.parse(source))})


def blueprint_operations(blueprint):
    result = {}
    for scenario in blueprint["scenarios"]:
        page = next(p for p in blueprint["pages"] if p["module"] == scenario["page"])
        operations = {op["method"]: op for op in page["operations"]}
        result[scenario["id"]] = [
            operation_identity(
                operations[method]["kind"],
                ast.unparse(
                    Expand(page["locators"]).visit(ast.parse(operations[method]["source"]))
                ),
            )
            for method in scenario["methods"]
        ]
    for scenario in blueprint.get("api_scenarios", []):
        result[scenario["id"]] = [digest(scenario)]
    return result


def current_operations(project, cases):
    # Reuse trusted rendering without invoking compile_blueprint (which checks us).
    from autoqa.framework import _operations, _PageLocators

    discovery = project.discovery()
    scope = Scope(project.config.application_url, project.config)
    result = {}
    for case in cases:
        if case.kind == "api":
            result[case.id] = [digest(case.contract)]
            continue
        result[case.id] = []
        for kind, _, source in _operations(case, discovery, scope):
            properties = {}
            lifted = _PageLocators(properties).visit(ast.parse(source))
            expanded = Expand(properties).visit(lifted)
            result[case.id].append(operation_identity(kind, ast.unparse(expanded)))
    return result


def create_revision(project, source, blueprint, proposal, original, revised, manual_source):
    from autoqa.core import LocatorCandidate
    from autoqa.functional import locator_expression

    # Change only the targeted case's referenced operations in a copy of the validated
    # baseline. A shared property must not authorize other cases' changes.
    expected = blueprint_operations(blueprint)
    scenario = next(s for s in blueprint["scenarios"] if s["id"] == original.id)
    page = next(p for p in blueprint["pages"] if p["module"] == scenario["page"])
    identities = (
        [None]
        + [s["element_id"] for s in original.contract["steps"]]
        + [a.get("element_id") for a in original.contract["assertions"]]
    )
    methods = {
        method
        for method, identity in zip(scenario["methods"], identities, strict=True)
        if identity == proposal.change.element_id
    }
    properties = set()
    for operation in page["operations"]:
        if operation["method"] in methods:
            properties.update(
                node.attr
                for node in ast.walk(ast.parse(operation["source"]))
                if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
                and node.attr in page["locators"]
            )
    if len(properties) != 1:
        raise ValueError("Ambiguous maintenance operation mapping")
    prop = next(iter(properties))
    replacement = locator_expression(
        LocatorCandidate.model_validate(proposal.change.locator.model_dump())
    ).replace("page.", "self.page.", 1)
    operations = {operation["method"]: operation for operation in page["operations"]}
    expected[original.id] = [
        operation_identity(
            operations[method]["kind"],
            ast.unparse(
                Expand(page["locators"] | ({prop: replacement} if method in methods else {})).visit(
                    ast.parse(operations[method]["source"])
                )
            ),
        )
        for method in scenario["methods"]
    ]
    cases = [revised if c.id == revised.id else c for c in project.cases()]
    represented = [c for c in cases if c.id in expected]
    if current_operations(project, represented) != expected:
        raise ValueError("Repair changes unrelated operations; affected-case review remains manual")
    return MaintenanceRevision(
        proposal=proposal,
        source_root=str(Path(source).absolute()),
        manual_root=str(Path(manual_source).absolute()) if manual_source is not None else None,
        context=context_identity(project),
        case_revisions={c.id: content_revision(c) for c in cases},
        operations=expected,
    )


def verify_revisions(project):
    """Read-only, fail closed before writes/processes. Renewed receipts are independent."""
    cases = project.cases()
    references = {c.id: c.maintenance_revision for c in cases if c.maintenance_revision is not None}
    if active_revisions(project) != references:
        raise ValueError("Missing or changed maintenance revision reference/index")
    bindings = {c.maintenance_revision for c in cases if c.maintenance_revision is not None}
    if bindings and (len(cases) > 1000 or len({c.id for c in cases}) != len(cases)):
        raise ValueError("Invalid maintenance case inventory")
    for identity in sorted(bindings):
        try:
            record = MaintenanceRevision.model_validate(
                read_json(project.storage.path(revision_path(identity)))
            )
            if digest(record) != identity or record.proposal.project_id != project.root.name:
                raise ValueError("Revision identity mismatch")
            decision = MaintenanceDecision.model_validate(
                read_json(
                    project.storage.path(
                        "maintenance/v08/decision-" + digest(record.proposal.id) + ".json"
                    )
                )
            )
            if (
                decision.project_id != project.root.name
                or decision.proposal_id != record.proposal.id
                or decision.proposal_digest != digest(record.proposal)
                or decision.decision != "accepted"
            ):
                raise ValueError("Accepted maintenance decision changed")
            bound_case = next(c for c in cases if c.id == record.proposal.case_id)
            if bound_case.maintenance_revision != identity:
                raise ValueError("Revision case mismatch")
            if {c.id: content_revision(c) for c in cases} != record.case_revisions:
                raise ValueError("Case revision inventory changed")
            if context_identity(project) != record.context:
                raise ValueError("Maintenance evidence/configuration/data changed")
            if source_revision(Path(record.source_root)) != record.proposal.source_revision:
                raise ValueError("Maintenance baseline changed")
            if (
                record.manual_root is not None
                and source_revision(Path(record.manual_root)) != record.proposal.manual_revision
            ):
                raise ValueError("Manual source changed")
            represented = [c for c in cases if c.id in record.operations]
            if current_operations(project, represented) != record.operations:
                raise ValueError("Compiled maintenance operations changed")
        except ValueError, OSError, TypeError, KeyError, StopIteration, RecursionError, SyntaxError:
            raise ValueError(
                "Invalid or stale maintenance revision; new reviewed proposal required"
            ) from None
