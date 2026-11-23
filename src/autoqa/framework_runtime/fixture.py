"""Generated-framework fixtures; Chromium scope enforcement is retained."""

import json
import os
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import pytest
from playwright.sync_api import sync_playwright

from .config import Config
from .evidence import StepRecorder
from .integrity import validate
from .security import Scope


@pytest.fixture
def qa_session(request):
    root = Path(__file__).resolve().parents[1]
    manifest = validate(root)
    config = Config.model_validate(json.loads((root / "config/environment.json").read_text()))
    if config.auth_reference:
        raise ValueError("Authenticated execution is unsupported")
    base = os.environ.get("AUTOQA_BASE_URL", config.application_url)
    scope = Scope(base, config)
    test_id = next(
        k for k in manifest["cases"] if "test_" + k.replace("-", "_") == request.node.name
    )
    run_id = os.environ.get("AUTOQA_RUN_ID")
    if not run_id or not run_id.replace("-", "").isalnum():
        raise ValueError("Run via python -m qa_runtime.runner run")
    output = root / "artifacts" / run_id
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=config.headless, slow_mo=config.slow_mo_ms, args=scope.chromium_args
        )
        try:
            context = browser.new_context(service_workers="block", accept_downloads=False)
            context.route("**/*", scope.guard)
            context.route_web_socket("**/*", lambda socket: socket.close())
            if config.trace_enabled:
                context.tracing.start(screenshots=True, snapshots=True, sources=False)
            page = context.new_page()
            page.set_default_timeout(config.navigation_timeout_ms)
            recorder = StepRecorder(page, output, test_id, run_id, config.screenshot_policy)

            def resolve(recorded):
                return scope.validate(urljoin(base, urlsplit(recorded).path))

            try:
                yield page, resolve, recorder
            finally:
                if config.trace_enabled:
                    try:
                        name = test_id + ".zip"
                        context.tracing.stop(path=str(output / name))
                        for record in recorder.records:
                            record["evidence"].append(name)
                    except Exception as error:
                        for record in recorder.records:
                            record["evidence_error"] += (
                                f" Trace capture failed ({type(error).__name__})"
                            )
                recorder.persist()
        finally:
            browser.close()
