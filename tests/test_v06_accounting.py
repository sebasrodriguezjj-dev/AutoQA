"""Deterministic missing/ambiguous/partial accounting without executing source code."""

import json
import subprocess
from pathlib import Path

import pytest

from autoqa.core import Config
from autoqa.framework_runtime import runner
from autoqa.framework_runtime.evidence import StepRecorder
from autoqa.framework_runtime.management import TestSelection as Selection


def execute(tmp_path, monkeypatch, xml, *, unsupported=False, selection=None, steps=2):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/environment.json").write_text(json.dumps(Config(name="Owned").model_dump()))
    cases = {"TC-A": "a", **({} if unsupported else {"TC-B": "b"})}
    manifest = {"files": {}, "cases": cases, "operation_counts": {c: 2 for c in cases}}
    monkeypatch.setattr(runner, "validate", lambda root: manifest)
    inventory = runner.load_inventory(tmp_path, manifest)
    if unsupported:
        from autoqa.framework_runtime.management import TestCase

        inventory.cases.append(TestCase(id="TC-B", signature="b", kind="UI", supported=False))
    monkeypatch.setattr(runner, "load_inventory", lambda *args: inventory)
    commands = []

    def child(command, **kwargs):
        commands.append(command)
        if "--junitxml" in command:
            target = Path(command[command.index("--junitxml") + 1])
            target.write_text(xml)
            for case in cases:
                recorder = StepRecorder(
                    None, target.parent, case, kwargs["env"]["AUTOQA_RUN_ID"], "disabled"
                )
                for _ in range(steps):
                    with recorder.step("assertion", "Owned operation"):
                        pass
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(runner.subprocess, "run", child)
    result = runner.execute(tmp_path, selection=selection)
    from autoqa.framework_runtime.management import ExecutionRun

    contract = ExecutionRun.model_validate(result["execution_run"])
    assert contract.plan.case_ids == result["selected_case_ids"]
    assert [r.case_id for r in contract.results] == contract.plan.case_ids
    assert contract.completed_at == result["completed_at"]
    return result, commands


def test_partial_selection_is_not_full_regression(tmp_path, monkeypatch):
    result, commands = execute(
        tmp_path,
        monkeypatch,
        '<testsuite><testcase name="test_TC_A"/></testsuite>',
        selection=Selection(mode="case", values=["TC-A"]),
    )
    assert result["exit_code"] == 0
    assert result["scope"] == "SELECTED_SCOPE"
    assert result["accounting"]["selected"] == 1 and result["accounting"]["eligible"] == 2
    assert all("tests/test_approved.py::test_TC_B" not in c for c in commands)


@pytest.mark.parametrize(
    "xml,expected",
    [
        ('<testsuite><testcase name="test_TC_A"/></testsuite>', {"PASSED": 1, "NOT_EXECUTED": 1}),
        (
            '<testsuite><testcase name="test_TC_A"/><testcase name="test_TC_B"><skipped/></testcase></testsuite>',
            {"PASSED": 1, "SKIPPED": 1},
        ),
        (
            '<testsuite><testcase name="test_TC_A"/><testcase name="test_TC_A"/></testsuite>',
            {"ERROR": 1, "NOT_EXECUTED": 1},
        ),
        ("<broken", {"NOT_EXECUTED": 2}),
    ],
)
def test_incomplete_or_ambiguous_never_passes(tmp_path, monkeypatch, xml, expected):
    result, _ = execute(tmp_path, monkeypatch, xml)
    assert result["exit_code"] == 3
    assert result["overall_status"] == "INCOMPLETE_OR_FAILED"
    assert result["counts"] == expected
    assert (
        sum(
            result["accounting"][s]
            for s in ["passed", "failed", "error", "skipped", "not_executed", "unsupported"]
        )
        == 2
    )


def test_missing_operation_tail_fails_even_with_passed_junit(tmp_path, monkeypatch):
    result, _ = execute(
        tmp_path,
        monkeypatch,
        '<testsuite><testcase name="test_TC_A"/><testcase name="test_TC_B"/></testsuite>',
        steps=1,
    )
    assert result["exit_code"] == 3
    assert result["counts"] == {"ERROR": 2}


def test_unexpected_junit_identity_marks_run_incomplete(tmp_path, monkeypatch):
    result, _ = execute(
        tmp_path,
        monkeypatch,
        '<testsuite><testcase name="test_TC_A"/><testcase name="test_TC_B"/><testcase name="test_FOREIGN"/></testsuite>',
    )
    assert result["exit_code"] == 3
    assert result["reconciliation_errors"]


@pytest.mark.parametrize("only_unsupported", [False, True])
def test_unsupported_scope_is_reported_without_fallback(tmp_path, monkeypatch, only_unsupported):
    selection = Selection(mode="case", values=["TC-B"]) if only_unsupported else Selection()
    result, commands = execute(
        tmp_path,
        monkeypatch,
        '<testsuite><testcase name="test_TC_A"/></testsuite>',
        unsupported=True,
        selection=selection,
    )
    assert result["exit_code"] == 3
    assert result["accounting"]["unsupported"] == 1
    if only_unsupported:
        assert commands == [] and result["counts"] == {"UNSUPPORTED": 1}
    else:
        assert result["counts"] == {"PASSED": 1, "UNSUPPORTED": 1}
