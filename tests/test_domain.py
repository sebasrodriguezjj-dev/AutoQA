"""Versioned contracts and non-mutating frozen legacy projections."""

import json
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

import pytest
from pydantic import ValidationError

from autoqa import domain, legacy


@pytest.mark.parametrize("version", ["v01", "v02"])
def test_frozen_projection(version):
    with ZipFile(Path(__file__).parent / f"fixtures/compatibility/{version}.zip") as bundle:
        cases = json.loads(bundle.read("test-cases/test-matrix.json"))
        run = json.loads(bundle.read("reports/latest-run.json"))
    original = deepcopy((cases, run))
    suite = legacy.suite_from_legacy(cases, project_id="project", suite_id="suite")
    projected = [legacy.case_from_legacy(c, suite_id=suite.id) for c in cases]
    execution = legacy.run_from_legacy(run, project_id="project", suite_id=suite.id)
    assert [c.id for c in projected] == [c["id"] for c in cases]
    assert all(not s.supported for c in projected for s in c.steps)
    assert all(c.review_actor is None and c.reviewed_at is None for c in projected)
    assert all(s.status == "NOT_RECORDED" for r in execution.results for s in r.steps)
    assert domain.TestRun.model_validate_json(execution.model_dump_json()) == execution
    assert (cases, run) == original


@pytest.mark.parametrize("path", ["../secret", "/secret", "C:/secret", "a\\b", "a/../b", "a//b"])
def test_artifact_paths(path):
    with pytest.raises(ValueError):
        domain.Evidence(project_id="p", artifact=path)


def test_versions_and_relationships():
    with pytest.raises(ValidationError):
        domain.Project(name="p", schema_version="0.4")
    with pytest.raises(ValueError):
        legacy.case_from_legacy({"schema_version": "0.4"}, suite_id="s")
    with pytest.raises(ValidationError):
        domain.TestCase(
            id="c",
            suite_id="s",
            title="t",
            expected="e",
            steps=[domain.TestStep(case_id="other", ordinal=1, description="d")],
        )
    with pytest.raises(ValidationError):
        domain.Project(name="p", created_at="2026-01-01T00:00:00")
    project = domain.Project(name="p")
    assert domain.Project.model_validate_json(project.model_dump_json()).id == project.id
