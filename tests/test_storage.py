"""Persistence failure safety and confinement in disposable projects."""

import json
from pathlib import Path

import pytest

from autoqa.core import Project, initialize, select_project
from autoqa.storage import LocalProjectStorage, save_json


@pytest.mark.parametrize("reference", ["../x", "/x", "C:/x", "a\\b", "a/../b", "a//b"])
def test_invalid_paths(tmp_path, reference):
    store = LocalProjectStorage(tmp_path)
    with pytest.raises(ValueError):
        store.write_json(reference, {})
    assert list(tmp_path.iterdir()) == []


def test_missing_corrupt_and_read_only(project):
    store = project.storage
    with pytest.raises(ValueError, match="Missing"):
        store.read_json("reports/missing.json")
    store.write_text("reports/broken.json", "{")
    before = {
        p: (p.read_bytes(), p.stat().st_mtime_ns) for p in project.root.rglob("*") if p.is_file()
    }
    with pytest.raises(json.JSONDecodeError):
        store.read_json("reports/broken.json")
    Project(project.root)
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before} == before


def test_atomic_replace_failure_preserves_original(project, monkeypatch):
    path = project.root / "reports/record.json"
    save_json(path, {"original": True})
    before = path.read_bytes()

    def fail(*args):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(OSError, match="simulated"):
        project.storage.write_json("reports/record.json", {"new": True})
    assert path.read_bytes() == before
    assert list(path.parent.iterdir()) == [path]


def test_serialization_failure_is_non_mutating(project):
    before = set(project.root.rglob("*"))
    with pytest.raises(TypeError):
        project.storage.write_json("reports/new.json", {"bad": object()})
    assert set(project.root.rglob("*")) == before


def test_isolation_selection_and_history(project, monkeypatch):
    second = initialize("second", project.root.parent)
    project.storage.write_json("artifacts/run/results.json", {"status": "PASSED"})
    with pytest.raises(ValueError, match="immutable"):
        project.storage.write_json("artifacts/run/results.json", {})
    with pytest.raises(ValueError, match="immutable"):
        project.storage.write_text("artifacts/run/new.log", "changed")
    assert not second.storage.path("artifacts/run").exists()
    monkeypatch.chdir(project.root.parent.parent)
    assert select_project(None).root == second.root
    assert select_project(project.root).root == project.root


@pytest.mark.parametrize("method", ["is_symlink", "is_junction"])
def test_nested_links_rejected(project, monkeypatch, method):
    link = project.root / "reports/linked"
    original = getattr(Path, method)
    monkeypatch.setattr(Path, method, lambda path: path == link or original(path))
    with pytest.raises(ValueError, match="link"):
        project.storage.write_json("reports/linked/x.json", {})
    assert not link.exists()
