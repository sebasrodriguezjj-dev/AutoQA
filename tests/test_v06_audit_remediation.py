"""Independent audit reproductions: static detection and collection scope integrity."""

import json
import subprocess

import pytest
from test_api_framework import api_server as api_server

from autoqa.analyzer import analyze_framework
from autoqa.core import Config
from autoqa.framework_runtime import runner
from autoqa.framework_runtime.management import TestCase as Case
from autoqa.framework_runtime.management import TestPack as Pack
from autoqa.framework_runtime.management import TestSelection as Selection
from autoqa.framework_runtime.management import TestSuite as Suite


@pytest.mark.parametrize(
    "name,content",
    [
        ("package.json", '{"name":"owned-app","dependencies":{"express":"1"}}'),
        ("pom.xml", "<project><artifactId>owned-app</artifactId></project>"),
        ("build.gradle", "plugins { id 'application' }\nrepositories { mavenCentral() }"),
    ],
)
def test_plain_build_metadata_is_not_a_test_framework(tmp_path, name, content):
    (tmp_path / name).write_text(content, encoding="utf-8")
    result = analyze_framework(tmp_path)
    assert result["classification"] == "NO_FRAMEWORK"
    assert name in result["configuration"]


@pytest.mark.parametrize(
    "source",
    [
        "def test_helper(): pass\n",
        "def outer():\n    def test_nested(): pass\n",
    ],
)
def test_non_collected_python_helpers_are_uncertain_not_supported(tmp_path, source):
    (tmp_path / "helpers.py").write_text(source, encoding="utf-8")
    result = analyze_framework(tmp_path)
    assert result["classification"] == "PARTIALLY_SUPPORTED"
    assert result["tests"] == []


@pytest.mark.parametrize("folder", ["build", ".hidden"])
def test_default_excluded_directories_are_not_collected_test_facts(tmp_path, folder):
    directory = tmp_path / folder
    directory.mkdir()
    (directory / "test_helper.py").write_text("def test_helper(): pass\n")
    result = analyze_framework(tmp_path)
    assert result["classification"] != "SUPPORTED_FRAMEWORK"
    assert result["tests"] == []


@pytest.mark.parametrize(
    "name,content",
    [
        ("cypress.config.ts", "export default {};"),
        ("package.json", '{"devDependencies":{"cypress":"1"}}'),
        (
            "pom.xml",
            "<project><dependencies><dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId></dependency></dependencies></project>",
        ),
        ("build.gradle", "dependencies { testImplementation 'org.testng:testng:7' }"),
    ],
)
def test_recognized_non_python_tooling_remains_unsupported(tmp_path, name, content):
    (tmp_path / name).write_text(content, encoding="utf-8")
    assert analyze_framework(tmp_path)["classification"] == "UNSUPPORTED"


def test_valid_pytest_mixed_and_readonly(tmp_path):
    source = tmp_path / "test_owned.py"
    content = "raise RuntimeError('NEVER EXECUTE')\ndef test_owned(): pass\n"
    source.write_text(content, encoding="utf-8")
    assert analyze_framework(tmp_path)["classification"] == "SUPPORTED_FRAMEWORK"
    (tmp_path / "package.json").write_text('{"name":"plain-node-app"}')
    assert analyze_framework(tmp_path)["classification"] == "SUPPORTED_FRAMEWORK"
    (tmp_path / "cypress.config.js").write_text("throw new Error('NEVER EXECUTE')")
    assert analyze_framework(tmp_path)["classification"] == "PARTIALLY_SUPPORTED"
    assert source.read_text(encoding="utf-8") == content


def test_empty_unreadable_and_metadata_budget(tmp_path, monkeypatch):
    assert analyze_framework(tmp_path)["classification"] == "NO_FRAMEWORK"
    manifest = tmp_path / "package.json"
    manifest.write_bytes(b" " * 512001)
    assert analyze_framework(tmp_path)["classification"] == "ANALYSIS_BLOCKED"
    manifest.unlink()

    def denied(*args, **kwargs):
        raise PermissionError("private detail")

    monkeypatch.setattr("autoqa.analyzer.os.walk", denied)
    result = analyze_framework(tmp_path)
    assert result["classification"] == "ANALYSIS_BLOCKED"
    assert "private detail" not in json.dumps(result)


def collection(
    tmp_path,
    monkeypatch,
    *,
    unsupported=False,
    legacy=False,
    selection=None,
    output="tests/test_approved.py::test_TC_A\n\n1 test collected in 0.01s\n",
):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/environment.json").write_text(json.dumps(Config(name="Owned").model_dump()))
    manifest = {"files": {}, "cases": {"TC-A": "a"}}
    monkeypatch.setattr(runner, "validate", lambda root: manifest)
    if not legacy:
        suite = Suite(
            project_id="owned",
            review_status="approved",
            cases=[
                Case(id="TC-A", signature="a", kind="API"),
                *(
                    [Case(id="TC-B", signature="b", kind="UI", supported=False)]
                    if unsupported
                    else []
                ),
            ],
            packs=[
                Pack(id="MIXED", case_ids=["TC-A", "TC-B"] if unsupported else ["TC-A"]),
                Pack(id="EMPTY", case_ids=[]),
            ],
        )
        monkeypatch.setattr(runner, "load_inventory", lambda *args: suite)
    calls = []

    def child(command, **kwargs):
        assert "--collect-only" in command
        assert "--junitxml" not in command
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(runner.subprocess, "run", child)
    result = runner.execute(tmp_path, collect_only=True, selection=selection)
    assert not list((tmp_path / "artifacts").glob("*/results.json"))
    return result, calls


@pytest.mark.parametrize("selection", [Selection(), Selection(mode="pack", values=["MIXED"])])
def test_collect_mixed_selected_inventory_is_not_success(tmp_path, monkeypatch, selection):
    result, _ = collection(tmp_path, monkeypatch, unsupported=True, selection=selection)
    assert result["exit_code"] != 0


def test_collect_unsupported_only_never_invokes_pytest(tmp_path, monkeypatch):
    result, calls = collection(
        tmp_path, monkeypatch, unsupported=True, selection=Selection(mode="case", values=["TC-B"])
    )
    assert result["exit_code"] != 0 and calls == []


@pytest.mark.parametrize("legacy", [False, True])
def test_collect_supported_and_legacy_success(tmp_path, monkeypatch, legacy):
    result, calls = collection(tmp_path, monkeypatch, legacy=legacy)
    assert result["exit_code"] == 0 and len(calls) == 1


@pytest.mark.parametrize(
    "output",
    [
        "",
        "tests/test_approved.py::test_OTHER\n",
        "tests/test_approved.py::test_TC_A\ntests/test_approved.py::test_TC_A\n",
    ],
)
def test_collect_missing_foreign_or_duplicate_cannot_pass(tmp_path, monkeypatch, output):
    result, _ = collection(tmp_path, monkeypatch, output=output)
    assert result["exit_code"] != 0


def test_collect_foreign_module_cannot_hide_outside_fixed_module(tmp_path, monkeypatch):
    result, _ = collection(
        tmp_path,
        monkeypatch,
        output="tests/test_approved.py::test_TC_A\ntests/test_foreign.py::test_other\n",
    )
    assert result["exit_code"] != 0


@pytest.mark.parametrize(
    "selection",
    [Selection(mode="case", values=["TC-UNKNOWN"]), Selection(mode="pack", values=["EMPTY"])],
)
def test_collect_invalid_selection_has_no_fallback(tmp_path, monkeypatch, selection):
    with pytest.raises(ValueError):
        collection(tmp_path, monkeypatch, selection=selection)


def test_real_independent_collection_preserves_scope_without_requests(
    project, tmp_path, api_server
):
    import os

    from test_api_framework import prepare, spec

    from autoqa.application import ApplicationEngine
    from autoqa.management import approve_suite, propose
    from autoqa.planning import approve

    # An owned listener records any request; collection must never invoke runtime fixtures.
    origin, handler = api_server
    ctx = prepare(project, tmp_path / "source.json", [spec(origin)])
    cases = project.cases()
    unsupported = cases[0].model_copy(
        update={
            "id": "TC-UNSUPPORTED",
            "kind": "manual",
            "contract": None,
            "feasible": False,
            "review_status": "pending",
        }
    )
    project.storage.write_json(
        "test-cases/test-matrix.json", [c.model_dump() for c in [*cases, unsupported]]
    )
    approve(project, [unsupported.id], authorization=ctx)
    suite = propose(project)
    suite.packs = [
        Pack(id="MIXED", case_ids=[cases[0].id, unsupported.id]),
        Pack(id="EMPTY", case_ids=[]),
    ]
    approve_suite(project, suite, ctx)
    export = tmp_path / "standalone"
    ApplicationEngine(project, ctx).build_framework(export)
    install = subprocess.run(
        ["uv", "sync"], cwd=export, capture_output=True, text=True, timeout=120
    )
    assert install.returncode == 0, install.stderr
    python = export / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    assert (
        subprocess.run(
            [
                str(python),
                "-c",
                "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
            ],
            cwd=export,
            timeout=20,
        ).returncode
        == 0
    )

    def collect(args, expected):
        process = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", "collect", *args],
            cwd=export,
            capture_output=True,
            text=True,
            timeout=40,
        )
        assert process.returncode == expected, process.stdout + process.stderr
        assert handler.hits == []
        assert not list((export / "artifacts").glob("*/results.json"))
        assert not list((export / "artifacts").glob("*/*-steps.json"))
        return process

    collect(["--case", cases[0].id], 0)
    collect(["--pack", "MIXED"], 3)
    collect(["--all"], 3)
    collect(["--case", unsupported.id], 3)
    collect(["--case", "TC-UNKNOWN"], 1)
    collect(["--pack", "EMPTY"], 1)
    summaries = [
        json.loads(p.read_text()) for p in (export / "artifacts").glob("*/collection.json")
    ]
    assert sum(s["collection_status"] == "COMPLETE" for s in summaries) == 1
    assert all(
        s["unsupported_case_ids"] == [unsupported.id] for s in summaries if s["exit_code"] == 3
    )
    # Explicit legacy adapter only knows the executable historical manifest scope.
    manifest_path = export / "framework.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"].pop("review/management.json")
    (export / "review/management.json").unlink()
    manifest_path.write_text(json.dumps(manifest))
    collect([], 0)
