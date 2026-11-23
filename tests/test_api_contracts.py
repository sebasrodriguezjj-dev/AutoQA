"""Versioned API contracts and exact existing approval receipts."""

import json

import pytest

from autoqa.api_service import plan_api
from autoqa.authorization import AuthorizationContext
from autoqa.framework_runtime.contracts import APIScenario, Authentication, DataFixture
from autoqa.planning import approve, case_signature, verify_approval_binding


def scenario(origin="http://127.0.0.1:8000", **updates):
    value = dict(
        id="TC-API",
        title="Health",
        request={"path": "/health"},
        expect={"status": 200},
        environments=[{"name": "local", "origin": origin, "allow_localhost": True}],
        environment="local",
    )
    return APIScenario.model_validate(value | updates)


@pytest.mark.parametrize(
    "request_spec",
    [
        {"path": "//evil"},
        {"path": "/../evil"},
        {"path": "/x%2fy"},
        {"path": "/health", "method": "POST"},
        {"path": "/health", "headers": {"Authorization": "secret"}},
        {"path": "/health", "headers": {"Host": "evil"}},
        {"path": "/health", "json_body": {"password": "secret"}},
        {"path": "/health", "query": {"token": "secret"}},
        {"path": "/health", "timeout_seconds": 100},
    ],
)
def test_contract_rejects_unsafe_requests(request_spec):
    with pytest.raises(ValueError):
        scenario(request=request_spec)


@pytest.mark.parametrize(
    "origin",
    ["http://user:secret@localhost", "http://*.test", "file:///local", "http://localhost/path"],
)
def test_contract_rejects_unsafe_origin(origin):
    with pytest.raises(ValueError):
        scenario(origin)


def test_data_and_auth_references():
    s = scenario(
        data={"name": "customers", "seed": 42, "rows": [{"name": "Synthetic"}, {"name": "Second"}]}
    )
    first = s.data.materialize(0, s.environments[0])
    assert first == s.data.materialize(0, s.environments[0])
    assert first != s.data.materialize(1, s.environments[0])
    first["name"] = "Changed"
    assert s.data.rows[0]["name"] == "Synthetic"
    with pytest.raises(ValueError):
        DataFixture(name="bad", rows=[{"secret": "raw"}])
    with pytest.raises(ValueError):
        Authentication(strategy="bearer", token_env="actual-token")
    with pytest.raises(ValueError):
        scenario(request={"path": "/health", "query": {"q": "${missing}"}})


def test_api_plan_receipts_and_invalidation(project, tmp_path):
    path = tmp_path / "requirements.json"
    path.write_text(json.dumps([scenario().model_dump()]))
    context = AuthorizationContext(project.root, frozenset({"plan", "review"}))
    with pytest.raises(ValueError, match="Explicit plan"):
        plan_api(project, path, None)
    cases = plan_api(project, path, context)
    assert cases[0].review_status == "pending"
    approve(project, [cases[0].id], authorization=context)
    original = project.cases()[0]
    verify_approval_binding(project, original)
    assert plan_api(project, path, context)[0].review_status == "approved"
    changed = scenario(expect={"status": 201})
    path.write_text(json.dumps([changed.model_dump()]))
    new = plan_api(project, path, context)[0]
    assert new.review_status == "pending"
    assert case_signature(new) != case_signature(original)
    with pytest.raises(ValueError, match="changed"):
        verify_approval_binding(project, new)


def test_ui_replan_preserves_api_and_contract_fields_bind_approval(project, tmp_path):
    from autoqa.core import Discovery
    from autoqa.planning import plan

    path = tmp_path / "api.json"
    path.write_text(json.dumps([scenario().model_dump()]))
    ctx = AuthorizationContext(project.root, frozenset({"plan", "review"}))
    api = plan_api(project, path, ctx)[0]
    approve(project, [api.id], authorization=ctx)
    project.storage.write_json("discovery/workflow-map.json", Discovery().model_dump())
    assert plan(project, authorization=ctx)[0].kind == "api"
    assert project.cases()[0].review_status == "approved"
    base = project.cases()[0]
    for key, value in [
        (
            "environments",
            [{"name": "local", "origin": "http://127.0.0.1:8001", "allow_localhost": True}],
        ),
        ("data", {"name": "changed", "rows": [{"x": 1}]}),
        ("authentication", {"strategy": "bearer", "token_env": "AUTOQA_SECRET_NEW"}),
    ]:
        changed = base.model_copy(update={"contract": base.contract | {key: value}})
        assert case_signature(changed) != case_signature(base)
        with pytest.raises(ValueError, match="changed"):
            verify_approval_binding(project, changed)


def test_transient_evidence_replace_does_not_lose_results(tmp_path, monkeypatch):
    from pathlib import Path

    from autoqa.framework_runtime.evidence import StepRecorder

    real = Path.replace
    calls = []

    def transient(path, destination):
        calls.append(path)
        if len(calls) < 3:
            raise PermissionError("controlled transient sharing violation")
        return real(path, destination)

    recorder = StepRecorder(None, tmp_path, "TC-PERSIST", "owned-run", "disabled")
    monkeypatch.setattr(Path, "replace", transient)
    recorder.persist()
    assert len(calls) == 3
    assert json.loads((tmp_path / "TC-PERSIST-steps.json").read_text()) == []


def test_persistent_evidence_error_is_not_success(tmp_path, monkeypatch):
    from pathlib import Path

    from autoqa.framework_runtime.evidence import StepRecorder

    def denied(*args):
        raise PermissionError("controlled permanent denial")

    monkeypatch.setattr(Path, "replace", denied)
    with pytest.raises(PermissionError):
        StepRecorder(None, tmp_path, "TC-PERSIST", "owned-run", "disabled").persist()


def test_nested_json_boolean_is_not_an_integer():
    from autoqa.framework_runtime.api import APIExecutionError, check_response
    from autoqa.framework_runtime.contracts import ResponseAssertions

    expected = ResponseAssertions(status=200, json_values={"value": {"nested": 1}})
    with pytest.raises(APIExecutionError, match="JSON value"):
        check_response(expected, 200, {}, b'{"value":{"nested":true}}', {})
