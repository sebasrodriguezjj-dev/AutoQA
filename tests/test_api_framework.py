"""Owned-loopback API acceptance; no external target or real client credential."""

import base64
import json
import os
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest
from typer.testing import CliRunner

from autoqa.api_service import plan_api
from autoqa.application import ApplicationEngine
from autoqa.authorization import AuthorizationContext
from autoqa.cli import app
from autoqa.framework_runtime.api import APIExecutionError, APIService, endpoint
from autoqa.framework_runtime.contracts import APIScenario
from autoqa.framework_runtime.evidence import StepRecorder
from autoqa.framework_runtime.integrity import validate
from autoqa.planning import approve


@pytest.fixture
def api_server():
    class Handler(BaseHTTPRequestHandler):
        broken = False
        hits = []

        def log_message(self, *args):
            pass

        def do_GET(self):
            self.hits.append((self.command, self.path))
            path = urlsplit(self.path).path
            if path == "/ui":
                healthy = self.headers.get("Cookie") == "session=synthetic-cookie"
                self.send_response(200 if healthy else 401)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h1>Authorized synthetic UI</h1>" if healthy else b"<h1>Missing session</h1>"
                )
                return
            if path == "/slow":
                time.sleep(0.3)
            if path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:1/private")
                self.end_headers()
                return
            if path == "/large":
                self.send_response(200)
                self.end_headers()
                try:
                    self.wfile.write(b"x" * 1_048_577)
                except BrokenPipeError, ConnectionResetError, ConnectionAbortedError:
                    pass
                return
            expected = {
                "/bearer": "Bearer synthetic-credential",
                "/basic": "Basic " + base64.b64encode(b"synthetic:fixture-password").decode(),
                "/cookie": "session=synthetic-cookie",
            }
            authorized = (
                path not in expected
                or self.headers.get("Cookie" if path == "/cookie" else "Authorization")
                == expected[path]
            )
            status = 401 if not authorized else 404 if path == "/missing" else 200
            body = json.dumps(
                {
                    "healthy": not self.broken,
                    "method": self.command,
                    "query": parse_qs(urlsplit(self.path).query),
                    "data": json.loads(
                        self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"null"
                    ),
                    "token": "synthetic-response-sensitive",
                }
            ).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Contract", "fixture")
            self.send_header("Set-Cookie", "session=synthetic-response-sensitive")
            self.end_headers()
            try:
                self.wfile.write(body)
            except BrokenPipeError, ConnectionResetError, ConnectionAbortedError:
                pass

        do_POST = do_PUT = do_PATCH = do_DELETE = do_GET

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", Handler
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def spec(origin, **updates):
    return APIScenario.model_validate(
        dict(
            id="TC-API",
            title="Owned API contract",
            request={"path": "/health"},
            expect={
                "status": 200,
                "headers": {"x-contract": "fixture"},
                "json_values": {"healthy": True},
                "json_types": {"": "object", "healthy": "boolean"},
            },
            environments=[{"name": "local", "origin": origin, "allow_localhost": True}],
            environment="local",
        )
        | updates
    )


def service(tmp_path, name="TC-API"):
    tmp_path.mkdir(parents=True, exist_ok=True)
    recorder = StepRecorder(None, tmp_path, name, "owned-run", "disabled")
    return APIService(recorder)


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_methods_query_json_assertions_and_safe_evidence(api_server, tmp_path, method):
    origin, handler = api_server
    request = {
        "method": method,
        "path": "/health",
        "query": {"q": "${name}"},
        "headers": {"X-Reviewed": "fixture"},
    }
    if method != "GET":
        request |= {
            "mutation_review": "Owned synthetic API mutation reviewed; expect exact echo",
            "json_body": {"name": "${name}", "id": "${synthetic_id}"},
        }
    scenario = spec(
        origin,
        request=request,
        data={
            "name": "people",
            "seed": 42,
            "rows": [{"name": "Synthetic A"}, {"name": "Synthetic B"}],
        },
        expect={
            "status": 200,
            "json_values": {"query.q.0": "${name}", "method": method},
            "json_types": {"healthy": "boolean", "data": "null" if method == "GET" else "object"},
        },
    )
    for i in range(2):
        client = service(tmp_path / str(i))
        client.execute(scenario.model_dump(), i)
        assert [r["status"] for r in client.evidence.records] == ["PASSED", "PASSED"]
        assert client.evidence.records[0]["api"]["masked_headers"]["authorization"] == "[REDACTED]"
        evidence = next((tmp_path / str(i)).glob("*-steps.json")).read_text()
        assert "synthetic-response-sensitive" not in evidence and "Synthetic A" not in evidence
    assert len(handler.hits) == 2


@pytest.mark.parametrize(
    "strategy,path,values",
    [
        ("bearer", "/bearer", {"AUTOQA_SECRET_TOKEN": "synthetic-credential"}),
        (
            "basic",
            "/basic",
            {"AUTOQA_SECRET_USER": "synthetic", "AUTOQA_SECRET_PASSWORD": "fixture-password"},
        ),
        ("cookie", "/cookie", {"AUTOQA_SECRET_COOKIE": "synthetic-cookie"}),
    ],
)
def test_missing_and_valid_authentication(
    api_server, tmp_path, monkeypatch, strategy, path, values
):
    auth = {"strategy": strategy}
    if strategy == "basic":
        auth |= {"username_env": "AUTOQA_SECRET_USER", "password_env": "AUTOQA_SECRET_PASSWORD"}
    else:
        auth["token_env"] = next(iter(values))
    if strategy == "cookie":
        auth["cookie_name"] = "session"
    for key in values:
        monkeypatch.delenv(key, raising=False)
    s = spec(api_server[0], request={"path": path}, authentication=auth)
    with pytest.raises(APIExecutionError, match="missing"):
        service(tmp_path / "missing").execute(s.model_dump())
    assert not api_server[1].hits
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    client = service(tmp_path / "valid")
    client.execute(s.model_dump())
    assert client.evidence.records[0]["api"]["status"] == "PASSED"
    serialized = next((tmp_path / "valid").glob("*-steps.json")).read_text()
    assert all(value not in serialized for value in values.values())


def test_negative_failure_redirect_timeout_and_environment(api_server, tmp_path, monkeypatch):
    origin, handler = api_server
    service(tmp_path / "negative").execute(
        spec(
            origin, polarity="negative", request={"path": "/missing"}, expect={"status": 404}
        ).model_dump()
    )
    with pytest.raises(APIExecutionError, match="status assertion"):
        service(tmp_path / "failure").execute(spec(origin, expect={"status": 201}).model_dump())
    with pytest.raises(APIExecutionError, match="redirect"):
        service(tmp_path / "redirect").execute(
            spec(origin, request={"path": "/redirect"}).model_dump()
        )
    assert all("private" not in path for _, path in handler.hits)
    with pytest.raises(APIExecutionError):
        service(tmp_path / "timeout").execute(
            spec(origin, request={"path": "/slow", "timeout_seconds": 0.1}).model_dump()
        )
    with pytest.raises(APIExecutionError, match="bounded size"):
        service(tmp_path / "large").execute(spec(origin, request={"path": "/large"}).model_dump())
    monkeypatch.setenv("AUTOQA_ENVIRONMENT", "unreviewed")
    count = len(handler.hits)
    with pytest.raises(APIExecutionError, match="Environment"):
        service(tmp_path / "environment").execute(spec(origin).model_dump())
    assert len(handler.hits) == count


def test_dns_boundary_and_pinning(api_server, tmp_path, monkeypatch):
    from autoqa.framework_runtime.contracts import Environment

    with pytest.raises(APIExecutionError, match="network boundary"):
        endpoint(Environment(name="denied", origin="http://127.0.0.1:8000"))
    real = socket.getaddrinfo
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 80))],
    )
    with pytest.raises(APIExecutionError, match="network boundary"):
        endpoint(Environment(name="denied", origin="https://owned.example"))
    calls = []

    def resolve(host, *args, **kwargs):
        if host == "localhost":
            calls.append(host)
            assert len(calls) == 1, "Hostname must not be resolved again during connection"
            return real("127.0.0.1", *args, **kwargs)
        return real(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    service(tmp_path).execute(spec(api_server[0].replace("127.0.0.1", "localhost")).model_dump())
    assert calls == ["localhost"]


@pytest.mark.parametrize(
    "expect",
    [
        {"status": 200, "headers": {"X-Contract": "wrong"}},
        {"status": 200, "json_values": {"healthy": False}},
        {"status": 200, "json_types": {"healthy": "integer"}},
        {"status": 200, "json_values": {"absent.key": 1}},
    ],
)
def test_each_response_assertion_fails_without_payload_leak(api_server, tmp_path, expect):
    client = service(tmp_path)
    with pytest.raises(APIExecutionError) as caught:
        client.execute(spec(api_server[0], expect=expect).model_dump())
    assert "synthetic-response-sensitive" not in str(caught.value)
    assert client.evidence.records[-1]["status"] == "FAILED"


def test_review_environment_selection_and_no_base_override(api_server, tmp_path, monkeypatch):
    s = spec(
        api_server[0],
        environments=[
            {"name": "local", "origin": api_server[0], "allow_localhost": True},
            {
                "name": "second",
                "origin": api_server[0],
                "allow_localhost": True,
                "values": {"label": "synthetic"},
            },
        ],
    )
    monkeypatch.setenv("AUTOQA_ENVIRONMENT", "second")
    monkeypatch.setenv("AUTOQA_BASE_URL", "http://127.0.0.1:1/unauthorized")
    service(tmp_path).execute(s.model_dump())
    assert len(api_server[1].hits) == 1


def prepare(project, path, values):
    path.write_text(json.dumps([s.model_dump() for s in values]))
    ctx = AuthorizationContext(project.root, frozenset({"plan", "review", "generate", "execute"}))
    plan_api(project, path, ctx)
    approve(project, [s.id for s in values], authorization=ctx)
    return ctx


def test_api_export_requires_receipts_and_rejects_privacy_tamper(project, tmp_path):
    from autoqa.planning import reject

    s = spec("http://127.0.0.1:8000")
    source = tmp_path / "api.json"
    ctx = prepare(project, source, [s])
    reject(project, [s.id], authorization=ctx)
    with pytest.raises(ValueError, match="No approved"):
        ApplicationEngine(project, ctx).build_framework(tmp_path / "rejected")
    approve(project, [s.id], authorization=ctx)
    receipts = project.storage.read_json("test-cases/approval-receipts.json")
    project.storage.write_json("test-cases/approval-receipts.json", {})
    with pytest.raises(ValueError, match="reapproval"):
        ApplicationEngine(project, ctx).build_framework(tmp_path / "unbound")
    project.storage.write_json("test-cases/approval-receipts.json", receipts)
    export = tmp_path / "safe"
    ApplicationEngine(project, ctx).build_framework(export)
    manifest_path = export / "framework.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["privacy"] = "raw"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="privacy"):
        validate(export)
    changed = s.model_copy(update={"expect": s.expect.model_copy(update={"status": 201})})
    source.write_text(json.dumps([changed.model_dump()]))
    assert plan_api(project, source, ctx)[0].review_status == "pending"


def test_standalone_api_healthy_defect_restore(project, api_server, tmp_path, monkeypatch):
    origin, handler = api_server
    s = spec(
        origin,
        request={"path": "/bearer"},
        authentication={"strategy": "bearer", "token_env": "AUTOQA_SECRET_TOKEN"},
        data={"name": "examples", "rows": [{"label": "one"}, {"label": "two"}]},
        evidence={"sensitive_fields": ["token"]},
    )
    ctx = prepare(project, tmp_path / "api.json", [s])
    export = tmp_path / "standalone"
    result = ApplicationEngine(project, ctx).build_framework(export)
    assert result["cases"] == [s.id]
    manifest = validate(export)
    assert manifest["privacy"] == "summary_only"
    assert manifest["parameters"] == {s.id: 2}
    assert CliRunner().invoke(app, ["plan-api", "--help"]).exit_code == 0
    # A real independent environment, using only declared runtime dependencies.
    uv = ["uv", "sync"]
    installed = subprocess.run(uv, cwd=export, capture_output=True, text=True, timeout=120)
    assert installed.returncode == 0, installed.stdout + installed.stderr
    python = export / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    isolation = subprocess.run(
        [
            str(python),
            "-c",
            "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
        ],
        cwd=export,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert isolation.returncode == 0, isolation.stderr
    env = dict(os.environ, AUTOQA_SECRET_TOKEN="synthetic-credential")
    env.pop("PYTHONPATH", None)
    collected = subprocess.run(
        [str(python), "-m", "qa_runtime.runner", "collect"],
        cwd=export,
        env=env,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert collected.returncode == 0, collected.stdout + collected.stderr
    observed = []
    for broken in (False, True, False):
        handler.broken = broken
        run = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", "run"],
            cwd=export,
            env=env,
            capture_output=True,
            text=True,
            timeout=40,
        )
        outputs = sorted(
            (export / "artifacts").glob("*/results.json"), key=lambda p: p.stat().st_mtime_ns
        )
        result = json.loads(outputs[-1].read_text())
        assert run.returncode == (1 if broken else 0), run.stdout + run.stderr
        assert result["counts"] == ({"FAILED": 2} if broken else {"PASSED": 2})
        assert len(result["steps"]) == 4
        assert all(s["run_id"] == result["run_id"] for s in result["steps"])
        assert all(s["evidence"] == [] for s in result["steps"])
        observed.append(result["counts"])
    assert observed == [{"PASSED": 2}, {"FAILED": 2}, {"PASSED": 2}]
    del env["AUTOQA_SECRET_TOKEN"]
    run = subprocess.run(
        [str(python), "-m", "qa_runtime.runner", "run"],
        cwd=export,
        env=env,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert run.returncode == 1
    for path in (export / "artifacts").rglob("*"):
        if path.is_file():
            raw = path.read_text(encoding="utf-8")
            assert "synthetic-credential" not in raw and "synthetic-response-sensitive" not in raw
    assert not list((export / "artifacts").rglob("*.png"))
    assert not list((export / "artifacts").rglob("*.zip"))


@pytest.mark.browser
def test_combined_cookie_ui_api_independent(project, api_server, tmp_path):
    from autoqa.core import Discovery, PageEvidence
    from autoqa.planning import plan

    origin, _ = api_server
    project.config.application_url = origin + "/ui"
    project.config.allowed_domains = ["127.0.0.1"]
    project.config.allow_localhost = True
    project.config.auth_reference = "cookie:AUTOQA_SECRET_COOKIE:session"
    project.save_config()
    project.storage.write_json(
        "discovery/workflow-map.json",
        Discovery(
            pages=[
                PageEvidence(
                    url=origin + "/ui",
                    title="Owned UI",
                    headings=["Authorized synthetic UI"],
                    elements=[],
                    screenshot="screenshots/synthetic.png",
                    depth=0,
                )
            ]
        ).model_dump(),
    )
    ctx = AuthorizationContext(project.root, frozenset({"plan", "review", "generate", "execute"}))
    ui = plan(project, authorization=ctx)
    approve(project, [ui[0].id], authorization=ctx)
    prepare(project, tmp_path / "api.json", [spec(origin)])
    export = tmp_path / "combined"
    ApplicationEngine(project, ctx).build_framework(export)
    manifest = validate(export)
    assert len(manifest["cases"]) == 2
    assert list((export / "pages").glob("page_*.py"))
    assert (export / "services/api_service.py").is_file()
    setup = subprocess.run(["uv", "sync"], cwd=export, capture_output=True, text=True, timeout=120)
    assert setup.returncode == 0, setup.stdout + setup.stderr
    python = export / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    clean = dict(os.environ, AUTOQA_SECRET_COOKIE="synthetic-cookie")
    clean.pop("PYTHONPATH", None)
    check = subprocess.run(
        [
            str(python),
            "-c",
            "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
        ],
        cwd=export,
        env=clean,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert check.returncode == 0, check.stderr
    for missing in (False, True):
        env = dict(clean)
        if missing:
            env.pop("AUTOQA_SECRET_COOKIE")
        process = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", "run"],
            cwd=export,
            env=env,
            capture_output=True,
            text=True,
            timeout=50,
        )
        latest = max(
            (export / "artifacts").glob("*/results.json"), key=lambda p: p.stat().st_mtime_ns
        )
        result = json.loads(latest.read_text())
        assert process.returncode == (1 if missing else 0), process.stdout + process.stderr
        assert result["counts"] == ({"PASSED": 1, "ERROR": 1} if missing else {"PASSED": 2})
    for path in (export / "artifacts").rglob("*"):
        if path.is_file():
            assert "synthetic-cookie" not in path.read_text(encoding="utf-8")
    assert not list((export / "artifacts").rglob("*.png"))
    assert not list((export / "artifacts").rglob("*.zip"))
