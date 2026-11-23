"""Stage 0: characterize existing contracts without executing saved suites."""

import ast
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from playwright.sync_api import Error as BrowserError
from typer.main import get_command
from typer.testing import CliRunner

from autoqa import cli, planning, reporting, testing
from autoqa.authorization import AuthorizationContext
from autoqa.core import Project, initialize, load_json, select_project

FIXTURES = Path(__file__).parent / "fixtures/compatibility"
BASELINE = json.loads((FIXTURES / "baseline.json").read_text(encoding="utf-8"))
# name, default, repeatable, required, flag; automatic negative bool options are protected too.
CLI = {
    "init": [("name", None, False, True, False), ("parent", Path("projects"), False, False, False)],
    "demo": [
        ("host", "127.0.0.1", False, False, False),
        ("port", 8000, False, False, False),
        ("variant", "original", False, False, False),
    ],
    "explore": [
        ("url", None, False, False, False),
        ("repo", None, False, False, False),
        ("project", None, False, False, False),
        ("authorized", False, False, False, True),
        ("allow_localhost", False, False, False, True),
    ],
    "plan": [
        ("project", None, False, False, False),
        ("approve", None, True, False, False),
        ("reject", None, True, False, False),
        ("requirements", None, False, False, False),
        ("ai", False, False, False, True),
    ],
    "generate": [("project", None, False, False, False), ("approved", False, False, False, True)],
    "run": [("project", None, False, False, False)],
    "diagnose": [("project", None, False, False, False)],
    "report": [("project", None, False, False, False), ("format", "html", False, False, False)],
    "integrate": [
        ("project", None, False, False, False),
        ("provider", "github", False, False, False),
    ],
}


def tree_state(root):
    return {
        p.relative_to(root).as_posix(): (
            hashlib.sha256(p.read_bytes()).hexdigest(),
            p.stat().st_mtime_ns,
        )
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.fixture(params=["v01", "v02"])
def legacy_project(request, tmp_path):
    version = request.param
    archive = FIXTURES / f"{version}.zip"
    metadata = BASELINE[version]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == metadata["archive_sha256"]
    with ZipFile(archive) as bundle:
        assert set(bundle.namelist()) == set(metadata["files"])
        for name, expected in metadata["files"].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
        bundle.extractall(tmp_path / version)
    return version, Project(tmp_path / version)


@pytest.mark.parametrize("command", CLI)
def test_cli_signatures_and_help(command):
    commands = get_command(cli.app).commands
    assert set(commands) == set(CLI) | {
        "build-framework",
        "validate-framework",
        "run-framework",
        "plan-api",
        "analyze-framework",
        "suite-propose",
        "suite-approve",
    }
    actual = []
    for param in commands[command].params:
        flag = getattr(param, "is_flag", False)
        actual.append((param.name, param.default, param.multiple, param.required, flag))
        option = "--" + param.name.replace("_", "-")
        assert param.opts == (["name"] if param.name == "name" else [option])
        assert param.secondary_opts == (["--no-" + option[2:]] if flag else [])
    assert actual == CLI[command]
    assert CliRunner().invoke(cli.app, [command, "--help"]).exit_code == 0


@pytest.mark.parametrize(
    "args", [[], ["init"], ["unknown"], ["demo", "--port", "invalid"], ["plan", "--unknown"]]
)
def test_cli_usage_errors(args):
    assert CliRunner().invoke(cli.app, args).exit_code == 2


def test_cli_entry_point_and_root_help():
    metadata = tomllib.loads((FIXTURES.parents[2] / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["scripts"]["autoqa"] == "autoqa.cli:app"
    assert CliRunner().invoke(cli.app, ["--help"]).exit_code == 0


@pytest.mark.parametrize(
    "args,message",
    [
        (["generate"], "--approved"),
        (["plan", "--approve", "TC-001", "--reject", "TC-002"], "separate commands"),
        (["plan", "--approve", "TC-001", "--ai"], "separately"),
        (["explore", "--url", "http://127.0.0.1"], "--authorized"),
    ],
)
def test_cli_review_and_authorization_guards_are_non_mutating(project, args, message):
    before = tree_state(project.root)
    result = CliRunner().invoke(cli.app, [*args, "--project", str(project.root)])
    assert result.exit_code == 1
    assert message in result.output
    assert tree_state(project.root) == before


@pytest.mark.parametrize(
    "error,code",
    [
        (ValueError("bad input"), 1),
        (OSError("IO failure"), 1),
        (BrowserError("browser failure"), 1),
        (KeyboardInterrupt(), 130),
    ],
)
def test_cli_handled_errors(project, monkeypatch, error, code):
    def fail(_, *, authorization):
        raise error

    monkeypatch.setattr(testing, "run", fail)
    result = CliRunner().invoke(cli.app, ["run", "--project", str(project.root)])
    assert result.exit_code == code
    assert (str(error) or "Interrupted") in result.output


@pytest.mark.parametrize("code", [0, 1, 2, 3, 4, 5, 124])
def test_cli_run_propagates_process_status(project, monkeypatch, code):
    monkeypatch.setattr(
        testing, "run", lambda _, *, authorization: {"run_id": "stub", "exit_code": code}
    )
    assert CliRunner().invoke(cli.app, ["run", "--project", str(project.root)]).exit_code == code


@pytest.mark.parametrize("option", ["approve", "reject"])
def test_cli_repeated_review_ids_preserve_order(project, monkeypatch, option):
    calls = []
    monkeypatch.setattr(
        planning,
        option,
        lambda selected, ids, *, authorization: calls.append((selected.root, ids)) or [],
    )
    result = CliRunner().invoke(
        cli.app,
        ["plan", "--project", str(project.root), f"--{option}", "TC-003", f"--{option}", "TC-001"],
    )
    assert result.exit_code == 0
    assert calls == [(project.root, ["TC-003", "TC-001"])]


def test_selection_precedence_and_no_ancestor_search(project, tmp_path, monkeypatch):
    other = initialize("other", project.root.parent)  # Becomes active, distinct from cwd.
    monkeypatch.chdir(project.root)
    assert select_project(other.root).root == other.root
    assert select_project(None).root == project.root
    with pytest.raises(ValueError, match="No AutoQA project"):
        select_project(tmp_path / "missing")  # Explicit invalid path never falls back.
    monkeypatch.chdir(tmp_path)
    assert select_project(None).root == other.root
    nested = project.root / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    with pytest.raises(ValueError, match="No active project"):
        select_project(None)


def test_legacy_readers_are_non_mutating(legacy_project, monkeypatch):
    version, selected = legacy_project
    before = tree_state(selected.root)
    monkeypatch.chdir(selected.root)
    for _ in range(2):
        project = select_project(None)
        assert select_project(project.root).root == selected.root
        cases = project.cases()
        discovery = project.discovery()
        manifest = load_json(project.root / "automation/manifest.json")
        run = load_json(project.root / "reports/latest-run.json")
        assert len(cases) == (27 if version == "v01" else 31)
        assert discovery.pages
        assert project.config.api_resources == []
        for case in cases:
            if case.id in manifest["cases"]:
                assert case.review_status == "approved"
                assert planning.case_signature(case) == manifest["cases"][case.id]
        assert len(run["records"]) == (5 if version == "v01" else 9)
    assert tree_state(selected.root) == before  # Includes approvals, file additions and mtimes.


def test_legacy_manifest_signatures_and_generated_imports(legacy_project):
    version, project = legacy_project
    manifest = load_json(project.root / "automation/manifest.json")
    assert set(manifest) == (
        {"files", "cases"} if version == "v01" else {"version", "files", "cases"}
    )
    assert manifest.get("version") == (None if version == "v01" else "0.2.0")
    assert set(manifest["files"]) == {"test_observed.py", "conftest.py"}
    for name, expected in manifest["files"].items():
        assert (
            testing.digest((project.root / "automation" / name).read_text(encoding="utf-8"))
            == expected
        )
    fixture = (project.root / "automation/conftest.py").read_text(encoding="utf-8")
    imports = {
        (node.module, alias.name)
        for node in ast.walk(ast.parse(fixture))
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert {
        ("autoqa.core", "Project"),
        ("autoqa.security", "Scope"),
        ("playwright.sync_api", "sync_playwright"),
    } <= imports
    assert "Path(__file__).resolve().parent.parent" in fixture
    assert all(name in fixture for name in ["AUTOQA_BASE_URL", "AUTOQA_RUN_DIR", "qa_page"])


def test_signature_review_and_extension_field_rules(legacy_project):
    _, project = legacy_project
    for case in project.cases():
        signature = planning.case_signature(case)
        assert (
            planning.case_signature(case.model_copy(update={"review_status": "rejected"}))
            == signature
        )
        assert (
            planning.case_signature(
                case.model_copy(update={"expected": case.expected + " changed"})
            )
            != signature
        )
        for field, value in {
            "test_data": {"baseline": "changed"},
            "evidence_refs": ["baseline-changed"],
            "workflow_id": "baseline-changed",
            "contract": {"baseline": "changed"},
        }.items():
            changed = case.model_copy(update={field: value})
            assert (planning.case_signature(changed) != signature) == (case.kind == "functional")


def test_legacy_run_shape_and_junit(legacy_project):
    version, project = legacy_project
    run = load_json(project.root / "reports/latest-run.json")
    keys = {"run_id", "created_at", "exit_code", "duration", "records", "artifact_dir", "base_url"}
    snapshots = {"case_snapshot", "planning_snapshot", "discovery_snapshot"}
    assert set(run) == keys | (snapshots if version == "v02" else set())
    assert run["exit_code"] == 0
    assert run["artifact_dir"] == "artifacts/" + run["run_id"]
    parsed = testing.parse_junit(project.root / run["artifact_dir"] / "junit.xml")
    assert [(r["name"], r["status"]) for r in parsed] == [
        (r["name"], r["status"]) for r in run["records"]
    ]
    for record in run["records"]:
        assert set(record) == {"id", "name", "status", "duration", "error"}
        assert record["status"] == "PASSED"
    if version == "v02":
        assert len(run["case_snapshot"]) == 9
        assert len(run["planning_snapshot"]) == 31
        assert {c["id"] for c in run["case_snapshot"]} == {r["id"] for r in run["records"]}
        assert all(c["review_status"] == "approved" for c in run["case_snapshot"])
        assert run["discovery_snapshot"]["pages"]


def test_report_snapshot_precedence_and_documented_write_side_effects(legacy_project):
    version, project = legacy_project
    (project.root / "logs").mkdir()
    # Mutate only the disposable extracted copy to distinguish fallback from snapshots.
    (project.root / "test-cases/test-matrix.json").write_text("[]", encoding="utf-8")
    before = tree_state(project.root)
    payload = load_json(Path(reporting.report(project, "json")))
    assert payload["proposed"] == (0 if version == "v01" else 31)
    assert payload["approved"] == (0 if version == "v01" else 9)
    assert payload["counts"] == {"PASSED": 5 if version == "v01" else 9}
    after = tree_state(project.root)
    assert {name for name in after if after[name] != before.get(name)} == {
        "reports/qa-report.json",
        "reports/diagnosis.json",
        "logs/events.jsonl",
    }


@pytest.mark.parametrize(
    "outcome,code", [("partial", 0), ("collection_error", 2), ("timeout", 124)]
)
def test_run_records_snapshots_and_missing_tests_without_browser_execution(
    legacy_project, monkeypatch, outcome, code
):
    _, project = legacy_project
    (project.root / "logs").mkdir()
    manifest = load_json(project.root / "automation/manifest.json")
    cases = project.cases()
    chosen = next(iter(manifest["cases"]))
    calls = []

    def process(command, **kwargs):
        calls.append((command, kwargs))
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=2 if outcome == "collection_error" else 0, stdout="collection", stderr=""
            )
        if outcome == "timeout":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        junit = Path(command[command.index("--junitxml") + 1])
        junit.write_text(
            f'<testsuite><testcase name="test_{chosen.replace("-", "_")}" time="0.1"/></testsuite>',
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="execution", stderr="")

    monkeypatch.setenv("AUTOQA_BASE_URL", project.config.application_url)
    monkeypatch.setenv("AUTOQA_BASELINE_SECRET", "must-not-be-inherited")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--untrusted-option")
    monkeypatch.setattr(testing, "validate_python", lambda source, name: source)
    monkeypatch.setattr(testing.subprocess, "run", process)
    result = testing.run(
        project, authorization=AuthorizationContext(project.root, frozenset({"execute"}))
    )
    assert result["exit_code"] == code
    assert len(calls) == (1 if outcome == "collection_error" else 2)
    assert "--collect-only" in calls[0][0]
    env = calls[0][1]["env"]
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert env["AUTOQA_BASE_URL"] == project.config.application_url
    assert "AUTOQA_BASELINE_SECRET" not in env and "PYTEST_ADDOPTS" not in env
    assert calls[0][1]["shell"] is False
    assert result["case_snapshot"] == [c.model_dump() for c in cases if c.id in manifest["cases"]]
    assert result["planning_snapshot"] == [c.model_dump() for c in cases]
    assert result["discovery_snapshot"] == project.discovery().model_dump()
    records = {r["id"]: r for r in result["records"]}
    assert set(records) == set(manifest["cases"])
    assert all(
        r["status"] == ("PASSED" if outcome == "partial" and key == chosen else "NOT_EXECUTED")
        for key, r in records.items()
    )
    # model_dump retains tuple edges in memory; persisted JSON uses arrays.
    serialized = json.loads(json.dumps(result))
    assert load_json(project.root / "reports/latest-run.json") == serialized
    assert load_json(project.root / result["artifact_dir"] / "results.json") == serialized
    assert (project.root / result["artifact_dir"] / "pytest.log").is_file()


@pytest.mark.parametrize(
    "mutation,message",
    [
        ("manifest", "Unexpected automation manifest"),
        ("nested", "Unmanaged Python"),
        ("content", "changed after generation"),
        ("approval", "Approvals changed"),
    ],
)
def test_saved_suite_refuses_drift_before_execution(legacy_project, mutation, message, monkeypatch):
    _, project = legacy_project
    root = project.root / "automation"
    if mutation == "manifest":
        path = root / "manifest.json"
        data = load_json(path)
        data["files"]["extra.py"] = "invalid"
        path.write_text(json.dumps(data), encoding="utf-8")
    elif mutation == "nested":
        (root / "nested").mkdir()
        (root / "nested/unmanaged.py").write_text("", encoding="utf-8")
    elif mutation == "content":
        with (root / "test_observed.py").open("a", encoding="utf-8") as stream:
            stream.write("\n# changed\n")
    else:
        path = project.root / "test-cases/test-matrix.json"
        cases = load_json(path)
        for case in cases:
            case["review_status"] = "pending"
        path.write_text(json.dumps(cases), encoding="utf-8")
    # Guard tests exercise preflight only, never import/collect/run frozen browser code.
    monkeypatch.setattr(testing, "validate_python", lambda source, name: source)
    monkeypatch.setattr(
        testing.subprocess, "run", lambda *a, **kw: pytest.fail("Unexpected subprocess")
    )
    with pytest.raises(ValueError, match=message):
        testing.run(
            project, authorization=AuthorizationContext(project.root, frozenset({"execute"}))
        )
