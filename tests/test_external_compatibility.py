"""V0.2.1 targeted tests: no external connections or external permissions."""

import json
import socket
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from playwright.sync_api import Error, sync_playwright
from pydantic import ValidationError

from autoqa.authorization import AuthorizationContext
from autoqa.core import APIResourceRule, Config
from autoqa.exploration import explore
from autoqa.readiness import observe_readiness
from autoqa.security import Scope


def rule(origin="https://api.example.test", path="/catalog", **kwargs):
    return APIResourceRule(
        origin=origin,
        path=path,
        enabled=True,
        approval_reference="Controlled local test approval",
        **kwargs,
    )


def request(
    url="https://api.example.test/catalog",
    method="GET",
    navigation=False,
    resource_type="fetch",
    headers=None,
    body=None,
):
    return SimpleNamespace(
        url=url,
        method=method,
        resource_type=resource_type,
        post_data=body,
        is_navigation_request=lambda: navigation,
        all_headers=lambda: headers or {},
    )


@pytest.fixture
def public_dns(monkeypatch):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *args, **kw: [(socket.AF_INET, 1, 6, "", ("8.8.8.8", 443))]
    )


def test_default_empty_and_disabled_rules_do_not_grant_resources(public_dns):
    config = Config(name="test", api_resources=[rule().model_copy(update={"enabled": False})])
    scope = Scope("https://app.example.test/", config)
    assert not scope.request_decision(request())[0]
    assert not scope.api_scopes
    assert scope.request_decision(
        request("https://app.example.test/style.css", resource_type="stylesheet")
    )[0]


def test_proposal_is_valid_disabled_and_not_applied(public_dns):
    root = Path(__file__).resolve().parents[1]
    proposal = yaml.safe_load(
        (root / "docs/v021-api-allowlist.proposed.yaml").read_text(encoding="utf-8")
    )
    config = Config(name="review-only", **proposal)
    assert len(config.api_resources) == 4
    assert all(not r.enabled and r.methods == ["GET"] and not r.query for r in config.api_resources)
    scope = Scope("https://app.example.test/", config)
    assert not scope.api_scopes


def test_approved_exact_api_resource_never_grants_navigation(public_dns):
    scope = Scope(
        "https://app.example.test/",
        Config(name="test", allowed_domains=["app.example.test"], api_resources=[rule()]),
    )
    assert scope.request_decision(request()) == (True, "approved_api_resource")
    assert not scope.request_decision(request(navigation=True))[0]
    assert not scope.allows("https://api.example.test/catalog")
    assert "api.example.test" in scope.chromium_args[0]
    assert scope.config.allowed_domains == ["app.example.test"]


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "QUERY", "TRACE"])
def test_write_and_unreviewed_methods_stay_blocked(public_dns, method):
    scope = Scope("https://app.example.test/", Config(name="test", api_resources=[rule()]))
    assert scope.request_decision(request(method=method)) == (False, "method_not_read_only")


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.test/catalog/1",
        "https://api.example.test/catalogue",
        "https://api.example.test/%63atalog",
        "https://api.example.test/catalog?token=sensitive",
        "https://api.example.test:444/catalog",
        "https://api.example.test:0/catalog",
        "http://api.example.test/catalog",
        "https://elsewhere.example.test/catalog",
    ],
)
def test_near_matches_do_not_expand_the_allowlist(public_dns, url):
    scope = Scope("https://app.example.test/", Config(name="test", api_resources=[rule()]))
    assert not scope.request_decision(request(url))[0]


def test_query_values_are_exact_bounded_and_optional(public_dns):
    scope = Scope(
        "https://app.example.test/",
        Config(name="test", api_resources=[rule(query={"page": ["1"]})]),
    )
    assert scope.request_decision(request("https://api.example.test/catalog?page=1"))[0]
    for query in ("page=2", "page=1&page=1", "page=1&sort=price", "page=", "unknown=1"):
        assert not scope.request_decision(request("https://api.example.test/catalog?" + query))[0]
    assert not scope.request_decision(request("https://app.example.test/?page=1"))[0]


@pytest.mark.parametrize(
    "headers",
    [{"Authorization": "Bearer private"}, {"Cookie": "private"}, {"X-API-Key": "private"}],
)
def test_api_credentials_are_never_allowed(public_dns, headers):
    scope = Scope("https://app.example.test/", Config(name="test", api_resources=[rule()]))
    assert (
        scope.request_decision(request(headers=headers))[1]
        == "api_authentication_headers_forbidden"
    )


def test_body_resource_type_sensitive_paths_and_budget(public_dns):
    scope = Scope(
        "https://app.example.test/",
        Config(name="test", api_resources=[rule(), rule(path="/auth/login")]),
    )
    assert not scope.request_decision(request(body="{}"))[0]
    assert not scope.request_decision(request(resource_type="script"))[0]
    assert not scope.request_decision(request("https://api.example.test/auth/login"))[0]
    scope.request_count = scope.config.max_requests
    assert scope.request_decision(request())[1] == "request_budget_exhausted"


def test_private_api_dns_and_rebinding_are_rejected(monkeypatch):
    def dns(host, *args, **kwargs):
        return [
            (
                socket.AF_INET,
                1,
                6,
                "",
                ("10.0.0.1" if host == "api.example.test" else "8.8.8.8", 443),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", dns)
    with pytest.raises(ValueError, match="Non-public"):
        Scope("https://app.example.test/", Config(name="test", api_resources=[rule()]))
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *a, **kw: [(socket.AF_INET, 1, 6, "", ("8.8.8.8", 443))]
    )
    scope = Scope("https://app.example.test/", Config(name="test", api_resources=[rule()]))
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    assert not scope.request_decision(request())[0]


@pytest.mark.parametrize(
    "overrides",
    [
        {"origin": "https://*.example.test"},
        {"path": "/catalog/*"},
        {"methods": ["QUERY"]},
        {"query": {"token": ["x"]}},
        {"query": {"q": ["*"]}},
    ],
)
def test_rule_schema_rejects_wildcards_sensitive_queries_and_methods(overrides):
    data = {
        "origin": "https://api.example.test",
        "path": "/catalog",
        "methods": ["GET"],
        "approval_reference": "Human review required",
        **overrides,
    }
    with pytest.raises(ValidationError):
        APIResourceRule.model_validate(data)


def test_specific_audit_paths_and_reasons_never_store_values(public_dns):
    scope = Scope("https://app.example.test/", Config(name="test"))
    req = request("https://api.example.test/catalog?page=1&token=secret")
    allowed, reason = scope.request_decision(req)
    assert not allowed
    scope._record_block(req.url, req.method, reason)
    event = scope.blocked_requests[0]
    assert event["path"] == "/catalog" and "resource_policy:" in event["reason"]
    assert "secret" not in json.dumps(event)
    assert (
        Scope._audit_url("https://user:secret@api.example.test:8443/auth/private")["path"]
        == "[redacted-sensitive-path]"
    )


@pytest.fixture
def local_resources():
    hits = Counter()

    class API(BaseHTTPRequestHandler):
        def do_GET(self):
            hits[self.path] += 1
            if self.path.startswith("/redirect"):
                self.send_response(302)
                self.send_header(
                    "Location", "/catalog" if self.path.endswith("allowed") else "/admin"
                )
                self.end_headers()
                return
            payload = b'{"items":["Controlled item"]}'
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    class App(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/nav-redirect":
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{api.server_port}/catalog")
                self.end_headers()
                return
            if self.path == "/delayed":
                content = '<main aria-busy="true"><h1>Loading</h1></main><script>setTimeout(()=>{document.querySelector("main").removeAttribute("aria-busy");document.querySelector("h1").textContent="Loaded content"},80)</script>'
            elif self.path == "/busy":
                content = '<main aria-busy="true"><h1>Still loading</h1></main>'
            elif self.path == "/shell":
                content = "<nav><button>Menu</button></nav>"
            elif self.path == "/status":
                content = '<main><p role="alert">Content unavailable</p></main>'
            else:
                content = "<main><h1>Local application</h1></main>"
            body = ("<!doctype html><html><body>" + content + "</body></html>").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    api = ThreadingHTTPServer(("127.0.0.1", 0), API)
    app = ThreadingHTTPServer(("127.0.0.1", 0), App)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (app, api)]
    for t in threads:
        t.start()
    try:
        yield f"http://127.0.0.1:{app.server_port}", f"http://127.0.0.1:{api.server_port}", hits
    finally:
        for s in (app, api):
            s.shutdown()
            s.server_close()
        for t in threads:
            t.join(timeout=2)


@pytest.mark.browser
def test_local_api_only_approved_resources_and_redirects(local_resources):
    app, api, hits = local_resources
    scope = Scope(
        app,
        Config(
            name="test",
            allow_localhost=True,
            request_interval_ms=0,
            api_resources=[
                rule(api),
                rule(api, "/redirect-denied"),
                rule(api, "/redirect-allowed"),
            ],
        ),
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=scope.chromium_args)
        try:
            context = browser.new_context(service_workers="block")
            context.route("**/*", scope.guard)
            page = context.new_page()
            page.goto(app)
            fetch = """async url => {try {const response=await fetch(url);return await response.json();}catch{return 'blocked';}}"""
            assert page.evaluate(fetch, api + "/catalog") == {"items": ["Controlled item"]}
            assert page.evaluate(fetch, api + "/unknown") == "blocked"
            assert page.evaluate(fetch, api + "/redirect-denied") == "blocked"
            assert page.evaluate(fetch, api + "/redirect-allowed") == "blocked"
            assert hits["/unknown"] == hits["/admin"] == 0
            assert hits["/catalog"] == 1  # The approved redirect target was not followed either.
            with pytest.raises(Error):
                page.goto(api + "/catalog")
            assert hits["/catalog"] == 1
            with pytest.raises(Error):
                page.goto(app + "/nav-redirect")
            assert hits["/catalog"] == 1
            assert any(
                e["reason"] == "redirect_blocked_before_follow"
                and e["redirect_path"] == "[redacted-sensitive-path]"
                for e in scope.blocked_requests
            )
            assert any(
                e["reason"] == "redirect_blocked_before_follow" and e["redirect_path"] == "/catalog"
                for e in scope.blocked_requests
            )
        finally:
            browser.close()


@pytest.mark.browser
@pytest.mark.parametrize(
    "path,status",
    [
        ("/delayed", "CONTENT_STABLE"),
        ("/busy", "TIMEOUT"),
        ("/shell", "TIMEOUT"),
        ("/status", "STATUS_STABLE"),
    ],
)
def test_bounded_observable_readiness(local_resources, path, status):
    app, _, _ = local_resources
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(app + path, wait_until="domcontentloaded")
            result = observe_readiness(page, timeout_ms=400, quiet_window_ms=50)
            assert result["status"] == status
            assert result["application_completeness"] == "UNVERIFIED"
            assert result["timeout_ms"] == 400
            if path == "/delayed":
                assert page.get_by_role("heading", name="Loaded content").count() == 1
        finally:
            browser.close()


@pytest.mark.browser
def test_exploration_persists_readiness_without_fixed_delay(project, local_resources):
    app, _, _ = local_resources
    project.config.allow_localhost = True
    project.config.max_pages = 1
    project.config.request_interval_ms = 0
    project.config.spa_quiet_window_ms = 50
    discovery = explore(
        project,
        app + "/delayed",
        authorization=AuthorizationContext(project.root, frozenset({"discover"})),
    )
    assert discovery.pages[0].headings == ["Loaded content"]
    assert discovery.pages[0].readiness["status"] == "CONTENT_STABLE"
    assert not discovery.errors
