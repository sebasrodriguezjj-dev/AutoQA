"""Independent H04 approval-to-compilation binding regressions over owned fixtures."""

import json

import pytest
from test_v08_framework import auth, drift, prepare, snapshot

from autoqa.framework import FrameworkService
from autoqa.management import approve_suite
from autoqa.management import propose as propose_suite
from autoqa.planning import approve
from autoqa.v08_maintenance import MaintenanceService


def locator_drift(project, value="amount-other", element="EL-AMOUNT"):
    discovery = project.storage.read_json("discovery/workflow-map.json")
    target = next(e for e in discovery["pages"][0]["elements"] if e["id"] == element)
    target["locators"] = [{"strategy": "test_id", "value": value, "name": "", "count": 1}]
    project.storage.write_json("discovery/workflow-map.json", discovery)


def applied_repair(project, tmp_path):
    source, original = prepare(project, tmp_path)
    original_page = next((source / "pages").glob("page_*.py"))
    assert "amount-old" in original_page.read_text(encoding="utf-8")
    locator = drift(project)
    service = MaintenanceService(project, auth(project, "review", "maintain"))
    proposal = service.propose(source, original.id, "EL-AMOUNT", locator)
    service.review(source, proposal, "accepted")
    revised = service.apply(source, proposal)
    assert revised.contract == original.contract
    assert revised.expected == original.expected
    assert revised.review_status == "pending"
    return source, original, proposal


def reapprove(project, case):
    return approve(project, [case.id], authorization=auth(project, "review"))


def membership(project):
    return approve_suite(project, propose_suite(project), auth(project, "review"))


@pytest.mark.parametrize(
    "boundary", ["after-apply", "after-scenario", "after-membership", "legacy-generate"]
)
def test_exact_reviewed_locator_cannot_drift_into_managed_output(project, tmp_path, boundary):
    from autoqa.testing import generate

    source, original, _ = applied_repair(project, tmp_path)
    original_source = snapshot(source)
    if boundary != "after-apply":
        reapprove(project, original)
    if boundary in {"after-membership", "legacy-generate"}:
        membership(project)
    locator_drift(project)
    actions = []
    if boundary == "after-apply":
        actions.append(lambda: reapprove(project, original))
    if boundary in {"after-apply", "after-scenario"}:
        actions.append(lambda: membership(project))
    output = tmp_path / "fresh-unreviewed-locator"
    if boundary == "legacy-generate":
        actions.append(lambda: generate(project, authorization=auth(project, "generate")))
    else:
        actions.append(lambda: FrameworkService(project, auth(project, "generate")).build(output))
    for action in actions:
        before = snapshot(project.root)
        try:
            action()
        except ValueError:
            assert snapshot(project.root) == before, (
                "Rejected boundary must not refresh review state"
            )
            assert snapshot(source) == original_source
            assert not output.exists()
            return
    assert snapshot(source) == original_source
    if boundary == "legacy-generate":
        generated = (project.root / "automation/test_observed.py").read_text(encoding="utf-8")
        print(
            "Observed legacy output locator:",
            "amount-other" if "amount-other" in generated else "other",
        )
    else:
        generated = "\n".join(
            p.read_text(encoding="utf-8") for p in (output / "pages").glob("*.py")
        )
        blueprint = json.loads((output / "blueprint.json").read_text(encoding="utf-8"))
        print("Observed PageObject amount-other:", "amount-other" in generated)
        print("Observed blueprint amount-other:", "amount-other" in json.dumps(blueprint))
        assert "amount-other" not in json.dumps(blueprint), (
            "Unreviewed locator entered compiled blueprint"
        )
    assert "amount-other" not in generated, (
        "Accepted amount-new decision authorized amount-other output"
    )
    pytest.fail("Meaningful post-apply locator drift was not rejected at any managed boundary")


def test_legacy_execution_refuses_drift_before_any_process_or_run_write(
    project, tmp_path, monkeypatch
):
    from autoqa import testing

    source, original, _ = applied_repair(project, tmp_path)
    reapprove(project, original)
    membership(project)
    testing.generate(project, authorization=auth(project, "generate"))
    assert "amount-new" in (project.root / "automation/test_observed.py").read_text(
        encoding="utf-8"
    )
    locator_drift(project)
    before, source_before = snapshot(project.root), snapshot(source)

    def forbidden(*args, **kwargs):
        pytest.fail("Stale maintenance execution reached a subprocess")

    monkeypatch.setattr(testing, "validate_python", lambda text, name: text)
    monkeypatch.setattr(testing.subprocess, "run", forbidden)
    with pytest.raises(ValueError):
        testing.run(project, authorization=auth(project, "execute"))
    assert snapshot(project.root) == before
    assert snapshot(source) == source_before
