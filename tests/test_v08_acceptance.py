"""Independent V0.8 acceptance over owned API runs and explicit inventory snapshots."""

import json
import os
import subprocess
from pathlib import Path

import pytest
from test_api_framework import api_server as api_server

from autoqa.api_service import plan_api
from autoqa.application import ApplicationEngine
from autoqa.authorization import AuthorizationContext
from autoqa.framework_runtime.contracts import APIScenario
from autoqa.management import approve_suite, propose
from autoqa.planning import approve, case_signature, save_cases, verify_approval_binding
from autoqa.v08_contracts import LocatorSpec


def context(project, *operations):
    return AuthorizationContext(project.root, frozenset(operations))


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file() and ".venv" not in p.relative_to(root).parts
    }


def api_case(project, tmp_path, origin, *, authentication=None):
    scenario = APIScenario.model_validate(
        {
            "id": "TC-QA-API",
            "title": "Independent owned API acceptance",
            "request": {"path": "/health", "query": {"q": "${query}"}},
            "expect": {"status": 200, "json_values": {"healthy": True, "query.q.0": "${query}"}},
            "environments": [{"name": "local", "origin": origin, "allow_localhost": True}],
            "environment": "local",
            "data": {"name": "original", "rows": [{"query": "original"}]},
            **({"authentication": authentication} if authentication else {}),
        }
    )
    auth = context(project, "plan", "review", "generate", "execute", "maintain")
    plan_api(project, write_json(tmp_path / "api.json", [scenario.model_dump()]), auth)
    approve(project, [scenario.id], authorization=auth)
    return scenario, auth


def approved_export(project, auth, destination):
    approve(project, [c.id for c in project.cases()], authorization=auth)
    approve_suite(project, propose(project), auth)
    ApplicationEngine(project, auth).build_framework(destination)
    installed = subprocess.run(
        ["uv", "sync"], cwd=destination, capture_output=True, text=True, timeout=120
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    python = destination / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    isolated = subprocess.run(
        [
            str(python),
            "-c",
            "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
        ],
        cwd=destination,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert isolated.returncode == 0, isolated.stdout + isolated.stderr
    return python


def execute(python, export):
    previous = (
        set((export / "artifacts").glob("*/results.json"))
        if (export / "artifacts").exists()
        else set()
    )
    process = subprocess.run(
        [
            str(python),
            "-m",
            "qa_runtime.runner",
            "run",
            "--all",
        ],
        cwd=export,
        capture_output=True,
        text=True,
        timeout=60,
    )
    created = set((export / "artifacts").glob("*/results.json")) - previous
    assert len(created) == 1, process.stdout + process.stderr
    path = created.pop()
    return process, path, json.loads(path.read_text(encoding="utf-8"))


def test_synthetic_alias_flows_through_approval_independent_execution_and_genuine_diagnosis(
    project,
    tmp_path,
    api_server,
):
    from autoqa.v08_data import TestDataService as DataService
    from autoqa.v08_diagnosis import DiagnosisService

    origin, handler = api_server
    _, auth = api_case(project, tmp_path, origin)
    old = project.cases()[0]
    old_expected, old_request = old.contract["expect"], old.contract["request"]
    source = write_json(
        tmp_path / "data.json",
        {
            "project_id": project.root.name,
            "definitions": [
                {
                    "alias": "datasets.health",
                    "kind": "value",
                    "environments": ["local"],
                    "sensitivity": "SYNTHETIC",
                    "values": [{"query": "independent-owned"}],
                }
            ],
        },
    )
    data = DataService(project, auth)
    data.import_inventory(source)
    bound = data.bind_case("datasets.health", old.id, "local")
    assert bound.review_status == "pending"
    assert case_signature(bound) != case_signature(old)
    assert bound.contract["expect"] == old_expected
    assert bound.contract["request"] == old_request
    assert bound.contract["data"]["rows"] == [{"query": "independent-owned"}]
    with pytest.raises(ValueError):
        verify_approval_binding(project, bound)
    with pytest.raises(ValueError):
        ApplicationEngine(project, auth).build_framework(tmp_path / "must-refuse-pending")
    export = tmp_path / "approved-export"
    python = approved_export(project, auth, export)
    before_project = snapshot(project.root)
    healthy_process, healthy_path, healthy = execute(python, export)
    assert healthy_process.returncode == 0
    assert healthy["counts"] == {"PASSED": 1}
    assert len(healthy["steps"]) == 2
    assert healthy["evidence_policy"] == "summary_only"
    assert len(healthy["diagnostic_snapshot"]) == 1
    assert set(healthy["diagnostic_snapshot"][0]) == {
        "id",
        "kind",
        "signature",
        "operation_count",
        "review_status",
    }
    assert any("independent-owned" in path for _, path in handler.hits)
    healthy_report = DiagnosisService(project).analyze(healthy_path)
    assert any(f.category == "HEALTHY_RECORDED_EXECUTION" for f in healthy_report.findings)
    assert all(not f.root_cause_confirmed for f in healthy_report.findings)

    handler.broken = True
    defect_process, defect_path, defect = execute(python, export)
    assert defect_process.returncode != 0
    assert defect["counts"] == {"FAILED": 1}
    assert defect["steps"][-1]["status"] == "FAILED"
    report = DiagnosisService(project).analyze(defect_path)
    assert any(f.category == "ASSERTION_MISMATCH" and f.case_id == old.id for f in report.findings)
    assert all(not f.root_cause_confirmed for f in report.findings)
    payload = report.model_dump_json()
    assert "synthetic-response-sensitive" not in payload
    assert "independent-owned" not in payload
    assert str(export) not in payload
    assert snapshot(project.root) == before_project
    # Imported file claims cannot override contradictory current-run evidence.
    for name, mutation in [
        ("missing-snapshot", {"diagnostic_snapshot": []}),
        ("missing-operation", {"steps": defect["steps"][:-1]}),
        (
            "foreign-operation",
            {"steps": [*defect["steps"], defect["steps"][0] | {"test_id": "TC-FOREIGN"}]},
        ),
    ]:
        path = write_json(tmp_path / f"{name}.json", defect | mutation)
        attacked = DiagnosisService(project).analyze(path)
        assert all(not finding.root_cause_confirmed for finding in attacked.findings)
        assert not any(
            finding.category == "HEALTHY_RECORDED_EXECUTION" for finding in attacked.findings
        )
        assert any(
            finding.category
            in {"EVIDENCE_INTEGRITY_FAILURE", "INCOMPLETE_EXECUTION", "INSUFFICIENT_EVIDENCE"}
            or finding.missing_evidence
            for finding in attacked.findings
        )
    duplicate = write_json(
        tmp_path / "duplicate-invocation.json",
        defect
        | {
            "records": [*defect["records"], defect["records"][0]],
        },
    )
    with pytest.raises(ValueError):
        DiagnosisService(project).analyze(duplicate)
    # Historical run interpretation cannot silently drift with the latest case.
    changed = project.cases()
    changed[0].expected = "Unrelated later approved behavior"
    changed[0].review_status = "pending"
    save_cases(project, changed, authorization=auth)
    assert DiagnosisService(project).analyze(defect_path) == report
    assert (
        json.loads((export / "review/cases.json").read_text(encoding="utf-8"))[0]["contract"][
            "expect"
        ]
        == old_expected
    )


def test_missing_credential_reference_fails_at_authorized_execution_without_echo(
    project,
    tmp_path,
    api_server,
    monkeypatch,
):
    from autoqa.v08_data import TestDataService as DataService
    from autoqa.v08_diagnosis import DiagnosisService

    origin, handler = api_server
    _, auth = api_case(
        project,
        tmp_path,
        origin,
        authentication={
            "strategy": "bearer",
            "token_env": "AUTOQA_SECRET_PREVIOUS",
        },
    )
    name = "AUTOQA_SECRET_QA_MISSING"
    monkeypatch.delenv(name, raising=False)
    source = write_json(
        tmp_path / "credential-reference.json",
        {
            "project_id": project.root.name,
            "definitions": [
                {
                    "alias": "users.standard",
                    "kind": "credential",
                    "environments": ["local"],
                    "sensitivity": "SECRET_REFERENCE",
                    "reference": name,
                }
            ],
        },
    )
    service = DataService(project, auth)
    service.import_inventory(source)
    # Analysis stores and validates only the reference, with no secret resolution.
    assert service.validate_alias("users.standard", "local").valid
    pending = service.bind_case("users.standard", "TC-QA-API", "local")
    assert pending.review_status == "pending"
    assert pending.contract["authentication"]["strategy"] == "bearer"
    assert pending.contract["authentication"]["token_env"] == name
    export = tmp_path / "missing-auth-export"
    python = approved_export(project, auth, export)
    process, run_path, result = execute(python, export)
    assert process.returncode != 0
    assert not handler.hits, "Missing credentials must fail before an HTTP request"
    assert result["counts"].get("ERROR", 0) + result["counts"].get("FAILED", 0) == 1
    report = DiagnosisService(project).analyze(run_path)
    assert all(not finding.root_cause_confirmed for finding in report.findings)
    assert "synthetic-response-sensitive" not in report.model_dump_json()


def test_explicit_application_inventory_change_is_potential_not_executed_impact(project, tmp_path):
    from autoqa.v08_impact import ImpactService

    objects = [
        {
            "id": "OBJ-ROUTE",
            "kind": "route",
            "source_location": "application/routes.py",
            "semantics": {"path": "/owned"},
            "case_ids": ["TC-ROUTE"],
            "requirement_ids": ["REQ-ROUTE"],
            "page_objects": ["pages/route.py"],
        },
        {
            "id": "OBJ-UNCHANGED",
            "kind": "control",
            "source_location": "application/other.html",
            "semantics": {"name": "Unrelated control"},
            "case_ids": ["TC-UNRELATED"],
        },
    ]
    before = write_json(
        tmp_path / "before.json", {"project_id": project.root.name, "objects": objects}
    )
    changed = objects[0] | {"semantics": {"path": "/owned-renamed"}}
    after = write_json(
        tmp_path / "after.json", {"project_id": project.root.name, "objects": [objects[1], changed]}
    )
    original_project = snapshot(project.root)
    original_inputs = before.read_bytes(), after.read_bytes()
    report = ImpactService(project).compare(before, after)
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.object_id == "OBJ-ROUTE" and finding.change == "CHANGED"
    assert finding.potential_case_ids == ["TC-ROUTE"]
    assert finding.requirement_ids == ["REQ-ROUTE"]
    assert finding.page_objects == ["pages/route.py"]
    assert not finding.verified_runtime_impact
    assert "TC-UNRELATED" in report.unaffected_case_ids
    assert snapshot(project.root) == original_project
    assert (before.read_bytes(), after.read_bytes()) == original_inputs
    reordered = write_json(
        tmp_path / "reordered.json",
        {"project_id": project.root.name, "objects": list(reversed(objects))},
    )
    equivalent = ImpactService(project).compare(before, reordered)
    assert equivalent.findings == []
    assert equivalent.before_digest == equivalent.after_digest


def recorded_fixture(project):
    return {
        "schema_version": "0.6",
        "project_id": project.root.name,
        "run_id": "RUN-OWNED",
        "exit_code": 0,
        "selected_case_ids": ["TC-OWNED"],
        "diagnostic_snapshot": [
            {
                "id": "TC-OWNED",
                "kind": "api",
                "signature": "a" * 64,
                "operation_count": 2,
                "review_status": "approved",
            }
        ],
        "records": [
            {
                "id": "TC-OWNED--row-0",
                "case_id": "TC-OWNED",
                "name": "test_TC_OWNED[0]",
                "status": "PASSED",
                "error": "",
            }
        ],
        "steps": [
            {
                "run_id": "RUN-OWNED",
                "test_id": "TC-OWNED--row-0",
                "step_id": f"TC-OWNED--row-0:step-{i}",
                "sequence": i,
                "kind": "navigation" if i == 1 else "assertion",
                "status": "PASSED",
            }
            for i in [1, 2]
        ],
    }


@pytest.mark.parametrize(
    "attack",
    [
        "orphan",
        "wrong-run",
        "wrong-order",
        "missing-operation",
        "failed-no-failed-operation",
        "nonzero-exit",
    ],
)
def test_contradictory_imported_run_cannot_support_unqualified_health_or_defect(
    project, tmp_path, attack
):
    from autoqa.v08_diagnosis import DiagnosisService

    value = recorded_fixture(project)
    if attack == "orphan":
        value["steps"].append(value["steps"][0] | {"test_id": "TC-FOREIGN"})
    elif attack == "wrong-run":
        value["steps"][0]["run_id"] = "RUN-OTHER"
    elif attack == "wrong-order":
        value["steps"].reverse()
    elif attack == "missing-operation":
        value["steps"].pop()
    elif attack == "failed-no-failed-operation":
        value["records"][0].update(
            status="FAILED", error="AssertionError: synthetic-private-sentinel"
        )
        value["exit_code"] = 1
        value["steps"].pop()
    else:
        value["exit_code"] = 1
    source = write_json(tmp_path / "recorded.json", value)
    before = snapshot(project.root), source.read_bytes()
    report = DiagnosisService(project).analyze(source)
    assert not any(f.category == "HEALTHY_RECORDED_EXECUTION" for f in report.findings)
    assert any(
        f.category
        in {"EVIDENCE_INTEGRITY_FAILURE", "INCOMPLETE_EXECUTION", "INSUFFICIENT_EVIDENCE"}
        or f.missing_evidence
        for f in report.findings
    )
    assert all(not f.root_cause_confirmed for f in report.findings)
    assert "synthetic-private-sentinel" not in report.model_dump_json()
    assert (snapshot(project.root), source.read_bytes()) == before


def data_input(tmp_path, project, *, reference="fixtures/data.json", kind="json"):
    path = tmp_path / "inventory.json"
    path.write_text(
        json.dumps(
            {
                "project_id": project.root.name,
                "definitions": [
                    {
                        "alias": "datasets.owned",
                        "kind": kind,
                        "environments": ["local"],
                        "sensitivity": "SYNTHETIC",
                        "reference": reference,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_external_file_alias_requires_authorized_unambiguous_root_and_fresh_content(
    project, tmp_path
):
    from autoqa.authorization import AuthorizationContext
    from autoqa.v08_data import TestDataService as DataService

    first, second = tmp_path / "first", tmp_path / "second"
    for root in [first, second]:
        (root / "fixtures").mkdir(parents=True)
        (root / "fixtures/data.json").write_text('[{"query":"owned"}]', encoding="utf-8")
    source = data_input(tmp_path, project)
    service = DataService(project, AuthorizationContext(project.root, frozenset({"plan"})))
    before = snapshot(project.root)
    with pytest.raises(ValueError):
        service.import_inventory(source)
    assert snapshot(project.root) == before
    with pytest.raises(ValueError):
        service.import_inventory(source, authorized_roots=(first, second))
    assert snapshot(project.root) == before
    service.import_inventory(source, authorized_roots=(first,))
    original = service.validate_alias("datasets.owned", "local")
    assert original.valid
    (first / "fixtures/data.json").write_text('[{"query":"changed"}]', encoding="utf-8")
    protected = snapshot(project.root)
    with pytest.raises(ValueError):
        service.validate_alias("datasets.owned", "local")
    assert snapshot(project.root) == protected


@pytest.mark.parametrize(
    "reference",
    ["../outside.json", "/absolute.json", "C:/private.json", "https://remote.test/data.json"],
)
def test_test_data_references_refuse_traversal_absolute_and_remote_input(
    project, tmp_path, reference
):
    from autoqa.authorization import AuthorizationContext
    from autoqa.v08_data import TestDataService as DataService

    source = data_input(tmp_path, project, reference=reference)
    before = snapshot(project.root)
    with pytest.raises(ValueError) as caught:
        DataService(
            project, AuthorizationContext(project.root, frozenset({"plan"}))
        ).import_inventory(source, authorized_roots=(tmp_path,))
    assert "C:/private" not in str(caught.value)
    assert "https://remote" not in str(caught.value)
    assert snapshot(project.root) == before


def test_missing_import_authorization_is_checked_before_source_reads(
    project, tmp_path, monkeypatch
):
    from autoqa.v08_data import TestDataService as DataService

    source = data_input(tmp_path, project)
    service = DataService(project)

    def forbidden(*args, **kwargs):
        pytest.fail("Unauthorized import attempted filesystem read")

    monkeypatch.setattr(Path, "open", forbidden)
    with pytest.raises(ValueError):
        service.import_inventory(source, authorized_roots=(tmp_path,))


def test_inventory_tampering_is_refused_without_repair(project, tmp_path):
    from autoqa.authorization import AuthorizationContext
    from autoqa.v08_data import INVENTORY
    from autoqa.v08_data import TestDataService as DataService

    source = tmp_path / "owned-values.json"
    source.write_text(
        json.dumps(
            {
                "project_id": project.root.name,
                "definitions": [
                    {
                        "alias": "datasets.owned",
                        "kind": "value",
                        "environments": ["local"],
                        "sensitivity": "SYNTHETIC",
                        "values": [{"query": "owned"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    service = DataService(project, AuthorizationContext(project.root, frozenset({"plan"})))
    service.import_inventory(source)
    payload = project.storage.read_json(INVENTORY)

    # Mutate a synthetic recorded value while retaining its stored integrity metadata.
    def replace_owned(value):
        if isinstance(value, dict):
            return {key: replace_owned(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace_owned(item) for item in value]
        return "tampered-owned" if value == "owned" else value

    changed = replace_owned(payload)
    assert changed != payload
    project.storage.write_json(INVENTORY, changed)
    before = snapshot(project.root)
    with pytest.raises(ValueError):
        service.inspect()
    assert snapshot(project.root) == before


@pytest.fixture
def maintenance_fixture(project, tmp_path):
    from autoqa.authorization import AuthorizationContext
    from autoqa.core import (
        Discovery,
        Element,
        EvidenceReference,
        LocatorCandidate,
        PageEvidence,
        Workflow,
    )
    from autoqa.framework import FrameworkService
    from autoqa.functional import BehaviorContract, functional_case
    from autoqa.management import approve_suite, propose
    from autoqa.planning import approve, save_cases

    url = "http://127.0.0.1:8123/form"
    project.config.application_url = url
    project.config.allow_localhost = True
    project.config.allowed_domains = ["127.0.0.1"]
    project.save_config()
    auth = AuthorizationContext(project.root, frozenset({"review", "generate", "maintain"}))
    amount = Element(
        id="EL-AMOUNT",
        kind="input",
        name="Amount",
        input_type="number",
        role="spinbutton",
        locators=[LocatorCandidate(strategy="test_id", value="amount-old", count=1)],
    )
    result = Element(
        id="EL-RESULT",
        kind="div",
        name="Result",
        role="status",
        locators=[LocatorCandidate(strategy="test_id", value="result", count=1)],
    )
    discovery = Discovery(
        pages=[
            PageEvidence(
                url=url,
                title="Owned form",
                headings=["Owned form"],
                elements=[amount, result],
                screenshot="owned.png",
                depth=0,
            )
        ],
        workflows=[
            Workflow(
                id="WF-FORM",
                name="Owned form",
                page_url=url,
                elements=["Amount"],
                element_ids=[amount.id, result.id],
                evidence=[],
                steps=["Fill amount"],
                status="OBSERVED",
                kind="form",
            )
        ],
        evidence_records=[
            EvidenceReference(
                id=e.id, category="OBSERVED", description="Synthetic observation", page_url=url
            )
            for e in [amount, result]
        ],
    )
    project.storage.write_json("discovery/workflow-map.json", discovery.model_dump())
    contract = BehaviorContract.model_validate(
        {
            "id": "AMOUNT",
            "title": "Owned amount result",
            "page_url": url,
            "workflow": "form",
            "test_type": "Positive",
            "basis": "OBSERVED",
            "source": "Owned synthetic requirements",
            "evidence_ids": [amount.id, result.id],
            "steps": [{"action": "fill", "element_id": amount.id, "value": "3"}],
            "assertions": [
                {"check": "text", "element_id": result.id, "expected": "Approved result"}
            ],
        }
    )
    case = functional_case(contract, discovery, local=True)
    save_cases(project, [case], authorization=auth)
    approve(project, [case.id], authorization=auth)
    approve_suite(project, propose(project), auth)
    source = tmp_path / "managed-baseline"
    FrameworkService(project, auth).build(source)
    # Synthetic static fixture: runtime browser observations are separately accepted by Framework.
    discovery.pages[0].elements[0].locators = [
        LocatorCandidate(strategy="test_id", value="amount-new", count=1)
    ]
    project.storage.write_json("discovery/workflow-map.json", discovery.model_dump())
    return project, source, project.cases()[0], auth


def proposal_for(fixture):
    from autoqa.v08_maintenance import MaintenanceService

    project, source, case, auth = fixture
    locator = LocatorSpec(strategy="test_id", value="amount-new")
    service = MaintenanceService(project, auth)
    return service, service.propose(source, case.id, "EL-AMOUNT", locator)


def test_maintenance_acceptance_does_not_apply_or_approve_source(maintenance_fixture, tmp_path):
    from autoqa.authorization import AuthorizationContext
    from autoqa.framework import FrameworkService
    from autoqa.planning import case_signature, verify_approval_binding
    from autoqa.v08_maintenance import MaintenanceService

    project, source, original, _ = maintenance_fixture
    before_source, before_project = snapshot(source), snapshot(project.root)
    service, proposal = proposal_for(maintenance_fixture)
    assert snapshot(source) == before_source
    assert snapshot(project.root) == before_project
    assert proposal.original_behavior == original.expected
    assert proposal.review_status == "pending"
    review_only = MaintenanceService(
        project, AuthorizationContext(project.root, frozenset({"review"}))
    )
    decision = review_only.review(source, proposal, "accepted")
    assert decision.decision == "accepted"
    assert snapshot(source) == before_source
    assert project.cases()[0] == original
    after_review = snapshot(project.root)
    with pytest.raises(ValueError):
        review_only.apply(source, proposal)
    assert snapshot(project.root) == after_review
    revised = service.apply(source, proposal)
    assert revised.review_status == "pending"
    assert case_signature(revised) != case_signature(original)
    assert revised.expected == original.expected
    assert revised.contract == original.contract
    assert revised.steps == original.steps
    assert revised.url == original.url
    assert snapshot(source) == before_source
    with pytest.raises(ValueError):
        verify_approval_binding(project, revised)
    with pytest.raises(ValueError):
        FrameworkService(
            project, AuthorizationContext(project.root, frozenset({"generate"}))
        ).build(tmp_path / "refuse-unapproved")


@pytest.mark.parametrize(
    "field", ["behavior", "project", "case-signature", "evidence", "source-root", "locator", "id"]
)
def test_tampered_proposal_never_becomes_an_accepted_decision(maintenance_fixture, field):
    from autoqa.v08_contracts import MaintenanceProposal

    project, source, _, _ = maintenance_fixture
    service, proposal = proposal_for(maintenance_fixture)
    payload = proposal.model_dump()
    if field == "behavior":
        payload["original_behavior"] = "Fabricated expected outcome"
    elif field == "project":
        payload["project_id"] = "other-project"
    elif field == "case-signature":
        payload["case_signature"] = "a" * 64
    elif field == "evidence":
        payload["evidence_digest"] = "b" * 64
    elif field == "source-root":
        payload["source_revision"]["root_binding"] = "c" * 64
    elif field == "locator":
        payload["change"]["locator"]["value"] = "unobserved-control"
    else:
        payload["id"] = "MNT-tampered"
    changed = MaintenanceProposal.model_validate(payload)
    before_source, before_project = snapshot(source), snapshot(project.root)
    with pytest.raises(ValueError):
        service.review(source, changed, "accepted")
    assert snapshot(source) == before_source
    assert snapshot(project.root) == before_project


@pytest.mark.parametrize("drift", ["source", "case", "evidence", "root"])
def test_accepted_decision_cannot_apply_after_bound_context_drift(
    maintenance_fixture, tmp_path, drift
):
    import shutil

    from autoqa.planning import save_cases

    project, source, _, auth = maintenance_fixture
    service, proposal = proposal_for(maintenance_fixture)
    service.review(source, proposal, "accepted")
    if drift == "source":
        path = next((source / "pages").glob("*.py"))
        path.write_text(
            path.read_text(encoding="utf-8") + "\n# changed source revision\n", encoding="utf-8"
        )
    elif drift == "case":
        cases = project.cases()
        cases[0].expected = "Changed reviewed expectation"
        save_cases(project, cases, authorization=auth)
    elif drift == "evidence":
        discovery = project.storage.read_json("discovery/workflow-map.json")
        discovery["pages"][0]["elements"][0]["required"] = True
        project.storage.write_json("discovery/workflow-map.json", discovery)
    else:
        copied = tmp_path / "substituted-baseline"
        shutil.copytree(source, copied)
        source = copied
    before_source, before_project = snapshot(source), snapshot(project.root)
    with pytest.raises(ValueError):
        service.apply(source, proposal)
    assert snapshot(source) == before_source
    assert snapshot(project.root) == before_project


def test_reconciliation_does_not_execute_malicious_new_or_changed_source(
    maintenance_fixture, tmp_path
):
    import shutil

    from autoqa.v08_reconciliation import ReconciliationService

    project, baseline, _, _ = maintenance_fixture
    current = tmp_path / "manual"
    shutil.copytree(baseline, current)
    marker = tmp_path / "MUST-NOT-EXIST"
    (current / "conftest.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    page = next((current / "pages").glob("*.py"))
    page.write_text(
        page.read_text(encoding="utf-8")
        + "\nraise RuntimeError('never execute inspected source')\n",
        encoding="utf-8",
    )
    before = snapshot(current), snapshot(project.root)
    report = ReconciliationService(project).inspect(baseline, current)
    assert any(
        f.state in {"UNSUPPORTED", "INTEGRITY_VIOLATION", "MANUAL_CANDIDATE"}
        for f in report.findings
    )
    assert any(
        not f.supported for f in report.findings if f.path == page.relative_to(current).as_posix()
    )
    assert not marker.exists()
    assert (snapshot(current), snapshot(project.root)) == before


def test_file_data_import_rejects_linked_ancestor_before_child_probe(
    project, tmp_path, monkeypatch
):
    from autoqa.authorization import AuthorizationContext
    from autoqa.v08_data import TestDataService as DataService

    root, target = tmp_path / "authorized-root", tmp_path / "owned-target"
    root.mkdir()
    target.mkdir()
    (target / "data.json").write_text('[{"query":"owned"}]', encoding="utf-8")
    linked = root / "fixtures"
    if os.name == "nt":
        created = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(linked), str(target)],
            capture_output=True,
            text=True,
        )
        assert created.returncode == 0, "Owned test junction creation must succeed on Windows"
    else:
        linked.symlink_to(target, target_is_directory=True)
    source = data_input(tmp_path, project)
    service = DataService(project, AuthorizationContext(project.root, frozenset({"plan"})))
    original_project, original_target = snapshot(project.root), snapshot(target)

    def protect(original):
        def inspect(path, *args, **kwargs):
            if path != linked and path.is_relative_to(linked):
                pytest.fail("Data import probed a child before rejecting its linked ancestor")
            return original(path, *args, **kwargs)

        return inspect

    for name in ["exists", "is_symlink", "is_junction", "is_file", "stat", "open", "resolve"]:
        monkeypatch.setattr(Path, name, protect(getattr(Path, name)))
    with pytest.raises(ValueError):
        service.import_inventory(source, authorized_roots=(root,))
    assert snapshot(project.root) == original_project
    assert snapshot(target) == original_target


@pytest.mark.parametrize("drift", ["data-inventory", "membership"])
def test_accepted_review_is_stale_after_relevant_data_or_membership_change(
    maintenance_fixture, tmp_path, drift
):
    from autoqa.authorization import AuthorizationContext
    from autoqa.management import approve_suite, propose
    from autoqa.v08_data import TestDataService as DataService

    project, source, _, auth = maintenance_fixture
    service, proposal = proposal_for(maintenance_fixture)
    service.review(source, proposal, "accepted")
    if drift == "data-inventory":
        data_path = write_json(
            tmp_path / "changed-data.json",
            {
                "project_id": project.root.name,
                "definitions": [
                    {
                        "alias": "datasets.revised",
                        "kind": "value",
                        "environments": ["local"],
                        "sensitivity": "SYNTHETIC",
                        "values": [{"amount": 7}],
                    }
                ],
            },
        )
        DataService(
            project, AuthorizationContext(project.root, frozenset({"plan"}))
        ).import_inventory(data_path)
    else:
        membership = propose(project)
        membership.cases[0].tags = ["reviewed-new-scope"]
        approve_suite(project, membership, auth)
    source_before, project_before = snapshot(source), snapshot(project.root)
    with pytest.raises(ValueError):
        service.apply(source, proposal)
    assert snapshot(source) == source_before
    assert snapshot(project.root) == project_before


def test_maintenance_decision_cannot_be_substituted_or_downgraded_then_applied(
    maintenance_fixture,
):
    project, source, _, _ = maintenance_fixture
    service, proposal = proposal_for(maintenance_fixture)
    service.review(source, proposal, "accepted")
    decisions = list((project.root / "maintenance/v08").glob("decision-*.json"))
    assert len(decisions) == 1
    decision_path = decisions[0]
    original = json.loads(decision_path.read_text(encoding="utf-8"))
    for attack in [
        {"project_id": "other-project"},
        {"proposal_id": "MNT-OTHER"},
        {"proposal_digest": "b" * 64},
        {"decision": "rejected"},
    ]:
        write_json(decision_path, original | attack)
        source_before, project_before = snapshot(source), snapshot(project.root)
        with pytest.raises(ValueError):
            service.apply(source, proposal)
        assert snapshot(source) == source_before
        assert snapshot(project.root) == project_before


def test_proposal_and_reconciliation_are_readonly_deterministic_static_operations(
    maintenance_fixture, monkeypatch
):
    from autoqa.v08_reconciliation import ReconciliationService

    project, source, _, _ = maintenance_fixture
    source_before, project_before = snapshot(source), snapshot(project.root)

    def forbidden(*args, **kwargs):
        pytest.fail("Static inspection attempted to run a process")

    monkeypatch.setattr(subprocess, "run", forbidden)
    service, first = proposal_for(maintenance_fixture)
    _, second = proposal_for(maintenance_fixture)
    assert first == second
    assert first.id == second.id
    unchanged = ReconciliationService(project).inspect(source, source)
    assert unchanged.baseline == unchanged.current
    assert all(f.state == "UNCHANGED_MANAGED" for f in unchanged.findings)
    assert snapshot(source) == source_before
    assert snapshot(project.root) == project_before
