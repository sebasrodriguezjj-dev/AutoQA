"""Suppress unsafe persistent capture before JUnit serialization, preserving outcomes."""

import json
from pathlib import Path

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    report = result.get_result()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "framework.json").read_text(encoding="utf-8"))
    if manifest.get("privacy") == "summary_only":
        report.sections = []
        report.user_properties = []
        if report.failed:
            category = type(call.excinfo.value).__name__ if call.excinfo else "UnknownError"
            report.longrepr = f"{report.when} failed ({category}); sensitive details withheld by reviewed evidence policy"
