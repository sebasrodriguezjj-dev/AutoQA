from pathlib import Path

import pytest

from autoqa.application import ApplicationEngine, InProcessAdapter
from autoqa.authorization import AuthorizationContext
from autoqa.core import Discovery, PageEvidence


def test_application_engine_keeps_controls_below_interface(project):
    page = PageEvidence(
        url="http://127.0.0.1:8000/",
        title="Example",
        headings=["Example"],
        elements=[],
        screenshot="screenshots/example.png",
        depth=0,
    )
    project.storage.write_json("discovery/workflow-map.json", Discovery(pages=[page]).model_dump())
    project.config.application_url = page.url
    project.config.allow_localhost = True
    project.save_config()

    with pytest.raises(ValueError, match="Explicit"):
        ApplicationEngine(project).plan()

    context = AuthorizationContext(project.root, frozenset({"plan", "review"}))
    adapter = InProcessAdapter(ApplicationEngine(project, context))
    cases = adapter.plan()
    assert cases and cases[0].review_status == "pending"
    assert adapter.approve([cases[0].id])[0].review_status == "approved"


def test_application_engine_rejects_wrong_project_context(project, tmp_path: Path):
    context = AuthorizationContext(tmp_path / "other", frozenset({"plan"}))
    with pytest.raises(ValueError, match="Explicit"):
        ApplicationEngine(project, context).plan()
