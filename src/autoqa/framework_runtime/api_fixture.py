"""No-browser API fixture; one isolated recorder and data mapping per parameter row."""

import os
import re
from pathlib import Path

import pytest

from .api import APIService
from .evidence import StepRecorder
from .integrity import validate


@pytest.fixture
def qa_api(request):
    root = Path(__file__).resolve().parents[1]
    manifest = validate(root)
    case_id = next(
        k
        for k in manifest["cases"]
        if request.node.name.split("[")[0] == "test_" + k.replace("-", "_")
    )
    index = request.node.callspec.params["row"] if hasattr(request.node, "callspec") else 0
    test_id = case_id + f"--row-{index}"
    run_id = os.environ.get("AUTOQA_RUN_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9-]+", run_id):
        raise ValueError("Run via python -m qa_runtime.runner run")
    output = root / "artifacts" / run_id
    output.mkdir(parents=True, exist_ok=True)
    recorder = StepRecorder(None, output, test_id, run_id, "disabled")
    try:
        yield APIService(recorder)
    finally:
        recorder.persist()
