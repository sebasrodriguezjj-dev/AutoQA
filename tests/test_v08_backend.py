"""Historical diagnosis, potential impact and reviewed synthetic alias boundaries."""

import copy
import json
import os
import subprocess

import pytest

from autoqa.authorization import AuthorizationContext
from autoqa.core import TestCase as Case
from autoqa.framework_runtime.contracts import APIScenario
from autoqa.planning import approve, case_signature, save_cases, verify_approval_binding
from autoqa.v08_data import BINDINGS, INVENTORY
from autoqa.v08_data import TestDataService as DataService
from autoqa.v08_diagnosis import DiagnosisService
from autoqa.v08_impact import ImpactService


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def auth(project, *operations):
    return AuthorizationContext(project.root, frozenset(operations))


def files(project):
    return {
        p.relative_to(project.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in project.root.rglob("*")
        if p.is_file()
    }


def api_case(project, authentication=None):
    contract = APIScenario.model_validate(
        {
            "id": "TC-API",
            "title": "Owned synthetic response",
            "request": {"path": "/health"},
            "expect": {"status": 200},
            "environment": "local",
            "environments": [
                {"name": "local", "origin": "http://127.0.0.1:8123", "allow_localhost": True}
            ],
            **({"authentication": authentication} if authentication else {}),
        }
    )
    case = Case(
        id=contract.id,
        feature="Owned API",
        title=contract.title,
        description="Synthetic reviewed API",
        preconditions=[],
        steps=["GET health"],
        expected="Reviewed healthy response",
        evidence=[],
        kind="api",
        url="http://127.0.0.1:8123/health",
        contract=contract.model_dump(),
    )
    save_cases(project, [case], authorization=auth(project, "review"))
    approve(project, [case.id], authorization=auth(project, "review"))
    return project.cases()[0]


def recorded(case):
    return {
        "run_id": "owned-run",
        "selected_case_ids": [case.id],
        "diagnostic_snapshot": [
            {
                "id": case.id,
                "kind": "API",
                "signature": case_signature(case),
                "operation_count": 2,
                "review_status": "approved",
            }
        ],
        "records": [
            {
                "id": case.id,
                "case_id": case.id,
                "status": "FAILED",
                "name": "test_TC_API",
                "error": "AssertionError private-sentinel",
            }
        ],
        "steps": [
            {
                "run_id": "owned-run",
                "test_id": case.id,
                "step_id": f"{case.id}:step-{i}",
                "sequence": i,
                "kind": "action" if i == 1 else "assertion",
                "status": "PASSED" if i == 1 else "FAILED",
            }
            for i in (1, 2)
        ],
    }


def inventory(project, **definition):
    return {
        "project_id": project.root.name,
        "definitions": [
            {
                "alias": "datasets.health",
                "kind": "value",
                "environments": ["local"],
                "sensitivity": "SYNTHETIC",
                "values": [{"query": "owned"}],
                **definition,
            }
        ],
    }


def test_diagnosis_is_historical_and_suppressed(project, tmp_path):
    case = api_case(project)
    source = write(tmp_path / "run.json", recorded(case))
    service = DiagnosisService(project)
    before = files(project)
    first = service.analyze(source)
    assert files(project) == before
    finding = first.findings[0]
    assert finding.category == "ASSERTION_MISMATCH" and not finding.root_cause_confirmed
    assert {h.category for h in finding.hypotheses} >= {
        "APPLICATION_DEFECT_CANDIDATE",
        "AUTOMATION_DEFECT_CANDIDATE",
    }
    assert "private-sentinel" not in first.model_dump_json()
    cases = project.cases()
    cases[0].expected = "Changed current expectation"
    save_cases(project, cases, authorization=auth(project, "review"))
    assert service.analyze(source) == first


@pytest.mark.parametrize(
    "change", ["run", "sequence", "step-id", "missing-pass", "foreign", "duplicate"]
)
def test_inconsistent_evidence_cannot_be_healthy(project, tmp_path, change):
    value = recorded(api_case(project))
    if change == "run":
        value["steps"][0]["run_id"] = "other-run"
    if change == "sequence":
        value["steps"][0]["sequence"] = 3
    if change == "step-id":
        value["steps"][0]["step_id"] = "TC-OTHER:step-1"
    if change == "missing-pass":
        value["records"][0]["status"] = "PASSED"
        value["steps"] = []
    if change == "foreign":
        value["selected_case_ids"] = ["TC-OTHER"]
    if change == "duplicate":
        value["records"].append(dict(value["records"][0]))
    source = write(tmp_path / "run.json", value)
    if change == "duplicate":
        with pytest.raises(ValueError, match="Invalid bounded recorded-run"):
            DiagnosisService(project).analyze(source)
    else:
        findings = DiagnosisService(project).analyze(source).findings
        assert any(f.category == "EVIDENCE_INTEGRITY_FAILURE" for f in findings)
        assert not any(
            f.category in {"HEALTHY_RECORDED_EXECUTION", "APPLICATION_DEFECT_CANDIDATE"}
            for f in findings
        )


def test_missing_snapshot_is_not_replaced_by_latest_approved_case(project, tmp_path):
    value = recorded(api_case(project))
    del value["diagnostic_snapshot"]
    plan = DiagnosisService(project).analyze(write(tmp_path / "run.json", value))
    assert "Historical approved case snapshot" in plan.findings[0].missing_evidence[0]
    assert not plan.findings[0].maintenance_appropriate


def test_volatile_metadata_does_not_invalidate_diagnosis(project, tmp_path):
    value = recorded(api_case(project))
    source = write(tmp_path / "run.json", value)
    first = DiagnosisService(project).analyze(source)
    value["created_at"], value["duration"] = "later", 100
    value["steps"][0]["timestamp"] = "later"
    value["steps"][0]["evidence"] = ["new-private.png"]
    assert DiagnosisService(project).analyze(write(source, value)) == first


def test_impact_is_potential_and_deterministic(project, tmp_path):
    objects = [
        {
            "id": "control-name",
            "kind": "validation",
            "source_location": "app/form.html",
            "semantics": {"min": "1"},
            "case_ids": ["TC-ONE"],
            "requirement_ids": ["REQ-ONE"],
        },
        {
            "id": "route-other",
            "kind": "route",
            "source_location": "app/other.py",
            "semantics": {"path": "/other"},
            "case_ids": ["TC-OTHER"],
        },
    ]
    before = {"project_id": project.root.name, "objects": objects}
    after = copy.deepcopy(before)
    after["objects"][0]["semantics"]["min"] = "5"
    left, right = write(tmp_path / "old.json", before), write(tmp_path / "new.json", after)
    state = files(project)
    report = ImpactService(project).compare(left, right)
    assert report.findings[0].potential_case_ids == ["TC-ONE"]
    assert report.unaffected_case_ids == ["TC-OTHER"]
    assert not report.findings[0].verified_runtime_impact and report.unknown_impact
    after["objects"].reverse()
    assert ImpactService(project).compare(left, write(right, after)) == report
    assert files(project) == state
    after["objects"].append(dict(after["objects"][0]))
    with pytest.raises(ValueError, match="Invalid bounded application impact"):
        ImpactService(project).compare(left, write(right, after))


def test_alias_application_is_pending_and_invalidates_old_receipt(project, tmp_path):
    original = api_case(project)
    service = DataService(project, auth(project, "plan", "maintain", "review"))
    service.import_inventory(write(tmp_path / "data.json", inventory(project)))
    before = files(project)
    assert service.validate_alias("datasets.health", "local").value["rows"] == [{"query": "owned"}]
    assert files(project) == before
    revised = service.bind_case("datasets.health", original.id, "local")
    assert revised.review_status == "pending"
    assert revised.contract["request"] == original.contract["request"]
    assert revised.contract["expect"] == original.contract["expect"]
    assert revised.contract["data"]["rows"] == [{"query": "owned"}]
    assert case_signature(revised) != case_signature(original)
    with pytest.raises(ValueError, match="Approval binding changed"):
        verify_approval_binding(project, revised)


def test_authorization_precedes_input_and_binding_requires_maintain(project, tmp_path):
    before = files(project)
    with pytest.raises(ValueError, match="Explicit plan"):
        DataService(project).import_inventory(tmp_path / "absent")
    assert files(project) == before
    service = DataService(project, auth(project, "plan", "review"))
    service.import_inventory(write(tmp_path / "data.json", inventory(project)))
    before = files(project)
    with pytest.raises(ValueError, match="Explicit maintain"):
        service.bind_case("datasets.health", "TC-ABSENT", "local")
    assert files(project) == before


@pytest.mark.parametrize(
    "kind,content", [("json", '[{"query":"owned"}]'), ("csv", "query\nowned\n")]
)
def test_file_aliases_pin_authorized_root_and_content(project, tmp_path, kind, content):
    root = tmp_path / "owned-data"
    root.mkdir()
    file = root / ("fixture." + kind)
    file.write_text(content, encoding="utf-8")
    service = DataService(project, auth(project, "plan"))
    source = write(
        tmp_path / "inventory.json", inventory(project, kind=kind, values=[], reference=file.name)
    )
    with pytest.raises(ValueError, match="unauthorized test-data import"):
        service.import_inventory(source)
    imported = service.import_inventory(source, [root])
    assert imported.definitions[0].fingerprint
    assert service.validate_alias("datasets.health", "local").value["rows"] == [{"query": "owned"}]
    file.write_text(content.replace("owned", "changed"), encoding="utf-8")
    with pytest.raises(ValueError, match="stale or unauthorized"):
        service.validate_alias("datasets.health", "local")


def test_identical_files_in_two_roots_are_ambiguous(project, tmp_path):
    roots = [tmp_path / "first", tmp_path / "second"]
    for root in roots:
        root.mkdir()
        (root / "fixture.json").write_text('[{"v":"owned"}]', encoding="utf-8")
    source = write(
        tmp_path / "inventory.json",
        inventory(project, kind="json", values=[], reference="fixture.json"),
    )
    before = files(project)
    with pytest.raises(ValueError, match="unauthorized test-data import"):
        DataService(project, auth(project, "plan")).import_inventory(source, roots)
    assert files(project) == before


def test_credential_alias_never_resolves_secret_and_cannot_store_values(
    project, tmp_path, monkeypatch
):
    service = DataService(project, auth(project, "plan", "maintain", "review"))
    value = inventory(
        project,
        kind="credential",
        values=[],
        sensitivity="SECRET_REFERENCE",
        reference="AUTOQA_SECRET_OWNED",
    )
    monkeypatch.setenv("AUTOQA_SECRET_OWNED", "private-value-never-output")
    service.import_inventory(write(tmp_path / "inventory.json", value))
    validated = service.validate_alias("datasets.health", "local")
    assert validated.value["reference"] == "AUTOQA_SECRET_OWNED"
    assert "private-value-never-output" not in validated.model_dump_json()
    case = api_case(project, {"strategy": "bearer", "token_env": "AUTOQA_SECRET_PREVIOUS"})
    revised = service.bind_case("datasets.health", case.id, "local")
    assert revised.contract["authentication"]["token_env"] == "AUTOQA_SECRET_OWNED"
    assert revised.review_status == "pending"
    value["definitions"][0]["values"] = [{"token": "must-not-store"}]
    with pytest.raises(ValueError):
        service.inspect(write(tmp_path / "inventory.json", value))


@pytest.mark.parametrize(
    "reference",
    ["../private.json", "/private.json", "https://owned.test/data.json", "C:\\private.json"],
)
def test_unsafe_references_fail_generically(project, tmp_path, reference):
    source = write(
        tmp_path / "inventory.json", inventory(project, kind="json", values=[], reference=reference)
    )
    with pytest.raises(ValueError) as error:
        DataService(project, auth(project, "plan")).import_inventory(source, [tmp_path])
    assert str(error.value) == "Invalid or unauthorized test-data import"


def test_tampered_inventory_fails_current_binding(project, tmp_path):
    service = DataService(project, auth(project, "plan"))
    service.import_inventory(write(tmp_path / "inventory.json", inventory(project)))
    value = project.storage.read_json(INVENTORY)
    value["definitions"][0]["values"] = [{"query": "changed"}]
    project.storage.write_json(INVENTORY, value)
    with pytest.raises(ValueError):
        service.validate_alias("datasets.health", "local")
    assert project.storage.path(BINDINGS).is_file()


def test_legacy_historical_case_snapshot_and_embedded_steps_are_supported(project, tmp_path):
    case = api_case(project)
    value = recorded(case)
    del value["diagnostic_snapshot"]
    value["case_snapshot"] = [case.model_dump()]
    value["step_results"] = value.pop("steps")
    for step in value["step_results"]:
        del step["run_id"]
        del step["kind"]
    report = DiagnosisService(project).analyze(write(tmp_path / "run.json", value))
    assert report.findings[0].category == "ASSERTION_MISMATCH"
    assert not report.findings[0].missing_evidence


def test_missing_selected_case_is_explicitly_incomplete(project, tmp_path):
    value = recorded(api_case(project))
    value["selected_case_ids"].append("TC-MISSING")
    findings = DiagnosisService(project).analyze(write(tmp_path / "run.json", value)).findings
    assert any(f.category == "EVIDENCE_INTEGRITY_FAILURE" and f.case_id is None for f in findings)


@pytest.mark.parametrize(
    "symptom,expected",
    [
        ("strict mode violation", "LOCATOR_AMBIGUITY"),
        ("waiting for locator", "LOCATOR_MISSING"),
        ("request timed out", "TIMEOUT_SYMPTOM"),
        ("missing credential reference", "AUTH_FAILURE"),
        ("fixture data missing", "TEST_DATA_FAILURE"),
        ("ModuleNotFoundError", "ENVIRONMENT_FAILURE"),
    ],
)
def test_diagnostic_symptoms_are_hypotheses_not_confirmed_causes(
    project, tmp_path, symptom, expected
):
    value = recorded(api_case(project))
    value["records"][0]["error"] = symptom
    report = DiagnosisService(project).analyze(write(tmp_path / "run.json", value))
    assert report.findings[0].category == expected
    assert not report.findings[0].root_cause_confirmed
    assert report.findings[0].hypotheses[0].confidence == "POSSIBLE"


def test_duplicate_json_and_oversized_source_fail_before_any_mutation(project, tmp_path):
    source = tmp_path / "inventory.json"
    source.write_text('{"project_id":"first","project_id":"second"}', encoding="utf-8")
    before = files(project)
    with pytest.raises(ValueError):
        DataService(project).inspect(source)
    source.write_bytes(b" " * 1_000_001)
    with pytest.raises(ValueError):
        DataService(project).inspect(source)
    assert files(project) == before


def test_file_alias_link_rejected(project, tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    real = outside / "real.json"
    real.write_text('[{"v":"owned"}]', encoding="utf-8")
    link = root / "linked"
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, check=True
        )
    else:
        link.symlink_to(outside, target_is_directory=True)
    source = write(
        tmp_path / "inventory.json",
        inventory(project, kind="json", values=[], reference="linked/real.json"),
    )
    with pytest.raises(ValueError):
        DataService(project, auth(project, "plan")).import_inventory(source, [root])


def test_equivalent_inventory_order_is_stable_and_row_order_is_meaningful(project, tmp_path):
    value = inventory(project)
    value["definitions"][0]["environments"] = ["other", "local"]
    value["definitions"][0]["values"] = [{"query": "first"}, {"query": "second"}]
    service = DataService(project, auth(project, "plan"))
    source = write(tmp_path / "inventory.json", value)
    first = service.import_inventory(source)
    first_identity = service.validate_alias("datasets.health", "local").digest
    value["definitions"][0]["environments"].reverse()
    assert service.import_inventory(write(source, value)) == first
    assert service.validate_alias("datasets.health", "local").digest == first_identity
    value["definitions"][0]["values"].reverse()
    service.import_inventory(write(source, value))
    assert service.validate_alias("datasets.health", "local").digest != first_identity
