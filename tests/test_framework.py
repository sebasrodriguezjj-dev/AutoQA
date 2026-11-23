"""Framework compilation, approval/path boundaries and real standalone acceptance."""

import hashlib
import json
import os
import subprocess
import sys
import threading
import tomllib
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
from typer.testing import CliRunner

from autoqa import __version__
from autoqa.application import ApplicationEngine
from autoqa.authorization import AuthorizationContext
from autoqa.cli import app
from autoqa.core import Discovery, PageEvidence
from autoqa.discovery_service import DiscoveryService
from autoqa.framework import (
    FrameworkBlueprint,
    FrameworkService,
    checked_destination,
    compile_blueprint,
)
from autoqa.framework_runtime import runner
from autoqa.framework_runtime.evidence import StepRecorder
from autoqa.framework_runtime.integrity import safe_path, validate
from autoqa.framework_runtime.runner import read_steps, render_report
from autoqa.independent_demo import SupplyHandler
from autoqa.planning_service import PlanningService
from examples.independent_contracts import reviewed_contracts


def context(project, *operations):
    return AuthorizationContext(project.root, frozenset(operations))


@pytest.fixture
def reviewed_project(project):
    project.config.application_url = "http://127.0.0.1:8000/"
    project.config.allow_localhost = True
    project.config.allowed_domains = ["127.0.0.1"]
    project.save_config()
    page = PageEvidence(
        url=project.config.application_url,
        title="Demo",
        headings=["Demo"],
        elements=[],
        screenshot="screenshots/page.png",
        depth=0,
    )
    project.storage.write_json("discovery/workflow-map.json", Discovery(pages=[page]).model_dump())
    planning = PlanningService(project, context(project, "plan", "review"))
    cases = planning.plan()
    planning.approve([cases[0].id])
    return project


def test_framework_authorization_receipts_and_destination(reviewed_project, tmp_path):
    project = reviewed_project
    destination = tmp_path / "export"
    with pytest.raises(ValueError, match="Explicit generate"):
        FrameworkService(project, None).build(destination)
    with pytest.raises(ValueError, match="Explicit generate"):
        FrameworkService(project, AuthorizationContext(tmp_path, frozenset({"generate"}))).build(
            destination
        )
    receipt = project.storage.read_json("test-cases/approval-receipts.json")
    project.storage.write_json("test-cases/approval-receipts.json", {})
    with pytest.raises(ValueError, match="reapproval"):
        FrameworkService(project, context(project, "generate")).build(destination)
    assert not destination.exists()
    project.storage.write_json("test-cases/approval-receipts.json", receipt)
    with pytest.raises(ValueError, match="overlap"):
        checked_destination(project, project.root / "export")
    with pytest.raises(ValueError, match="traversal"):
        checked_destination(project, tmp_path / ".." / "export")
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "user.txt").write_text("preserve")
    with pytest.raises(ValueError, match="already exists"):
        checked_destination(project, existing)
    assert (existing / "user.txt").read_text() == "preserve"


def test_blueprint_reports_unsupported_and_excludes_unapproved(reviewed_project):
    project = reviewed_project
    cases = project.cases()
    unsupported = cases[0].model_copy(
        update={"id": "TC-MANUAL", "kind": "manual", "feasible": False}
    )
    pending = cases[0].model_copy(update={"id": "TC-PENDING", "review_status": "pending"})
    project.storage.write_json(
        "test-cases/test-matrix.json", [c.model_dump() for c in [*cases, unsupported, pending]]
    )
    PlanningService(project, context(project, "review")).approve([unsupported.id])
    blueprint, selected = compile_blueprint(project)
    assert [c.id for c in selected] == [cases[0].id]
    assert blueprint.unsupported == {unsupported.id: "Approved scenario is not automatable"}
    assert all(s.id != pending.id for s in blueprint.scenarios)
    assert {o.kind for p in blueprint.pages for o in p.operations} == {"navigation", "assertion"}


def test_framework_export_integrity_and_cli(reviewed_project, tmp_path):
    project = reviewed_project
    destination = tmp_path / "export"
    result = ApplicationEngine(project, context(project, "generate")).build_framework(destination)
    manifest = validate(destination)
    assert manifest["version"] == __version__ == "0.5.0"
    metadata = tomllib.loads((destination / "pyproject.toml").read_text())
    assert metadata["project"]["version"] == __version__
    assert result["cases"] == list(manifest["cases"])
    second = tmp_path / "repeat-export"
    FrameworkService(project, context(project, "generate")).build(second)
    assert validate(second) == manifest
    assert (destination / "requirements.txt").read_text().startswith("playwright==")
    assert "autoqa" not in (destination / "requirements.txt").read_text().lower()
    source = (destination / "tests/test_approved.py").read_text()
    assert "model.assertion_" in source and "get_by_role" not in source
    page = next((destination / "pages").glob("page_*.py")).read_text()
    assert "locator_demo_" in page and "to_be_visible" in page
    assert not (destination / "discovery").exists()
    assert CliRunner().invoke(app, ["validate-framework", str(destination)]).exit_code == 0
    for command in ("build-framework", "validate-framework", "run-framework"):
        assert CliRunner().invoke(app, [command, "--help"]).exit_code == 0
    assert (
        CliRunner()
        .invoke(app, ["build-framework", str(tmp_path / "other"), "--project", str(project.root)])
        .exit_code
        == 1
    )
    (destination / "tests/test_approved.py").write_text("raise RuntimeError('changed')")
    with pytest.raises(ValueError, match="file changed"):
        validate(destination)
    assert CliRunner().invoke(app, ["validate-framework", str(destination)]).exit_code == 1


def test_framework_current_approvals_are_rechecked(reviewed_project, tmp_path):
    project = reviewed_project
    destination = tmp_path / "export"
    service = FrameworkService(project, context(project, "generate", "execute"))
    service.build(destination)
    PlanningService(project, context(project, "review")).reject([project.cases()[0].id])
    with pytest.raises(ValueError, match="approvals changed"):
        service.run(destination)
    with pytest.raises(ValueError, match="Explicit execute"):
        FrameworkService(project, None).run(destination)


def test_blueprint_relationships_and_unrepresentable_expectations(reviewed_project):
    blueprint, _ = compile_blueprint(reviewed_project)
    payload = blueprint.model_dump()
    payload["scenarios"][0]["methods"] = ["nonexistent", "also_missing"]
    with pytest.raises(ValueError, match="unknown page operations"):
        FrameworkBlueprint.model_validate(payload)
    cases = reviewed_project.cases()
    cases[0].expected = "Unrepresented business requirement"
    reviewed_project.storage.write_json(
        "test-cases/test-matrix.json", [c.model_dump() for c in cases]
    )
    PlanningService(reviewed_project, context(reviewed_project, "review")).approve([cases[0].id])
    with pytest.raises(ValueError, match="not representable"):
        compile_blueprint(reviewed_project)


def test_exported_receipt_and_unmanaged_code_guards(reviewed_project, tmp_path):
    destination = tmp_path / "export"
    FrameworkService(reviewed_project, context(reviewed_project, "generate")).build(destination)
    extra = destination / "tests/unmanaged.py"
    extra.write_text("raise RuntimeError('do not execute')")
    with pytest.raises(ValueError, match="Unmanaged executable"):
        validate(destination)
    extra.unlink()
    receipts = destination / "review/receipts.json"
    original = json.loads(receipts.read_text())
    original[next(iter(original))]["scenario_signature"] = "changed"
    receipts.write_text(json.dumps(original))
    manifest_path = destination / "framework.json"
    manifest = json.loads(manifest_path.read_text())
    # Even refreshing a single file digest must not repair the independent receipt binding.
    manifest["files"]["review/receipts.json"] = hashlib.sha256(receipts.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="approval binding invalid"):
        validate(destination)


class FakePage:
    def __init__(self, broken=False):
        self.broken = broken

    def is_closed(self):
        return False

    def screenshot(self, path):
        if self.broken:
            raise OSError("sensitive raw error")
        Path(path).write_bytes(b"synthetic image")


@pytest.mark.parametrize(
    "policy,passed,expected",
    [
        ("every_step", True, 1),
        ("every_step", False, 1),
        ("failures_only", True, 0),
        ("failures_only", False, 1),
        ("disabled", True, 0),
        ("disabled", False, 0),
    ],
)
def test_operation_evidence_policies(tmp_path, policy, passed, expected):
    recorder = StepRecorder(FakePage(), tmp_path, "TC-1", "run", policy)
    if passed:
        with recorder.step("action", "Perform fill"):
            pass
    else:
        with pytest.raises(AssertionError):
            with recorder.step("assertion", "Verify count"):
                raise AssertionError("sensitive input must not enter step log")
    assert len(list(tmp_path.glob("*.png"))) == expected
    assert recorder.records[0]["status"] == ("PASSED" if passed else "FAILED")
    assert "sensitive" not in (tmp_path / "TC-1-steps.json").read_text()
    assert recorder.records[0]["run_id"] == "run"


def test_capture_failures_skips_interruptions_and_absent_steps(tmp_path):
    recorder = StepRecorder(FakePage(True), tmp_path, "TC-1", "run", "every_step")
    assert recorder.records == []
    with recorder.step("action", "Perform action"):
        pass
    assert recorder.records[0]["status"] == "PASSED"
    assert "OSError" in recorder.records[0]["evidence_error"]
    with pytest.raises(pytest.skip.Exception):
        with recorder.step("assertion", "Verify result"):
            pytest.skip("synthetic skip")
    assert recorder.records[1]["status"] == "SKIPPED"
    with pytest.raises(KeyboardInterrupt):
        with recorder.step("action", "Perform action"):
            raise KeyboardInterrupt
    assert recorder.records[2]["status"] == "INTERRUPTED"
    assert [s["sequence"] for s in recorder.records] == [1, 2, 3]


def test_run_scoped_diagnostics_and_report_escaping(tmp_path):
    for name in ("TC-1-step-1.png", "TC-2-step-1.png"):
        (tmp_path / name).write_bytes(b"image")
    records = [
        {
            "run_id": "run",
            "test_id": "TC-1",
            "sequence": 1,
            "kind": "assertion",
            "status": "FAILED",
            "duration": 0.1,
            "evidence": ["TC-1-step-1.png", "TC-2-step-1.png", "../escape.png"],
        },
        {"run_id": "old", "test_id": "TC-1", "evidence": ["TC-1-step-1.png"]},
    ]
    (tmp_path / "TC-1-steps.json").write_text(json.dumps(records))
    steps = read_steps(tmp_path, "run", ["TC-1"])
    assert len(steps) == 1 and steps[0]["evidence"] == ["TC-1-step-1.png"]
    result = {
        "run_id": "run",
        "records": [
            {"id": "TC-1", "status": "FAILED", "duration": 1, "error": "<script>secret</script>"}
        ],
        "steps": steps,
    }
    render_report(tmp_path, result)
    assert "<script>" not in (tmp_path / "report.html").read_text()
    findings = json.loads((tmp_path / "diagnosis.json").read_text())
    assert findings[0]["evidence"] == ["TC-1-step-1.png"]


@pytest.mark.parametrize("reference", ["../x", "/x", "C:/x", "a\\b", "a//b"])
def test_standalone_safe_paths(tmp_path, reference):
    with pytest.raises(ValueError):
        safe_path(tmp_path, reference)


@pytest.mark.parametrize(
    "mode,expected", [("collection", 2), ("timeout", 124), ("missing-junit", 3)]
)
def test_missing_junit_is_not_passed(reviewed_project, tmp_path, monkeypatch, mode, expected):
    destination = tmp_path / "export"
    FrameworkService(reviewed_project, context(reviewed_project, "generate")).build(destination)
    calls = []

    def process(command, **kwargs):
        calls.append(command)
        if len(calls) == 1:
            return subprocess.CompletedProcess(
                command, 2 if mode == "collection" else 0, "collection", ""
            )
        if mode == "missing-junit":
            return subprocess.CompletedProcess(command, 0, "no JUnit emitted", "")
        raise subprocess.TimeoutExpired(command, 1)

    monkeypatch.setattr(runner.subprocess, "run", process)
    result = runner.execute(destination)
    assert result["exit_code"] == expected
    assert result["counts"] == {"NOT_EXECUTED": 1}
    assert result["steps"] == []
    assert len(calls) == (1 if mode == "collection" else 2)


def test_standalone_export_collects_without_autoqa_or_browser(reviewed_project, tmp_path):
    destination = tmp_path / "independent-export"
    FrameworkService(reviewed_project, context(reviewed_project, "generate")).build(destination)
    keep = {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "HOME",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "COMSPEC",
        "UV_CACHE_DIR",
        "UV_PYTHON_INSTALL_DIR",
    }
    environment = {key: value for key, value in os.environ.items() if key.upper() in keep}
    environment["UV_PYTHON"] = sys.executable
    install = subprocess.run(
        ["uv", "sync"],
        cwd=destination,
        env=environment,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert install.returncode == 0, install.stdout + install.stderr
    python = destination / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    probe = subprocess.run(
        [
            str(python),
            "-c",
            "import importlib.util; assert importlib.util.find_spec('autoqa') is None; import playwright, pytest, pydantic, yaml",
        ],
        cwd=destination,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr
    for operation in ("validate", "collect"):
        check = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", operation],
            cwd=destination,
            env=environment,
            capture_output=True,
            text=True,
            timeout=45,
        )
        assert check.returncode == 0, check.stdout + check.stderr
        if operation == "collect":
            assert "1 test collected" in check.stdout
    # Collection is not execution evidence and must not fabricate scenario outcomes.
    assert not list((destination / "artifacts").glob("*/results.json"))


@pytest.mark.parametrize("method", ["is_symlink", "is_junction"])
def test_framework_destination_rejects_parent_links(
    reviewed_project, tmp_path, monkeypatch, method
):
    parent = tmp_path / "linked"
    original = getattr(Path, method)
    monkeypatch.setattr(Path, method, lambda path: path == parent or original(path))
    with pytest.raises(ValueError, match="links/junctions"):
        checked_destination(reviewed_project, parent / "export")


@pytest.mark.browser
@pytest.mark.parametrize(
    "policy,trace,headed", [("failures_only", True, False), ("disabled", False, True)]
)
def test_framework_browser_configuration_and_cli(
    project, demo_server, tmp_path, policy, trace, headed
):
    base, handler = demo_server
    project.config.allow_localhost = True
    project.config.max_pages = 1
    project.config.request_interval_ms = 0
    project.config.screenshot_policy = policy
    project.config.trace_enabled = trace
    project.config.headless = not headed
    authorization = context(project, "discover", "plan", "review", "generate", "execute")
    DiscoveryService(project, authorization).discover(url=base)
    cases = PlanningService(project, authorization).plan()
    PlanningService(project, authorization).approve([cases[0].id])
    destination = tmp_path / "framework"
    built = CliRunner().invoke(
        app, ["build-framework", str(destination), "--project", str(project.root), "--approved"]
    )
    assert built.exit_code == 0, built.output
    assert (
        CliRunner()
        .invoke(app, ["run-framework", str(destination), "--project", str(project.root)])
        .exit_code
        == 0
    )
    healthy = sorted((destination / "artifacts").glob("*/results.json"))[-1]
    data = json.loads(healthy.read_text())
    assert data["counts"] == {"PASSED": 1}
    assert [s["kind"] for s in data["steps"]] == ["navigation", "assertion"]
    assert len(list(healthy.parent.glob("*.zip"))) == int(trace)
    assert not list(healthy.parent.glob("*.png"))
    handler.broken = True
    result = CliRunner().invoke(
        app, ["run-framework", str(destination), "--project", str(project.root)]
    )
    assert result.exit_code == 1
    broken = sorted((destination / "artifacts").glob("*/results.json"))[-1]
    data = json.loads(broken.read_text())
    assert data["counts"] == {"FAILED": 1}
    assert data["steps"][-1]["status"] == "FAILED"
    assert len(list(broken.parent.glob("*.png"))) == int(policy == "failures_only")
    assert len(list(broken.parent.glob("*.zip"))) == int(trace)


@pytest.mark.browser
def test_standalone_framework_pass_defect_restore(project, tmp_path):
    class Handler(SupplyHandler):
        regression = ""

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/inventory"
            project.config.allow_localhost = True
            project.config.request_interval_ms = 0
            project.config.screenshot_policy = "every_step"
            authorization = context(project, "discover", "plan", "review", "generate", "execute")
            discovery = DiscoveryService(project, authorization).discover(url=url).discovery
            requirements = project.root / "test-cases/reviewed.json"
            project.storage.write_json("test-cases/reviewed.json", reviewed_contracts(discovery))
            planning = PlanningService(project, authorization)
            cases = planning.plan(requirements)
            selected = [c.id for c in cases if c.kind == "functional"]
            selected.append(
                next(c.id for c in cases if c.kind == "link" and c.target == "Moss Journal")
            )
            planning.approve(selected)
            destination = tmp_path / "independent-framework"
            built = FrameworkService(project, authorization).build(destination)
            assert set(built["cases"]) == set(selected) and len(selected) == 9
            environment = {
                k: v
                for k, v in os.environ.items()
                if k.upper()
                not in {
                    "PYTHONPATH",
                    "VIRTUAL_ENV",
                    "UV_PROJECT_ENVIRONMENT",
                    "PYTEST_ADDOPTS",
                    "PYTEST_PLUGINS",
                }
            }
            synced = subprocess.run(
                ["uv", "sync", "--offline"],
                cwd=destination,
                env=environment,
                capture_output=True,
                text=True,
                timeout=90,
            )
            assert synced.returncode == 0, synced.stdout + synced.stderr
            python = (
                destination / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            )
            isolated = subprocess.run(
                [
                    str(python),
                    "-c",
                    "import importlib.util; assert importlib.util.find_spec('autoqa') is None; import playwright, pytest, pydantic, yaml",
                ],
                cwd=destination,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert isolated.returncode == 0, isolated.stderr

            def command(operation):
                completed = subprocess.run(
                    [str(python), "-m", "qa_runtime.runner", operation],
                    cwd=destination,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                return completed

            assert command("validate").returncode == 0
            collection = command("collect")
            assert collection.returncode == 0 and "9 tests collected" in collection.stdout

            def run(expected_code, expected_counts):
                completed = command("run")
                assert completed.returncode == expected_code, completed.stdout + completed.stderr
                candidates = sorted((destination / "artifacts").glob("*/results.json"))
                result_path = candidates[-1]
                result = json.loads(result_path.read_text())
                assert result["counts"] == expected_counts, (
                    result_path.parent / "pytest.log"
                ).read_text()
                assert all(step["run_id"] == result["run_id"] for step in result["steps"])
                assert {s["kind"] for s in result["steps"]} == {"navigation", "action", "assertion"}
                assert len(result["steps"]) > len(result["records"]) * 2
                for step in result["steps"]:
                    assert step["evidence"]
                    assert all((result_path.parent / name).is_file() for name in step["evidence"])
                assert (result_path.parent / "report.html").is_file()
                return result, result_path.parent

            healthy, _ = run(0, {"PASSED": 9})
            assert all(s["status"] == "PASSED" for s in healthy["steps"])
            Handler.regression = "search"
            broken, output = run(1, {"PASSED": 7, "FAILED": 2})
            failures = {r["id"] for r in broken["records"] if r["status"] == "FAILED"}
            assert failures == {"TC-F-search-found", "TC-F-search-empty"}
            assert {s["test_id"] for s in broken["steps"] if s["status"] == "FAILED"} == failures
            findings = json.loads((output / "diagnosis.json").read_text())
            assert len(findings) == 2 and all(f["human_review_required"] for f in findings)
            Handler.regression = ""
            restored, _ = run(0, {"PASSED": 9})
            assert restored["run_id"] != healthy["run_id"] != broken["run_id"]
            assert validate(destination)["cases"]
        finally:
            server.shutdown()
            thread.join(timeout=3)
