"""Separately reviewed, revision-bound declarative repairs; no source patch execution."""

import ast
from pathlib import Path
from urllib.parse import urlsplit

from autoqa.authorization import require_authorization
from autoqa.core import Discovery, LocatorCandidate
from autoqa.functional import BehaviorContract, candidate_for, validate_contract
from autoqa.planning import case_signature, save_cases, verify_approval_binding
from autoqa.planning_identity import discovery_identity
from autoqa.v08_contracts import (
    LocatorSpec,
    MaintenanceChange,
    MaintenanceDecision,
    MaintenanceProposal,
    digest,
)
from autoqa.v08_io import checked_root, read_json
from autoqa.v08_reconciliation import _locator, managed_baseline, supported_manual_edit


def _safe(operation):
    try:
        return operation()
    except (
        ValueError,
        OSError,
        TypeError,
        KeyError,
        RecursionError,
        OverflowError,
        SyntaxError,
        StopIteration,
    ):
        raise ValueError("Invalid or stale maintenance input") from None


class MaintenanceService:
    def __init__(self, project, authorization=None):
        self.project = project
        self.authorization = authorization

    def _proposal(self, source, case_id, element_id, locator, manual_source):
        root, revision, manifest, blueprint = managed_baseline(source)
        if root.resolve().is_relative_to(self.project.root) or self.project.root.is_relative_to(
            root.resolve()
        ):
            raise ValueError("Source and project must be disjoint")
        if manual_source is not None:
            manual = checked_root(manual_source).resolve()
            if manual.is_relative_to(self.project.root) or self.project.root.is_relative_to(manual):
                raise ValueError("Manual source and project must be disjoint")
        if isinstance(locator, LocatorSpec):
            locator = locator.model_dump(mode="json")
        locator = LocatorSpec.model_validate(locator)
        raw_cases = read_json(self.project.storage.path("test-cases/test-matrix.json"))
        if (
            not isinstance(raw_cases, list)
            or len(raw_cases) > 1000
            or len({c["id"] for c in raw_cases}) != len(raw_cases)
        ):
            raise ValueError("Invalid case inventory")
        cases = self.project.cases()
        case = next(c for c in cases if c.id == case_id)
        if case.kind != "functional" or not case.feasible or case.review_status != "approved":
            raise ValueError("Unsupported repair kind or unapproved scenario")
        verify_approval_binding(self.project, case)
        signature = case_signature(case)
        if manifest["cases"].get(case_id) != signature:
            raise ValueError("Source does not represent the current approved scenario")
        scenario = next(s for s in blueprint["scenarios"] if s["id"] == case_id)
        if not scenario["methods"]:
            raise ValueError("Scenario lacks mapped source operations")
        discovery = Discovery.model_validate(
            read_json(self.project.storage.path("discovery/workflow-map.json"))
        )
        workflows, evidence, provenance = discovery_identity(discovery)
        page = next(p for p in discovery.pages if p.url == case.url)
        matching = [e for e in page.elements if e.id == element_id]
        if len(matching) != 1 or provenance.get(element_id) != "OBSERVED":
            raise ValueError("Repair requires unambiguous observed element identity")
        contract = BehaviorContract.model_validate(case.contract)
        if element_id not in {s.element_id for s in contract.steps} | {
            a.element_id for a in contract.assertions
        }:
            raise ValueError("Locator is unrelated to the approved case")
        if any(
            a.element_id == element_id and a.check in {"texts", "count", "ordered"}
            for a in contract.assertions
        ):
            raise ValueError("Collection locator repair remains manual")
        identities = [
            None,
            *[s.element_id for s in contract.steps],
            *[a.element_id for a in contract.assertions],
        ]
        if len(identities) != len(scenario["methods"]):
            raise ValueError("Source operations do not map the reviewed contract")
        target_methods = {
            method
            for method, identity in zip(scenario["methods"], identities, strict=True)
            if identity == element_id
        }
        page_blueprint = next(p for p in blueprint["pages"] if p["module"] == scenario["page"])
        properties = set()
        for operation in page_blueprint["operations"]:
            if operation["method"] in target_methods:
                properties.update(
                    n.attr
                    for n in ast.walk(ast.parse(operation["source"]))
                    if isinstance(n, ast.Attribute)
                    and isinstance(n.value, ast.Name)
                    and n.value.id == "self"
                    and n.attr in page_blueprint["locators"]
                )
        if len(properties) != 1:
            raise ValueError("Source locator mapping is ambiguous")
        original_property = next(iter(properties))
        original_locator = _locator(
            ast.parse(page_blueprint["locators"][original_property], mode="eval").body
        )
        if original_locator is None or original_locator == locator:
            raise ValueError("No supported locator change")
        local = self.project.config.allow_localhost and urlsplit(case.url).hostname in {
            "localhost",
            "127.0.0.1",
            "::1",
        }
        validate_contract(contract, discovery, local=local)
        selected = candidate_for(matching[0])
        replacement = LocatorCandidate.model_validate(locator.model_dump())
        if selected.model_dump() != replacement.model_dump():
            raise ValueError("Replacement must be the current canonical unique observed locator")
        # Binding all semantic observations is conservative: unrelated drift can require review,
        # but reused IDs, validation changes and conflicting observations cannot retain acceptance.
        evidence_digest = digest(
            {
                "domain": "v08-maintenance-evidence",
                "workflows": workflows,
                "evidence": evidence,
                "provenance": provenance,
                "configuration": self.project.config.model_dump(),
                "membership": self._optional("test-cases/management.json"),
                "membership_receipt": self._optional("test-cases/management-receipt.json"),
            }
        )
        data_digest = digest(
            {
                "domain": "v08-maintenance-data",
                "case_data": case.test_data,
                "inventory": self._optional("test-cases/test-data-v08.json"),
                "bindings": self._optional("test-cases/test-data-bindings-v08.json"),
            }
        )
        manual_revision = None
        if manual_source is not None:
            manual_revision = supported_manual_edit(
                self.project,
                root,
                manual_source,
                case_id,
                locator,
                original_property,
                target_methods,
            )
        payload = {
            "project_id": self.project.root.name,
            "case_id": case_id,
            "case_signature": signature,
            "source_revision": revision,
            "manual_revision": manual_revision,
            "evidence_digest": evidence_digest,
            "data_digest": data_digest,
            "original_behavior": case.expected,
            "change": MaintenanceChange(
                kind="locator_replacement",
                element_id=element_id,
                locator=locator,
                description="Replace "
                + original_locator.model_dump_json()
                + " with "
                + locator.model_dump_json()
                + "; preserve all behavior assertions.",
            ),
            "rationale": "Current observed semantic evidence supplies a unique locator for an explicitly referenced element. Root cause and runtime success remain unconfirmed.",
            "risk": "Medium",
            "limitations": [
                "Only a declarative locator replacement is supported; synchronization, arbitrary Python and patches remain manual.",
                "Acceptance never changes executable source, scenario approval, suite membership or execution permissions.",
                "The generated runtime is not an OS sandbox; observations and unsigned local review remain operator-supplied evidence.",
            ],
            "required_validation": [
                "Separate explicit application authorization",
                "Renewed scenario approval and independent suite review",
                "Fresh validated trusted export",
                "Actual authorized regression with original assertions",
            ],
        }
        candidate = MaintenanceProposal(id="MNT-PENDING", **payload)
        identity = "MNT-" + digest(
            {
                "domain": "v08-maintenance-proposal",
                **candidate.model_dump(mode="json", exclude={"id"}),
            }
        )
        return MaintenanceProposal.model_validate(
            candidate.model_dump(mode="json") | {"id": identity}
        )

    def _optional(self, reference):
        path = self.project.storage.path(reference)
        return read_json(path) if path.exists() else None

    def propose(self, source, case_id, element_id, locator, manual_source=None):
        return _safe(lambda: self._proposal(source, case_id, element_id, locator, manual_source))

    def _current(self, source, proposal, manual_source):
        if isinstance(proposal, (str, Path)):
            proposal = read_json(proposal)
        if isinstance(proposal, MaintenanceProposal):
            proposal = proposal.model_dump(mode="json")
        supplied = MaintenanceProposal.model_validate(proposal)
        if (
            supplied.change.kind != "locator_replacement"
            or supplied.change.locator is None
            or supplied.change.element_id is None
        ):
            raise ValueError("Unsupported maintenance transformation")
        current = self._proposal(
            source,
            supplied.case_id,
            supplied.change.element_id,
            supplied.change.locator,
            manual_source,
        )
        if supplied != current:
            raise ValueError("Proposal or current bindings changed")
        return current

    @staticmethod
    def _decision_path(proposal):
        return "maintenance/v08/decision-" + digest(proposal.id) + ".json"

    def review(self, source, proposal, decision, manual_source=None):
        require_authorization(self.authorization, self.project.root, "review")

        def operation():
            current = self._current(source, proposal, manual_source)
            record = MaintenanceDecision(
                project_id=self.project.root.name,
                proposal_id=current.id,
                proposal_digest=digest(current),
                decision=decision,
            )
            self.project.storage.write_json(
                self._decision_path(current), record.model_dump(mode="json")
            )
            return record

        return _safe(operation)

    def apply(self, source, proposal, manual_source=None):
        require_authorization(self.authorization, self.project.root, "maintain")
        require_authorization(self.authorization, self.project.root, "review")

        def operation():
            current = self._current(source, proposal, manual_source)
            decision = MaintenanceDecision.model_validate(
                read_json(self.project.storage.path(self._decision_path(current)))
            )
            if (
                decision.project_id != self.project.root.name
                or decision.proposal_id != current.id
                or decision.proposal_digest != digest(current)
                or decision.decision != "accepted"
            ):
                raise ValueError("Current accepted review is required")
            cases = self.project.cases()
            original = next(c for c in cases if c.id == current.case_id)
            revised = original.model_copy(deep=True)
            revised.review_status = "pending"
            revised.description = (
                original.description + "\nReviewed maintenance revision " + current.id
            )
            if case_signature(revised) == case_signature(original):
                raise ValueError("Revision must invalidate the original approval binding")
            # Preserve the immutable behavior fields; only pending status/revision metadata changes.
            before = original.model_dump(exclude={"review_status", "description"})
            if revised.model_dump(exclude={"review_status", "description"}) != before:
                raise ValueError("Maintenance cannot change reviewed behavior")
            save_cases(
                self.project,
                [revised if c.id == revised.id else c for c in cases],
                authorization=self.authorization,
            )
            return revised

        return _safe(operation)
