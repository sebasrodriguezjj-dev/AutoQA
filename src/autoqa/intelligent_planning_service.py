"""Bounded local adapters for review-only V0.7 planning; legacy cases stay untouched."""

import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

from pydantic import ValidationError

from autoqa.authorization import require_authorization
from autoqa.core import Discovery, TestCase
from autoqa.management import export_inventory
from autoqa.planning import case_signature, verify_approval_binding
from autoqa.planning_contracts import (
    MAX_INPUT_BYTES,
    PlanningCase,
    PlanningContext,
    PlanningReview,
    PlanningSnapshot,
)
from autoqa.planning_identity import discovery_identity

REQUIREMENTS = "test-cases/requirements-v07.json"
REVIEWS = "test-cases/planning-review-v07.json"
MATRIX = "test-cases/test-matrix.json"
DISCOVERY = "discovery/workflow-map.json"
RECEIPTS = "test-cases/approval-receipts.json"
MEMBERSHIP = "test-cases/management.json"
MEMBERSHIP_RECEIPT = "test-cases/management-receipt.json"
SOURCE_LIMIT = 5_000_000
SIDECAR_LIMIT = 1_000_000


def _read_bytes(path, limit):
    """Reject links and bound the actual read as well as the observed file size."""
    try:
        path = Path(path).absolute()
        if any(p.is_symlink() or p.is_junction() for p in [path, *path.parents]):
            raise ValueError("Planning input cannot contain links")
        if not path.is_file():
            raise ValueError("Required planning input is missing or not a regular file")
        if path.stat().st_size > limit:
            raise ValueError("Planning input exceeds size limit")
        with path.open("rb") as stream:
            payload = stream.read(limit + 1)
        if len(payload) > limit:
            raise ValueError("Planning input exceeds size limit")
        return payload
    except OSError:
        raise ValueError("Planning input could not be read") from None


def _json(payload):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(_):
        raise ValueError("Non-finite JSON value")

    try:
        return json.loads(
            payload.decode("utf-8-sig"), object_pairs_hook=pairs, parse_constant=invalid_constant
        )
    except ValueError, RecursionError, OverflowError:
        raise ValueError("Invalid planning JSON") from None


def _bounded_serialization(value, limit):
    if len(json.dumps(value, indent=2, ensure_ascii=False).encode("utf-8")) > limit:
        raise ValueError("Serialized planning input exceeds size limit")


class IntelligentPlanningService:
    """Analysis is read-only; import/review have explicit project-bound intent."""

    def __init__(self, project, authorization=None):
        self.project = project
        self.authorization = authorization

    def _optional(self, reference, limit):
        path = self.project.storage.path(reference)
        if not path.exists():
            return None
        value = _json(_read_bytes(path, limit))
        if value is None:
            raise ValueError("Present planning JSON cannot be null")
        return value

    def _requirements(self, requirements):
        from autoqa.qa_planning import parse_requirements

        try:
            path = (
                Path(requirements)
                if requirements is not None
                else self.project.storage.path(REQUIREMENTS)
            )
            return parse_requirements(_read_bytes(path, MAX_INPUT_BYTES))
        except ValueError, TypeError, RecursionError, OverflowError:
            raise ValueError("Invalid or missing V0.7 requirements") from None

    def import_requirements(self, path):
        require_authorization(self.authorization, self.project.root, "plan")
        document = self._requirements(path)
        value = document.model_dump(mode="json")
        _bounded_serialization(value, MAX_INPUT_BYTES)
        self.project.storage.write_json(REQUIREMENTS, value)
        return document

    def _context(self):
        try:
            return self._context_from_snapshot()
        except ValueError, TypeError, KeyError, RecursionError, OverflowError:
            raise ValueError("Invalid current planning context") from None

    def _context_from_snapshot(self):
        raw_cases = self._optional(MATRIX, SOURCE_LIMIT)
        if raw_cases is None:
            cases = []
        else:
            if not isinstance(raw_cases, list) or len(raw_cases) > 1000:
                raise ValueError("Invalid case inventory")
            cases = [TestCase.model_validate(value) for value in raw_cases]
            if len({case.id for case in cases}) != len(cases):
                raise ValueError("Duplicate case identity")
        raw_discovery = self._optional(DISCOVERY, SOURCE_LIMIT)
        workflow_ids, evidence_ids = [], []
        workflow_provenance, evidence_provenance = {}, {}
        workflow_fingerprints, evidence_fingerprints = {}, {}
        if raw_discovery is not None:
            discovery = Discovery.model_validate(raw_discovery)
            if len(discovery.workflows) > 2000:
                raise ValueError("Too many observed workflows")
            workflow_ids = [workflow.id for workflow in discovery.workflows]
            if len(set(workflow_ids)) != len(workflow_ids):
                raise ValueError("Duplicate workflow identity")
            workflow_provenance = {workflow.id: workflow.status for workflow in discovery.workflows}
            workflow_fingerprints, evidence_fingerprints, evidence_provenance = discovery_identity(
                discovery
            )
            if len(evidence_provenance) > 5000:
                raise ValueError("Too many evidence identities")
            evidence_ids = sorted(evidence_provenance)
        receipts = self._optional(RECEIPTS, SIDECAR_LIMIT)
        membership = self._optional(MEMBERSHIP, SIDECAR_LIMIT)
        membership_receipt = self._optional(MEMBERSHIP_RECEIPT, SIDECAR_LIMIT)
        # Existing approval/suite validators operate on the same bounded read snapshot.
        # This avoids rereading a large receipt file once for every current case.
        cached = {
            RECEIPTS: receipts,
            MEMBERSHIP: membership,
            MEMBERSHIP_RECEIPT: membership_receipt,
        }
        snapshot_project = SimpleNamespace(
            root=self.project.root,
            storage=SimpleNamespace(path=self.project.storage.path, read_json=cached.__getitem__),
            cases=lambda: cases,
        )
        valid_receipts = {}
        for case in cases:
            valid_receipts[case.id] = False
            if case.review_status == "approved":
                try:
                    verify_approval_binding(snapshot_project, case)
                    valid_receipts[case.id] = True
                except ValueError:
                    pass
        suite_id, suite_digest, suite_state = None, None, "ABSENT"
        memberships = {}
        packs = {}
        if membership is not None:
            from autoqa.framework_runtime.management import TestSuite

            TestSuite.model_validate(membership)
            suite_digest = hashlib.sha256(
                json.dumps([membership, membership_receipt], sort_keys=True).encode("utf-8")
            ).hexdigest()
            suite_state = "STALE"
            try:
                suite = export_inventory(
                    snapshot_project, [c for c in cases if c.feasible and c.kind != "manual"], {}
                )
                if suite.project_id != self.project.root.name:
                    raise ValueError("Foreign suite")
                memberships = {case.id: case for case in suite.cases}
                packs = {
                    case.id: sorted(p.id for p in suite.packs if case.id in p.case_ids)
                    for case in cases
                }
                suite_id, suite_state = suite.id, "CURRENT"
            except ValueError, TypeError, KeyError:
                memberships, packs = {}, {}
        context_cases = []
        for case in cases:
            member = memberships.get(case.id)
            context_cases.append(
                PlanningCase(
                    id=case.id,
                    signature=case_signature(case),
                    review_status=case.review_status,
                    receipt_valid=valid_receipts[case.id],
                    supported=case.feasible and case.kind != "manual",
                    kind=case.kind,
                    title=case.title,
                    enabled=member.enabled if member else True,
                    pack_ids=packs.get(case.id, []),
                    tags=sorted(member.tags) if member else [],
                )
            )
        return PlanningContext(
            project_id=self.project.root.name,
            cases=context_cases,
            workflow_ids=sorted(workflow_ids),
            evidence_ids=evidence_ids,
            workflow_provenance=dict(sorted(workflow_provenance.items())),
            evidence_provenance=dict(sorted(evidence_provenance.items())),
            workflow_fingerprints=workflow_fingerprints,
            evidence_fingerprints=evidence_fingerprints,
            suite_id=suite_id,
            suite_state=suite_state,
            suite_digest=suite_digest,
        )

    def _review_record(self):
        raw = self._optional(REVIEWS, SIDECAR_LIMIT)
        if raw is None:
            return None
        try:
            return PlanningReview.model_validate(raw)
        except ValueError, TypeError, RecursionError:
            raise ValueError("Invalid planning review record") from None

    def analyze(self, requirements=None):
        from autoqa.qa_planning import build_plan

        document = self._requirements(requirements)
        context = self._context()
        snapshot = build_plan(document, context)
        record = self._review_record()
        if record is None:
            return snapshot
        data = snapshot.model_dump(mode="json")
        if record.plan_id != snapshot.id:
            data["review_state"] = "STALE"
        else:
            valid_ids = {proposal.id for proposal in snapshot.proposals}
            if not record.decisions.keys() <= valid_ids:
                raise ValueError("Invalid planning review relationships")
            data["review_state"] = "CURRENT"
            for proposal in data["proposals"]:
                proposal["review_status"] = record.decisions.get(proposal["id"], "pending")
        try:
            return PlanningSnapshot.model_validate(data)
        except ValidationError:
            raise ValueError("Invalid planning review projection") from None

    def review(self, plan_id, proposal_ids, decision):
        require_authorization(self.authorization, self.project.root, "review")
        if (
            not isinstance(plan_id, str)
            or re.fullmatch(r"PLAN-[a-f0-9]{64}", plan_id) is None
            or type(proposal_ids) is not list
            or not 1 <= len(proposal_ids) <= 1500
            or any(not isinstance(value, str) for value in proposal_ids)
            or len(set(proposal_ids)) != len(proposal_ids)
            or not isinstance(decision, str)
            or decision not in {"accepted", "rejected"}
        ):
            raise ValueError("Invalid planning review request")
        snapshot = self.analyze()
        if snapshot.id != plan_id:
            raise ValueError("Planning snapshot changed; analyze and review the current plan")
        if not set(proposal_ids) <= {proposal.id for proposal in snapshot.proposals}:
            raise ValueError("Unknown planning proposal")
        previous = self._review_record()
        decisions = dict(previous.decisions) if previous and previous.plan_id == plan_id else {}
        decisions.update(dict.fromkeys(proposal_ids, decision))
        record = PlanningReview(plan_id=plan_id, decisions=decisions)
        value = record.model_dump(mode="json")
        _bounded_serialization(value, SIDECAR_LIMIT)
        self.project.storage.write_json(REVIEWS, value)
        return self.analyze()
