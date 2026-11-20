from pathlib import Path

import pytest

from autoqa import exploration, repository
from autoqa.authorization import AuthorizationContext
from autoqa.discovery_service import DiscoveryService


def test_discovery_denied_before_mutation(project, tmp_path):
    service = DiscoveryService(project, None)
    before = project.config.model_dump()
    with pytest.raises(ValueError, match="Explicit"):
        service.discover(repo=tmp_path, allow_localhost=True)
    assert project.config.model_dump() == before
    for action in (
        lambda: exploration.explore(project, "http://127.0.0.1/"),
        lambda: repository.analyze(project, tmp_path),
        lambda: repository.source_discovery(project, {"routes": []}),
        lambda: repository.correlate(project, None),
    ):
        with pytest.raises(ValueError, match="Explicit"):
            action()


def test_source_discovery_in_process(project, tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text('@app.get("/hello")\ndef hello(): pass\n')
    auth = AuthorizationContext(project.root, frozenset({"discover"}))
    result = DiscoveryService(project, auth).discover(repo=repo)
    assert result.findings["routes"][0]["route"] == "/hello"
    assert project.discovery().workflows[0].status == "SOURCE"
    assert project.config.mode == "repository"
    assert (project.root / "discovery/repository.json").exists()


@pytest.mark.browser
def test_hybrid_service_uses_real_browser_and_correlates(project, tmp_path, demo_server):
    base, _ = demo_server
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text('@app.get("/")\ndef home(): pass\n')
    project.config.max_pages = 1
    project.config.request_interval_ms = 0
    auth = AuthorizationContext(project.root, frozenset({"discover"}))
    result = DiscoveryService(project, auth).discover(url=base, repo=repo, allow_localhost=True)
    assert result.discovery.pages
    assert result.discovery.evidence_records[0].category == "OBSERVED"
    assert result.correlation["matches"][0]["status"] == "INFERRED"
    assert project.config.mode == "hybrid"
