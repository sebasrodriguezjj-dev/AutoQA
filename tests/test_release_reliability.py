"""Bounded reliability review: real handles, distinct writers and conservative JUnit."""

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from autoqa.core import Config
from autoqa.framework_runtime import runner
from autoqa.framework_runtime.evidence import StepRecorder


def test_distinct_run_and_row_writers_keep_every_completed_step(tmp_path):
    def write(identity):
        run_id = f"review-run-{identity // 4}"
        test_id = f"TC-API--row-{identity % 4}"
        output = tmp_path / run_id
        output.mkdir(exist_ok=True)
        recorder = StepRecorder(None, output, test_id, run_id, "disabled")
        for i in range(8):
            with recorder.step("assertion", "Synthetic bounded check"):
                pass
            saved = json.loads((output / (test_id + "-steps.json")).read_text())
            assert len(saved) == i + 1
            assert [r["sequence"] for r in saved] == list(range(1, i + 2))
            assert all(
                r["run_id"] == run_id and r["test_id"] == test_id and r["status"] == "PASSED"
                for r in saved
            )
        return len(saved)

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(write, range(32))) == 256
    for i in range(8):
        ids = [f"TC-API--row-{row}" for row in range(4)]
        assert len(runner.read_steps(tmp_path / f"review-run-{i}", f"review-run-{i}", ids)) == 32
        assert runner.read_steps(tmp_path / f"review-run-{i}", "other-run", ids) == []


@pytest.mark.skipif(os.name != "nt", reason="Requires Windows file sharing semantics")
def test_windows_real_read_handle_blocks_replace_until_closed(tmp_path, monkeypatch):
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    recorder = StepRecorder(None, tmp_path, "TC-WINDOWS", "review-run", "disabled")
    recorder.persist()
    path = tmp_path / "TC-WINDOWS-steps.json"
    # Read/write sharing, deliberately no FILE_SHARE_DELETE.
    handle = kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 0x80, None)
    assert handle != wintypes.HANDLE(-1).value
    waits = []

    def release(delay):
        nonlocal handle
        waits.append(delay)
        assert kernel.CloseHandle(handle)
        handle = None

    monkeypatch.setattr("autoqa.framework_runtime.evidence.time.sleep", release)
    try:
        with recorder.step("action", "Owned sharing-violation reproduction"):
            pass
        assert waits == [0.025]
        assert json.loads(path.read_text())[0]["status"] == "PASSED"
    finally:
        if handle is not None:
            kernel.CloseHandle(handle)


def fake_execution(tmp_path, monkeypatch, xml, step_run=None):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/environment.json").write_text(
        json.dumps(Config(name="Synthetic").model_dump())
    )
    monkeypatch.setattr(
        runner, "validate", lambda root: {"files": {}, "cases": {"TC-API": "reviewed"}}
    )

    def child(command, **kwargs):
        if "--junitxml" in command:
            if xml is not None:
                junit_path = Path(command[command.index("--junitxml") + 1])
                junit_path.write_text(xml)
                if step_run:
                    run_id = (
                        kwargs["env"]["AUTOQA_RUN_ID"] if step_run == "current" else "other-run"
                    )
                    recorder = StepRecorder(None, junit_path.parent, "TC-API", run_id, "disabled")
                    with recorder.step("assertion", "Synthetic completed operation"):
                        pass
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(runner.subprocess, "run", child)
    return runner.execute(tmp_path)


def test_missing_junit_never_becomes_pass(tmp_path, monkeypatch):
    result = fake_execution(tmp_path, monkeypatch, None)
    assert result["exit_code"] == 3
    assert result["counts"] == {"NOT_EXECUTED": 1}


@pytest.mark.parametrize(
    "first,second",
    [
        ("<failure>synthetic failure</failure>", ""),
        ("", "<error>synthetic error</error>"),
        ("", ""),
    ],
)
def test_duplicate_junit_does_not_overwrite_failure_with_pass(tmp_path, monkeypatch, first, second):
    result = fake_execution(
        tmp_path,
        monkeypatch,
        f'<testsuite><testcase name="test_TC_API">{first}</testcase><testcase name="test_TC_API">{second}</testcase></testsuite>',
    )
    assert result["exit_code"] != 0
    assert result["records"][0]["status"] != "PASSED"
    assert result["counts"] == {"ERROR": 1}


def test_actual_failed_junit_remains_failed_without_executed_steps(tmp_path, monkeypatch):
    result = fake_execution(
        tmp_path,
        monkeypatch,
        '<testsuite><testcase name="test_TC_API"><failure>synthetic failure</failure></testcase></testsuite>',
    )
    assert result["exit_code"] == 3
    assert result["counts"] == {"FAILED": 1}
    assert result["steps"] == []


@pytest.mark.parametrize("step_run", [None, "foreign", "current"])
def test_passing_junit_requires_evidence_from_current_run(tmp_path, monkeypatch, step_run):
    result = fake_execution(
        tmp_path, monkeypatch, '<testsuite><testcase name="test_TC_API"/></testsuite>', step_run
    )
    if step_run == "current":
        assert result["exit_code"] == 0
        assert result["counts"] == {"PASSED": 1}
    else:
        assert result["exit_code"] != 0
        assert result["counts"] == {"ERROR": 1}
