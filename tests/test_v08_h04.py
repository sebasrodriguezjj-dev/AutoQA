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


def compiled_operations(blueprint, case_id):
    scenario = next(s for s in blueprint["scenarios"] if s["id"] == case_id)
    page = next(p for p in blueprint["pages"] if p["module"] == scenario["page"])
    operations = {operation["method"]: operation for operation in page["operations"]}
    result = []
    for method in scenario["methods"]:
        operation = operations[method]
        source = operation["source"]
        for name, expression in page["locators"].items():
            source = source.replace("self." + name, expression)
        result.append((operation["kind"], source))
    return result


def two_case_baseline(project, tmp_path, shared):
    from autoqa.core import Element, LocatorCandidate
    from autoqa.functional import BehaviorContract, functional_case
    from autoqa.planning import save_cases

    _, original = prepare(project, tmp_path)
    discovery = project.discovery()
    other = Element(
        id="EL-OTHER",
        kind="input",
        name="Other amount",
        input_type="number",
        locators=[LocatorCandidate(strategy="test_id", value="other-old", count=1)],
    )
    discovery.pages[0].elements.append(other)
    project.storage.write_json("discovery/workflow-map.json", discovery.model_dump())
    contract = BehaviorContract.model_validate(
        original.contract
        | {
            "id": "SECOND",
            "title": "Separate approved operation",
            "steps": [
                {"action": "fill", "element_id": "EL-AMOUNT" if shared else other.id, "value": "8"}
            ],
        }
    )
    second = functional_case(contract, discovery, local=True)
    save_cases(project, [original, second], authorization=auth(project, "review"))
    approve(project, [original.id, second.id], authorization=auth(project, "review"))
    membership(project)
    source = tmp_path / "two-case-managed"
    FrameworkService(project, auth(project, "generate")).build(source)
    return source, original, project.cases()[1]


@pytest.mark.parametrize("shared", [True, False])
def test_single_repair_cannot_silently_change_another_approved_case(project, tmp_path, shared):
    source, original, other = two_case_baseline(project, tmp_path, shared)
    original_source = snapshot(source)
    old_blueprint = json.loads((source / "blueprint.json").read_text(encoding="utf-8"))
    from autoqa.v08_contracts import LocatorSpec

    locator_drift(project, "amount-new")
    locator = LocatorSpec(strategy="test_id", value="amount-new")
    service = MaintenanceService(project, auth(project, "review", "maintain"))
    output = tmp_path / "two-case-repaired"
    steps = [
        lambda: service.propose(source, original.id, "EL-AMOUNT", locator),
    ]
    before = snapshot(project.root)
    try:
        proposal = steps[0]()
    except ValueError:
        assert snapshot(project.root) == before
        assert snapshot(source) == original_source
        return
    for action in [
        lambda: service.review(source, proposal, "accepted"),
        lambda: service.apply(source, proposal),
        lambda: reapprove(project, original),
        lambda: membership(project),
        lambda: FrameworkService(project, auth(project, "generate")).build(output),
    ]:
        before = snapshot(project.root)
        try:
            action()
        except ValueError:
            assert snapshot(project.root) == before
            assert snapshot(source) == original_source
            assert not output.exists()
            return
    new_blueprint = json.loads((output / "blueprint.json").read_text(encoding="utf-8"))
    assert compiled_operations(new_blueprint, other.id) == compiled_operations(
        old_blueprint, other.id
    ), "Repair to one case silently changed another approved case's compiled operations"
    assert project.cases()[1].contract == other.contract
    assert project.cases()[1].expected == other.expected
    assert snapshot(source) == original_source


@pytest.mark.parametrize("scope", ["same-case", "other-case"])
def test_unrelated_locator_drift_cannot_hitchhike_on_a_reviewed_repair(project, tmp_path, scope):
    source, original, other = two_case_baseline(project, tmp_path, shared=False)
    original_source = snapshot(source)
    old_blueprint = json.loads((source / "blueprint.json").read_text(encoding="utf-8"))
    from autoqa.v08_contracts import LocatorSpec

    locator_drift(project, "amount-new")
    locator = LocatorSpec(strategy="test_id", value="amount-new")
    service = MaintenanceService(project, auth(project, "review", "maintain"))
    proposal = service.propose(source, original.id, "EL-AMOUNT", locator)
    service.review(source, proposal, "accepted")
    service.apply(source, proposal)
    reapprove(project, original)
    membership(project)
    if scope == "same-case":
        locator_drift(project, "unreviewed-result", "EL-RESULT")
    else:
        # drift() intentionally uses the standard amount fixture, so retain this
        # unrelated element in the fresh synthetic observation before challenging it.
        discovery = project.storage.read_json("discovery/workflow-map.json")
        if not any(e["id"] == "EL-OTHER" for e in discovery["pages"][0]["elements"]):
            pytest.fail("Synthetic unrelated element was lost before its drift test")
        locator_drift(project, "unreviewed-other", "EL-OTHER")
    output = tmp_path / "unrelated-drift"
    before = snapshot(project.root)
    try:
        FrameworkService(project, auth(project, "generate")).build(output)
    except ValueError:
        assert snapshot(project.root) == before
        assert snapshot(source) == original_source
        assert not output.exists()
        return
    new_blueprint = json.loads((output / "blueprint.json").read_text(encoding="utf-8"))
    actual = json.dumps(new_blueprint)
    assert "unreviewed-result" not in actual and "unreviewed-other" not in actual, (
        "Unrelated unreviewed locator entered a new managed export"
    )
    assert compiled_operations(new_blueprint, other.id) == compiled_operations(
        old_blueprint, other.id
    )
    assert snapshot(source) == original_source
    pytest.fail(
        "Unrelated meaningful locator drift was silently accepted during maintenance export"
    )


@pytest.mark.browser
def test_actual_chromium_exact_repair_binding_and_preserved_application_defect(project, tmp_path):
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from playwright.sync_api import sync_playwright

    from autoqa.observation import observe_elements
    from autoqa.v08_contracts import LocatorSpec

    class Handler(BaseHTTPRequestHandler):
        identifier = "amount-old"
        defective = False
        hits = 0

        def log_message(self, *_):
            pass

        def do_GET(self):
            Handler.hits += 1
            expected = "Wrong result" if self.defective else "Approved result"
            content = (
                '<label for="amount">Amount</label><input id="amount" type="number" '
                f'data-testid="{self.identifier}"><h1 data-testid="result">{expected}</h1>'
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = f"http://127.0.0.1:{server.server_port}/"

    def observed_locator(identifier):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            assert page.get_by_test_id(identifier).count() == 1
            elements = observe_elements(page, url, "synthetic-h04.png")
            element = next(e for e in elements if e.attributes.get("data-testid") == identifier)
            locator = next(c for c in element.locators if c.strategy == "test_id")
            assert locator.count == 1
            browser.close()
            return locator

    def record(destination):
        previous = set((destination / "artifacts").glob("*/results.json"))
        code = FrameworkService(project, auth(project, "execute")).run(destination)
        created = set((destination / "artifacts").glob("*/results.json")) - previous
        assert len(created) == 1
        result = json.loads(created.pop().read_text(encoding="utf-8"))
        assert result["exit_code"] == code
        return result

    try:
        assert observed_locator("amount-old").count == 1
        source, original = prepare(project, tmp_path, url)
        healthy = record(source)
        assert healthy["exit_code"] == 0 and healthy["counts"] == {"PASSED": 1}
        # Capture immutable original files before further project source review.
        source_before = snapshot(source)
        Handler.identifier = "amount-new"
        replacement = observed_locator("amount-new")
        locator_failure = record(source)
        assert locator_failure["exit_code"] != 0 and locator_failure["counts"].get("FAILED") == 1
        source_before = snapshot(source)
        discovery = project.storage.read_json("discovery/workflow-map.json")
        discovery["pages"][0]["elements"][0]["locators"] = [replacement.model_dump()]
        project.storage.write_json("discovery/workflow-map.json", discovery)
        service = MaintenanceService(project, auth(project, "maintain", "review"))
        proposal = service.propose(
            source, original.id, "EL-AMOUNT", LocatorSpec.model_validate(replacement.model_dump())
        )
        service.review(source, proposal, "accepted")
        service.apply(source, proposal)
        applied_context = project.storage.read_json("discovery/workflow-map.json")
        # A genuinely observed third locator cannot inherit the amount-new review.
        Handler.identifier = "amount-other"
        third = observed_locator("amount-other")
        changed = project.storage.read_json("discovery/workflow-map.json")
        changed["pages"][0]["elements"][0]["locators"] = [third.model_dump()]
        project.storage.write_json("discovery/workflow-map.json", changed)
        before_rejection = snapshot(project.root)
        with pytest.raises(ValueError):
            reapprove(project, original)
        assert snapshot(project.root) == before_rejection
        assert snapshot(source) == source_before
        # Restore the exact reviewed context; this does not refresh a stale binding.
        Handler.identifier = "amount-new"
        project.storage.write_json("discovery/workflow-map.json", applied_context)
        reapprove(project, original)
        membership(project)
        fresh = tmp_path / "reviewed-exact-repair"
        FrameworkService(project, auth(project, "generate")).build(fresh)
        page_source = "\n".join(
            p.read_text(encoding="utf-8") for p in (fresh / "pages").glob("*.py")
        )
        assert "amount-new" in page_source and "amount-other" not in page_source
        repaired = record(fresh)
        assert repaired["exit_code"] == 0 and repaired["counts"] == {"PASSED": 1}
        Handler.defective = True
        failed = record(fresh)
        assert failed["exit_code"] != 0 and failed["counts"].get("FAILED") == 1
        assert any(
            step["kind"] == "assertion" and step["status"] == "FAILED" for step in failed["steps"]
        )
        assert project.cases()[0].contract == original.contract
        assert project.cases()[0].expected == original.expected
        assert snapshot(source) == source_before
        evidence = {
            "healthy": {"exit_code": healthy["exit_code"], "counts": healthy["counts"]},
            "locator_changed": {
                "exit_code": locator_failure["exit_code"],
                "counts": locator_failure["counts"],
            },
            "repaired": {"exit_code": repaired["exit_code"], "counts": repaired["counts"]},
            "application_defect": {"exit_code": failed["exit_code"], "counts": failed["counts"]},
            "third_locator_rejected_before_approval": True,
            "all_actual_locator_counts": [1, 1, 1],
            "assertions_and_original_export_preserved": True,
        }
        path = tmp_path / "h04-browser-acceptance.json"
        path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print("H04 actual browser evidence:", json.dumps(evidence, sort_keys=True))
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def test_source_backed_framework_execution_rejects_drift_before_process_or_audit(
    project, tmp_path, monkeypatch
):
    import subprocess

    source, original, _ = applied_repair(project, tmp_path)
    reapprove(project, original)
    membership(project)
    output = tmp_path / "approved-exact-new"
    FrameworkService(project, auth(project, "generate")).build(output)
    locator_drift(project)
    before, old_before, fresh_before = snapshot(project.root), snapshot(source), snapshot(output)

    def forbidden(*args, **kwargs):
        pytest.fail("Stale source-backed framework execution reached a subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(ValueError):
        FrameworkService(project, auth(project, "execute")).run(output)
    assert snapshot(project.root) == before
    assert snapshot(source) == old_before
    assert snapshot(output) == fresh_before


def test_direct_blueprint_compilation_cannot_bypass_exact_maintenance_binding(project, tmp_path):
    from autoqa.framework import compile_blueprint

    source, original, _ = applied_repair(project, tmp_path)
    reapprove(project, original)
    membership(project)
    locator_drift(project)
    before, old_before = snapshot(project.root), snapshot(source)
    try:
        compiled, _ = compile_blueprint(project)
    except ValueError:
        assert snapshot(project.root) == before
        assert snapshot(source) == old_before
        return
    assert "amount-other" not in compiled.model_dump_json(), (
        "Direct compiler accepted unreviewed replacement"
    )
    pytest.fail("Direct compiler did not reject meaningful post-apply locator drift")


@pytest.mark.parametrize(
    "change",
    [
        "missing-reference",
        "null-reference",
        "missing-index",
        "changed-index",
        "missing-ledger",
        "changed-ledger",
        "missing-decision",
        "rejected-decision",
        "changed-source",
        "stored-config",
        "data",
        "missing-locator",
        "ambiguous-locator",
        "contradictory-element",
    ],
)
def test_lost_or_changed_maintenance_identity_rejects_every_managed_boundary(
    project, tmp_path, monkeypatch, change
):
    from autoqa import testing
    from autoqa.framework import compile_blueprint
    from autoqa.v08_contracts import digest
    from autoqa.v08_revision import ACTIVE, revision_path

    source, original, proposal = applied_repair(project, tmp_path)
    revised = project.cases()[0]
    assert revised.maintenance_revision is not None
    ledger_path = revision_path(revised.maintenance_revision)
    decision_path = "maintenance/v08/decision-" + digest(proposal.id) + ".json"
    if change in {"missing-reference", "null-reference"}:
        cases = project.storage.read_json("test-cases/test-matrix.json")
        if change == "missing-reference":
            cases[0].pop("maintenance_revision")
        else:
            cases[0]["maintenance_revision"] = None
        project.storage.write_json("test-cases/test-matrix.json", cases)
    elif change in {"missing-index", "missing-ledger", "missing-decision"}:
        relative = {
            "missing-index": ACTIVE,
            "missing-ledger": ledger_path,
            "missing-decision": decision_path,
        }[change]
        path = project.storage.path(relative)
        # Preserve the owned fixture input rather than discard it.
        path.rename(path.with_suffix(".preserved"))
    elif change == "changed-index":
        project.storage.write_json(ACTIVE, {"cases": {original.id: "0" * 64}})
    elif change == "changed-ledger":
        ledger = project.storage.read_json(ledger_path)
        ledger["context"] = "0" * 64
        project.storage.write_json(ledger_path, ledger)
    elif change == "rejected-decision":
        decision = project.storage.read_json(decision_path)
        decision["decision"] = "rejected"
        project.storage.write_json(decision_path, decision)
    elif change == "changed-source":
        (source / "README.md").write_text("Owned changed baseline", encoding="utf-8")
    elif change == "stored-config":
        # The same Project instance retains its old config: persisted drift still counts.
        stored = project.storage.read_config()
        stored["navigation_timeout_ms"] += 1
        project.storage.write_config(stored)
        assert project.config.navigation_timeout_ms != stored["navigation_timeout_ms"]
    elif change == "data":
        project.storage.write_json("test-cases/test-data-v08.json", {"changed": "synthetic"})
    else:
        discovery = project.storage.read_json("discovery/workflow-map.json")
        element = discovery["pages"][0]["elements"][0]
        if change == "missing-locator":
            element["locators"] = []
        elif change == "ambiguous-locator":
            element["locators"][0]["count"] = 2
        else:
            contradictory = json.loads(json.dumps(element))
            contradictory["locators"][0]["value"] = "amount-other"
            discovery["pages"][0]["elements"].append(contradictory)
        project.storage.write_json("discovery/workflow-map.json", discovery)

    before, source_before = snapshot(project.root), snapshot(source)
    output = tmp_path / "must-not-export"

    def forbidden(*args, **kwargs):
        pytest.fail("Rejected maintenance reached subprocess execution")

    monkeypatch.setattr(testing.subprocess, "run", forbidden)
    for action in (
        lambda: reapprove(project, original),
        lambda: membership(project),
        lambda: compile_blueprint(project),
        lambda: FrameworkService(project, auth(project, "generate")).build(output),
        lambda: testing.generate(project, authorization=auth(project, "generate")),
        lambda: testing.run(project, authorization=auth(project, "execute")),
        lambda: FrameworkService(project, auth(project, "execute")).run(source),
    ):
        with pytest.raises(ValueError):
            action()
        assert snapshot(project.root) == before
        assert snapshot(source) == source_before
        assert not output.exists()


def test_applied_manual_revision_stays_immutable_and_later_drift_rejects(project, tmp_path):
    from test_v08_framework import manual_copy

    source, original = prepare(project, tmp_path)
    locator = drift(project)
    manual, page = manual_copy(source, tmp_path)
    service = MaintenanceService(project, auth(project, "review", "maintain"))
    proposal = service.propose(source, original.id, "EL-AMOUNT", locator, manual)
    service.review(source, proposal, "accepted", manual)
    before_apply = snapshot(manual)
    service.apply(source, proposal, manual)
    assert snapshot(manual) == before_apply
    reapprove(project, original)
    membership(project)
    original_source = snapshot(source)
    FrameworkService(project, auth(project, "generate")).build(tmp_path / "valid-manual-repair")
    assert snapshot(manual) == before_apply
    assert snapshot(source) == original_source
    page.write_text(page.read_text(encoding="utf-8") + "\n# Later owned edit\n", encoding="utf-8")
    before, manual_before = snapshot(project.root), snapshot(manual)
    with pytest.raises(ValueError):
        reapprove(project, original)
    assert snapshot(project.root) == before
    assert snapshot(manual) == manual_before
    assert snapshot(source) == original_source
