import ast
import json
from pathlib import Path

import pytest
from playwright.sync_api import Error, sync_playwright

from autoqa.authorization import AuthorizationContext
from autoqa.core import Discovery, Element, PageEvidence, save_json
from autoqa.exploration import explore, extract_workflows
from autoqa.planning import approve, plan, save_cases
from autoqa.reporting import diagnose, report
from autoqa.repository import analyze, correlate, source_discovery
from autoqa.security import Scope
from autoqa.testing import generate, parse_junit, run


def _authorized(function, operation):
    def call(project, *args, **kwargs):
        context = AuthorizationContext(project.root, frozenset({operation}))
        return function(project, *args, authorization=context, **kwargs)

    return call


plan = _authorized(plan, "plan")
approve = _authorized(approve, "review")
generate = _authorized(generate, "generate")
run = _authorized(run, "execute")
explore = _authorized(explore, "discover")
analyze = _authorized(analyze, "discover")
correlate = _authorized(correlate, "discover")
source_discovery = _authorized(source_discovery, "discover")


def evidence(project):
    project.config.application_url = "http://127.0.0.1:8000/"
    project.config.allow_localhost = True
    project.save_config()
    page = PageEvidence(
        url=project.config.application_url,
        title="Demo",
        headings=["Demo"],
        elements=[Element(kind="input", name="Email", input_type="email")],
        screenshot="screenshots/page.png",
        depth=0,
    )
    discovery = Discovery(pages=[page])
    discovery.workflows = extract_workflows(discovery)
    save_json(project.root / "discovery/workflow-map.json", discovery.model_dump())
    return discovery


def test_workflows_planning_and_approval(project):
    discovery = evidence(project)
    assert [w.status for w in discovery.workflows] == ["OBSERVED", "INFERRED"]
    cases = plan(project)
    assert len(cases) == 2
    assert not cases[1].feasible
    with pytest.raises(ValueError, match="No approved"):
        generate(project)
    with pytest.raises(ValueError, match="Unknown test"):
        approve(project, ["TC-999"])
    approve(project, ["TC-001"])
    assert project.cases()[0].review_status == "approved"
    assert plan(project)[0].review_status == "approved"
    discovery.pages[0].headings = ["Changed"]
    save_json(project.root / "discovery/workflow-map.json", discovery.model_dump())
    assert plan(project)[0].review_status == "pending"


def test_generation_integrity_and_approval_binding(project):
    evidence(project)
    plan(project)
    approve(project, ["TC-001"])
    assert generate(project) == ["TC-001"]
    generated = project.root / "automation/test_observed.py"
    ast.parse(generated.read_text())
    assert "get_by_role" in generated.read_text()
    cases = project.cases()
    cases[0].expected = "Different requirement"
    save_cases(
        project, cases, authorization=AuthorizationContext(project.root, frozenset({"review"}))
    )
    with pytest.raises(ValueError, match="Approvals changed"):
        run(project)
    generated.write_text("raise RuntimeError('do not run')")
    with pytest.raises(ValueError, match="changed after"):
        run(project)
    with pytest.raises(ValueError, match="modified/unmanaged"):
        generate(project)


def test_junit_statuses(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text(
        """<testsuites><testsuite><testcase name="test_TC_001" time=".2"/><testcase name="test_TC_002"><failure>assert missing</failure></testcase><testcase name="test_TC_003"><error>setup failed</error></testcase><testcase name="test_TC_004"><skipped/></testcase></testsuite></testsuites>"""
    )
    records = parse_junit(path)
    assert [r["status"] for r in records] == ["PASSED", "FAILED", "ERROR", "SKIPPED"]
    assert records[0]["id"] == "TC-001"
    assert parse_junit(tmp_path / "missing.xml") == []


def test_report_escapes_untrusted_content_and_diagnosis(project):
    evidence(project)
    plan(project)
    project.config.name = "<script>alert(1)</script>"
    result = {
        "run_id": "real-parser-fixture",
        "created_at": "2026-11-17",
        "records": [
            {
                "id": "TC-001",
                "name": "test_TC_001",
                "status": "FAILED",
                "duration": 1,
                "error": "assert <script>bad()</script>",
            }
        ],
        "exit_code": 1,
        "duration": 1,
        "artifact_dir": "artifacts/fixture",
        "base_url": project.config.application_url,
    }
    save_json(project.root / "reports/latest-run.json", result)
    findings = diagnose(project)
    assert findings[0]["category"] == "Assertion failure"
    assert findings[0]["human_review_required"]
    html = Path(report(project, "html")).read_text(encoding="utf-8")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    data = json.loads(Path(report(project, "json")).read_text())
    assert data["counts"] == {"FAILED": 1}


def test_repository_static_analysis(project, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text(
        'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/products")\ndef products(): pass\n'
    )
    (repo / "package.json").write_text('{"dependencies":{"react":"*"}}')
    (repo / "test_app.py").write_text("raise RuntimeError('must never execute')")
    (repo / ".env").write_text("SECRET=do-not-read")
    (repo / "node_modules").mkdir()
    (repo / "node_modules/ignored.js").write_text("ignored")
    result = analyze(project, repo)
    assert result["files_scanned"] == 3
    assert result["routes"][0]["route"] == "/products"
    assert "test_app.py" in result["existing_tests"]
    assert "react" in result["frameworks"]
    assert "SECRET" not in json.dumps(result)


def test_source_only_plan_and_hybrid_correlation(project):
    findings = {"routes": [{"route": "/products", "file": "app.py", "line": 2, "status": "SOURCE"}]}
    save_json(project.root / "discovery/repository.json", findings)
    source_discovery(project, findings)
    cases = plan(project)
    assert cases and not cases[0].feasible
    assert cases[0].review_status == "pending"
    discovery = Discovery(
        pages=[
            PageEvidence(
                url="http://example.test/products",
                title="Products",
                headings=["Products"],
                elements=[],
                screenshot="page.png",
                depth=0,
            )
        ]
    )
    matches = correlate(project, discovery)
    assert matches["matches"][0]["status"] == "INFERRED"


def test_approval_persistence_and_modified_suite_refusal(project):
    evidence(project)
    plan(project)
    approve(project, ["TC-001"])
    assert plan(project)[0].review_status == "approved"
    generate(project)
    path = project.root / "automation/test_observed.py"
    path.write_text(path.read_text() + "\n# local changes\n")
    with pytest.raises(ValueError, match="changed"):
        run(project)
    with pytest.raises(ValueError, match="modified"):
        generate(project)
    discovery = project.discovery()
    discovery.pages[0].headings = ["Changed heading"]
    save_json(project.root / "discovery/workflow-map.json", discovery.model_dump())
    assert plan(project)[0].review_status == "pending"


def test_unapproved_generation_and_unknown_approval(project):
    evidence(project)
    plan(project)
    with pytest.raises(ValueError, match="No approved"):
        generate(project)
    with pytest.raises(ValueError, match="Unknown"):
        approve(project, ["TC-001", "TC-999"])
    assert project.cases()[0].review_status == "pending"


@pytest.mark.browser
def test_real_browser_vertical_slice(project, demo_server):
    base, _ = demo_server
    project.config.allow_localhost = True
    discovery = explore(project, base)
    assert len(discovery.pages) == 5
    assert not discovery.errors
    assert any(e.name == "Search products" for p in discovery.pages for e in p.elements)
    assert all((project.root / p.screenshot).is_file() for p in discovery.pages)
    cases = plan(project)
    ids = [c.id for c in cases if c.kind == "heading"][:3]
    ids += [next(c.id for c in cases if c.kind == "link" and c.target == "Atlas Notebook")]
    approve(project, ids)
    generate(project)
    result = run(project)
    assert result["exit_code"] == 0
    assert len(result["records"]) == 4
    assert all(r["status"] == "PASSED" for r in result["records"])
    assert len(list((project.root / result["artifact_dir"]).glob("*.zip"))) == 4
    assert len(result["step_results"]) == 4
    assert all(step["status"] == "PASSED" for step in result["step_results"])
    assert all(
        any(ref.endswith(".zip") for ref in step["evidence"]) for step in result["step_results"]
    )
    assert diagnose(project) == []
    assert Path(report(project, "html")).is_file()


@pytest.mark.browser
def test_real_failure_and_report(project, demo_server):
    base, handler = demo_server
    project.config.allow_localhost = True
    project.config.max_pages = 1
    explore(project, base)
    plan(project)
    approve(project, ["TC-001"])
    generate(project)
    handler.broken = True
    result = run(project)
    assert result["exit_code"] == 1
    assert result["records"][0]["status"] == "FAILED"
    assert result["step_results"][0]["status"] == "FAILED"
    assert any(ref.endswith(".png") for ref in result["step_results"][0]["evidence"])
    assert diagnose(project)[0]["human_review_required"]
    assert "FAILED: 1" in Path(report(project, "html")).read_text()


@pytest.mark.browser
def test_real_browser_scope_redirect_and_write_blocking(project, demo_server):
    base, handler = demo_server
    project.config.allow_localhost = True
    scope = Scope(base, project.config)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(service_workers="block")
        context.route("**/*", scope.guard)
        page = context.new_page()
        page.goto(base)
        result = page.evaluate(
            """async () => { try { await fetch('/contact',{method:'POST',body:'x'}); return 'allowed'; } catch { return 'blocked'; } }"""
        )
        assert result == "blocked"
        assert "/contact" not in handler.hits
        with pytest.raises(Error):
            page.goto(base + "/redirect")
        browser.close()


@pytest.mark.browser
def test_exploration_depth_and_page_bound(project, demo_server):
    base, _ = demo_server
    project.config.allow_localhost = True
    project.config.max_depth = 0
    assert len(explore(project, base).pages) == 1
    project.config.max_depth = 2
    project.config.max_pages = 2
    assert len(explore(project, base).pages) == 2
