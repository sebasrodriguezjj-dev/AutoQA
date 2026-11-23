"""Owned synthetic acceptance for analyzer, reviewed management and standalone selection."""

import hashlib
import json
import os
import subprocess

import pytest
from test_api_framework import api_server as api_server
from test_api_framework import spec
from typer.testing import CliRunner

from autoqa.analyzer import analyze_framework
from autoqa.api_service import plan_api
from autoqa.application import ApplicationEngine
from autoqa.authorization import AuthorizationContext
from autoqa.cli import app
from autoqa.framework_runtime.management import (
    TestCase as Case,
)
from autoqa.framework_runtime.management import (
    TestPack as Pack,
)
from autoqa.framework_runtime.management import (
    TestSelection as Selection,
)
from autoqa.framework_runtime.management import (
    TestSuite as Suite,
)
from autoqa.framework_runtime.management import (
    select,
)
from autoqa.management import approve_suite, propose
from autoqa.planning import approve


def test_analyzer_readonly_classifications(tmp_path):
    assert analyze_framework(tmp_path)["classification"] == "NO_FRAMEWORK"
    (tmp_path / "package.json").write_text('{"devDependencies":{"cypress":"1"}}')
    assert analyze_framework(tmp_path)["classification"] == "UNSUPPORTED"
    (tmp_path / "package.json").unlink()
    source = tmp_path / "test_owned.py"
    source.write_text(
        "import pytest\nraise RuntimeError('MUST NEVER EXECUTE')\n@pytest.fixture\ndef page(): pass\nclass HomePage: pass\ndef test_one(): pass\n"
    )
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    report = analyze_framework(tmp_path)
    assert report["classification"] == "SUPPORTED_FRAMEWORK"
    assert len(report["tests"]) == len(report["fixtures"]) == len(report["page_objects"]) == 1
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    source.write_text(source.read_text() + "\ndef test_one(): pass\n")
    assert analyze_framework(tmp_path)["classification"] == "PARTIALLY_SUPPORTED"
    source.write_bytes(b"x" * 512001)
    assert analyze_framework(tmp_path)["classification"] == "ANALYSIS_BLOCKED"
    assert analyze_framework(tmp_path / "missing")["classification"] == "ANALYSIS_BLOCKED"


def inventory():
    return Suite(
        project_id="owned",
        review_status="approved",
        cases=[
            Case(id="TC-A", signature="a", kind="API", tags=["smoke"]),
            Case(id="TC-B", signature="b", kind="UI"),
            Case(id="TC-D", signature="d", kind="API", enabled=False),
            Case(id="TC-P", signature="p", kind="API", review_status="pending"),
        ],
        packs=[
            Pack(id="SMOKE", case_ids=["TC-A", "TC-B"]),
            Pack(id="SANITY", case_ids=["TC-B"]),
            Pack(id="EMPTY", case_ids=[]),
        ],
    )


@pytest.mark.parametrize(
    "mode,values,expected",
    [
        ("case", ["TC-A"], ["TC-A"]),
        ("pack", ["SMOKE", "SANITY"], ["TC-A", "TC-B"]),
        ("all", [], ["TC-A", "TC-B"]),
        ("suite", ["DEFAULT"], ["TC-A", "TC-B"]),
        ("tag", ["smoke"], ["TC-A"]),
    ],
)
def test_selection_deterministic_unique(mode, values, expected):
    plan = select(inventory(), Selection(mode=mode, values=values))
    assert plan.case_ids == expected
    assert len(plan.inventory_digest) == 64


@pytest.mark.parametrize(
    "mode,values",
    [
        ("case", ["TC-UNKNOWN"]),
        ("case", ["TC-D"]),
        ("case", ["TC-P"]),
        ("case", []),
        ("pack", ["UNKNOWN"]),
        ("pack", ["EMPTY"]),
        ("suite", ["UNKNOWN"]),
        ("tag", ["unknown"]),
        ("all", ["TC-A"]),
    ],
)
def test_invalid_selection_never_falls_back(mode, values):
    with pytest.raises(ValueError):
        select(inventory(), Selection(mode=mode, values=values))


def test_membership_relations_and_review_required():
    with pytest.raises(ValueError):
        Suite(project_id="x", cases=[], packs=[Pack(id="BAD", case_ids=["TC-A"])])
    with pytest.raises(ValueError, match="approval"):
        select(inventory().model_copy(update={"review_status": "pending"}), Selection())


def test_independent_selection_accounting_and_defect(project, api_server, tmp_path):
    origin, handler = api_server
    values = [
        spec(origin, id="TC-A", data={"name": "rows", "rows": [{}, {}]}),
        spec(origin, id="TC-B"),
        spec(origin, id="TC-D"),
        spec(origin, id="TC-P"),
    ]
    source = tmp_path / "source.json"
    source.write_text(json.dumps([s.model_dump() for s in values]))
    ctx = AuthorizationContext(project.root, frozenset({"plan", "review", "generate", "execute"}))
    plan_api(project, source, ctx)
    approve(project, ["TC-A", "TC-B", "TC-D"], authorization=ctx)
    suite = propose(project)
    suite.cases[0].tags = ["smoke"]
    suite.cases[2].enabled = False
    suite.packs = [
        Pack(id="SMOKE", case_ids=["TC-A", "TC-B"]),
        Pack(id="SANITY", case_ids=["TC-B"]),
        Pack(id="EMPTY", case_ids=[]),
    ]
    approve_suite(project, suite, ctx)
    export = tmp_path / "independent"
    engine = ApplicationEngine(project, ctx)
    engine.build_framework(export)
    installed = subprocess.run(
        ["uv", "sync"], cwd=export, capture_output=True, text=True, timeout=120
    )
    assert installed.returncode == 0, installed.stderr
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

    def run(arguments, expected, count, operations):
        child = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", "run", *arguments],
            cwd=export,
            capture_output=True,
            text=True,
            timeout=40,
        )
        assert child.returncode == expected, child.stdout + child.stderr
        outputs = sorted(
            (export / "artifacts").glob("*/results.json"), key=lambda p: p.stat().st_mtime_ns
        )
        result = json.loads(outputs[-1].read_text())
        assert len(result["records"]) == count
        assert len(result["steps"]) == operations
        assert result["accounting"]["eligible"] == 2
        assert result["accounting"]["not_executed"] == 0
        assert len(result["selected_case_ids"]) == len(set(result["selected_case_ids"]))
        assert all(s["run_id"] == result["run_id"] for s in result["steps"])
        assert (outputs[-1].parent / "report.html").is_file()
        return result

    single = run(["--case", "TC-A"], 0, 2, 4)
    assert single["scope"] == "SELECTED_SCOPE" and single["accounting"]["selected"] == 1
    assert single["accounting"]["passed"] == 1
    run(["--pack", "SMOKE"], 0, 3, 6)
    run(["--pack", "SMOKE", "--pack", "SANITY"], 0, 3, 6)
    run(["--tag", "smoke"], 0, 2, 4)
    run(["--suite", "DEFAULT"], 0, 3, 6)
    healthy = run(["--all"], 0, 3, 6)
    assert healthy["scope"] == "FULL_REGRESSION" and healthy["accounting"]["passed"] == 2
    handler.broken = True
    broken = run(["--all"], 1, 3, 6)
    assert broken["counts"] == {"FAILED": 3}
    handler.broken = False
    assert run(["--all"], 0, 3, 6)["counts"] == {"PASSED": 3}
    hits = len(handler.hits)
    for args in [
        ["--case", "TC-D"],
        ["--case", "TC-P"],
        ["--case", "TC-UNKNOWN"],
        ["--pack", "UNKNOWN"],
        ["--pack", "EMPTY"],
        ["--case", "TC-A", "--all"],
    ]:
        child = subprocess.run(
            [str(python), "-m", "qa_runtime.runner", "run", *args],
            cwd=export,
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert child.returncode != 0
    assert len(handler.hits) == hits
    # A newly approved source membership invalidates source-backed old exports.
    suite.cases[0].enabled = False
    approve_suite(project, suite, ctx)
    with pytest.raises(ValueError, match="membership changed"):
        engine.run_framework(export, Selection(mode="case", values=["TC-A"]))
    # No edit to membership can bypass its separate receipt.
    project.storage.write_json("test-cases/management.json", inventory().model_dump())
    with pytest.raises(ValueError, match="membership approval"):
        engine.build_framework(tmp_path / "tampered")


def test_cli_new_commands_and_invalid_mode(tmp_path, project):
    runner = CliRunner()
    for command in ["analyze-framework", "suite-propose", "suite-approve", "run-framework"]:
        assert runner.invoke(app, [command, "--help"]).exit_code == 0
    assert runner.invoke(app, ["analyze-framework", str(tmp_path)]).exit_code == 0
    from test_api_framework import prepare

    prepare(project, tmp_path / "api.json", [spec("http://127.0.0.1:8000")])
    proposed = runner.invoke(app, ["suite-propose", "--project", str(project.root)])
    assert proposed.exit_code == 0
    assert json.loads(proposed.stdout)["review_status"] == "pending"
    source = tmp_path / "suite.json"
    source.write_text(proposed.stdout, encoding="utf-8-sig")
    assert (
        runner.invoke(app, ["suite-approve", str(source), "--project", str(project.root)]).exit_code
        == 0
    )
    invalid = runner.invoke(
        app,
        [
            "run-framework",
            str(tmp_path / "absent"),
            "--project",
            str(project.root),
            "--case",
            "TC-API",
            "--all",
        ],
    )
    assert invalid.exit_code != 0 and "one selection mode" in invalid.stdout


def test_historical_runner_receives_no_new_flags(project, tmp_path, monkeypatch):
    from test_api_framework import prepare

    ctx = prepare(project, tmp_path / "source.json", [spec("http://127.0.0.1:8000")])
    engine = ApplicationEngine(project, ctx)
    export = tmp_path / "legacy"
    engine.build_framework(export)
    manifest_path = export / "framework.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"].pop("review/management.json")
    manifest.pop("operation_counts")
    (export / "review/management.json").unlink()
    manifest_path.write_text(json.dumps(manifest))
    calls = []

    def child(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", child)
    assert engine.run_framework(export) == 0
    assert calls[0][-2:] == ["qa_runtime.runner", "run"]
    with pytest.raises(ValueError, match="Historical export"):
        engine.run_framework(export, Selection(mode="case", values=["TC-API"]))


def test_analyzer_unreadable_and_traversal_are_blocked(tmp_path, monkeypatch):
    assert (
        analyze_framework(tmp_path / ".." / tmp_path.name)["classification"] == "ANALYSIS_BLOCKED"
    )

    def denied(*args, **kwargs):
        raise PermissionError("Synthetic private path is not included in diagnostics")

    monkeypatch.setattr("autoqa.analyzer.os.walk", denied)
    result = analyze_framework(tmp_path)
    assert result["classification"] == "ANALYSIS_BLOCKED"
    assert "Synthetic private path" not in json.dumps(result)
