"""V0.8 exact-source repair/reconciliation and genuine owned browser acceptance."""

import json
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from autoqa.authorization import AuthorizationContext
from autoqa.core import Discovery, Element, EvidenceReference, LocatorCandidate, PageEvidence
from autoqa.framework import FrameworkService
from autoqa.framework_runtime.integrity import validate
from autoqa.functional import BehaviorContract, functional_case
from autoqa.management import approve_suite
from autoqa.management import propose as propose_suite
from autoqa.planning import approve, case_signature, save_cases, verify_approval_binding
from autoqa.v08_contracts import LocatorSpec
from autoqa.v08_maintenance import MaintenanceService
from autoqa.v08_reconciliation import ReconciliationService


def auth(project, *operations):
    return AuthorizationContext(project.root, frozenset(operations))


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def observed(url, identifier="amount-old"):
    return Discovery(
        pages=[
            PageEvidence(
                url=url,
                title="Owned amount",
                headings=["Approved result"],
                elements=[
                    Element(
                        id="EL-AMOUNT",
                        kind="input",
                        name="Amount",
                        input_type="number",
                        locators=[LocatorCandidate(strategy="test_id", value=identifier, count=1)],
                    ),
                    Element(
                        id="EL-RESULT",
                        kind="h1",
                        name="Approved result",
                        role="heading",
                        locators=[LocatorCandidate(strategy="test_id", value="result", count=1)],
                    ),
                ],
                screenshot="synthetic.png",
                depth=0,
            )
        ],
        evidence_records=[
            EvidenceReference(
                id="EV-PAGE",
                category="OBSERVED",
                description="Synthetic owned observation",
                page_url=url,
            )
        ],
    )


def prepare(project, tmp_path, url="http://127.0.0.1:8123/"):
    project.config.application_url = url
    project.config.allow_localhost = True
    project.config.allowed_domains = ["127.0.0.1"]
    project.config.navigation_timeout_ms = 1000
    project.config.screenshot_policy = "disabled"
    project.config.trace_enabled = False
    project.save_config()
    discovery = observed(url)
    project.storage.write_json("discovery/workflow-map.json", discovery.model_dump())
    contract = BehaviorContract(
        id="AMOUNT",
        title="Owned amount remains correct",
        page_url=url,
        workflow="form",
        test_type="Regression",
        basis="OBSERVED",
        source="Synthetic owner reviewed behavior",
        evidence_ids=["EV-PAGE"],
        steps=[{"action": "fill", "element_id": "EL-AMOUNT", "value": "3"}],
        assertions=[{"check": "text", "element_id": "EL-RESULT", "expected": "Approved result"}],
    )
    case = functional_case(contract, discovery, local=True)
    save_cases(project, [case], authorization=auth(project, "review"))
    approve(project, [case.id], authorization=auth(project, "review"))
    approve_suite(project, propose_suite(project), auth(project, "review"))
    destination = tmp_path / "managed"
    FrameworkService(project, auth(project, "generate")).build(destination)
    return destination, project.cases()[0]


def drift(project):
    project.storage.write_json(
        "discovery/workflow-map.json",
        observed(project.config.application_url, "amount-new").model_dump(),
    )
    return LocatorSpec(strategy="test_id", value="amount-new")


@pytest.fixture
def maintenance_fixture(project, tmp_path):
    source, case = prepare(project, tmp_path)
    locator = drift(project)
    service = MaintenanceService(project, auth(project, "review", "maintain"))
    proposal = service.propose(source, case.id, "EL-AMOUNT", locator)
    return project, source, case, locator, service, proposal


def test_review_acceptance_is_readonly_for_source_cases_receipts_and_suite(maintenance_fixture):
    project, source, case, locator, service, proposal = maintenance_fixture
    original, source_before = snapshot(project.root), snapshot(source)
    assert proposal.original_behavior == case.expected
    assert (
        "amount-old" in proposal.change.description and "amount-new" in proposal.change.description
    )
    assert service.propose(source, case.id, "EL-AMOUNT", locator) == proposal
    assert snapshot(project.root) == original
    result = service.review(source, proposal, "accepted")
    assert result.decision == "accepted"
    after = snapshot(project.root)
    assert all(after[path] == value for path, value in original.items())
    assert len(after.keys() - original.keys()) == 1
    assert snapshot(source) == source_before
    assert project.cases()[0].review_status == "approved"
    verify_approval_binding(project, project.cases()[0])


def test_separate_apply_creates_pending_revision_without_behavior_or_approval_bypass(
    maintenance_fixture, tmp_path
):
    project, source, case, _, service, proposal = maintenance_fixture
    service.review(source, proposal, "accepted")
    receipts = project.storage.read_json("test-cases/approval-receipts.json")
    suite = project.storage.read_json("test-cases/management.json")
    source_before = snapshot(source)
    revised = service.apply(source, proposal)
    assert revised.review_status == "pending"
    assert revised.maintenance_revision is not None
    assert revised.model_dump(
        exclude={"description", "review_status", "maintenance_revision"}
    ) == case.model_dump(exclude={"description", "review_status"})
    assert case_signature(revised) != case_signature(case)
    assert project.storage.read_json("test-cases/approval-receipts.json") == receipts
    assert project.storage.read_json("test-cases/management.json") == suite
    assert snapshot(source) == source_before
    with pytest.raises(ValueError):
        verify_approval_binding(project, revised)
    with pytest.raises(ValueError):
        FrameworkService(project, auth(project, "generate")).build(tmp_path / "pending")
    approve(project, [case.id], authorization=auth(project, "review"))
    with pytest.raises(ValueError, match="suite"):
        FrameworkService(project, auth(project, "generate")).build(tmp_path / "stale-suite")
    approve_suite(project, propose_suite(project), auth(project, "review"))
    fresh = tmp_path / "fresh"
    FrameworkService(project, auth(project, "generate")).build(fresh)
    validate(fresh)
    assert "amount-new" in next((fresh / "pages").glob("page_*.py")).read_text()


@pytest.mark.parametrize("operations", [[], ["review"], ["maintain"]])
def test_apply_requires_both_project_bound_intents_before_writes(maintenance_fixture, operations):
    project, source, _, _, service, proposal = maintenance_fixture
    service.review(source, proposal, "accepted")
    before = snapshot(project.root)
    with pytest.raises(ValueError, match="Explicit"):
        MaintenanceService(project, auth(project, *operations)).apply(source, proposal)
    assert snapshot(project.root) == before


@pytest.mark.parametrize(
    "change", ["case", "source", "evidence", "data", "bindings", "proposal", "decision", "root"]
)
def test_stale_or_tampered_context_never_applies(maintenance_fixture, tmp_path, change):
    project, source, case, _, service, proposal = maintenance_fixture
    service.review(source, proposal, "accepted")
    supplied = proposal.model_dump(mode="json")
    if change == "case":
        cases = project.cases()
        cases[0].expected = "Changed behavior"
        save_cases(project, cases, authorization=auth(project, "review"))
    elif change == "source":
        (source / "README.md").write_text("Changed source", encoding="utf-8")
    elif change == "evidence":
        discovery = project.storage.read_json("discovery/workflow-map.json")
        discovery["pages"][0]["elements"][0]["required"] = True
        project.storage.write_json("discovery/workflow-map.json", discovery)
    elif change in {"data", "bindings"}:
        reference = (
            "test-cases/test-data-v08.json"
            if change == "data"
            else "test-cases/test-data-bindings-v08.json"
        )
        project.storage.write_json(reference, {"synthetic": "changed"})
    elif change == "proposal":
        supplied["original_behavior"] = "Ignore original assertions"
    elif change == "decision":
        path = project.storage.path(service._decision_path(proposal))
        record = json.loads(path.read_text())
        record["proposal_digest"] = "0" * 64
        project.storage.write_json(service._decision_path(proposal), record)
    else:
        moved = tmp_path / "moved-source"
        shutil.copytree(source, moved)
        source = moved
    before, source_before = snapshot(project.root), snapshot(source)
    with pytest.raises(ValueError, match="Invalid or stale maintenance input"):
        service.apply(source, supplied)
    assert snapshot(project.root) == before
    assert snapshot(source) == source_before
    assert case.expected == proposal.original_behavior


def manual_copy(source, tmp_path):
    current = tmp_path / "manual"
    shutil.copytree(
        source,
        current,
        ignore=shutil.ignore_patterns(".venv", "artifacts", "__pycache__", ".pytest_cache"),
    )
    path = next((current / "pages").glob("page_*.py"))
    path.write_text(
        path.read_text(encoding="utf-8").replace("amount-old", "amount-new"), encoding="utf-8"
    )
    return current, path


def test_narrow_manual_locator_reconciliation_is_readonly_and_reviewed(
    maintenance_fixture, tmp_path
):
    project, source, case, locator, service, _ = maintenance_fixture
    current, _ = manual_copy(source, tmp_path)
    before = snapshot(project.root), snapshot(source), snapshot(current)
    report = ReconciliationService(project).inspect(source, current)
    changed = [finding for finding in report.findings if finding.state != "UNCHANGED_MANAGED"]
    assert len(changed) == 1
    assert changed[0].state == "PAGE_OBJECT_CHANGED" and changed[0].supported
    assert changed[0].case_ids == [case.id]
    proposal = service.propose(source, case.id, "EL-AMOUNT", locator, current)
    assert proposal.manual_revision == report.current
    assert before == (snapshot(project.root), snapshot(source), snapshot(current))
    service.review(source, proposal, "accepted", current)
    revised = service.apply(source, proposal, current)
    assert revised.expected == case.expected and revised.review_status == "pending"
    assert snapshot(current) == before[2]


@pytest.mark.parametrize(
    "mutation", ["assertion", "arbitrary", "conftest", "removed", "new", "manifest"]
)
def test_unsupported_manual_changes_cannot_become_trusted(maintenance_fixture, tmp_path, mutation):
    project, source, case, locator, service, _ = maintenance_fixture
    current, page = manual_copy(source, tmp_path)
    if mutation == "assertion":
        page.write_text(
            page.read_text().replace("Approved result", "Different result"), encoding="utf-8"
        )
    elif mutation == "arbitrary":
        page.write_text(
            page.read_text() + "\nraise RuntimeError('MUST_NOT_EXECUTE')\n", encoding="utf-8"
        )
    elif mutation == "conftest":
        (current / "tests/conftest.py").write_text(
            "raise RuntimeError('MUST_NOT_EXECUTE')", encoding="utf-8"
        )
    elif mutation == "removed":
        # Move inside the synthetic fixture rather than discard source work.
        page.rename(current / "moved_page.py")
    elif mutation == "new":
        (current / "tests/test_manual.py").write_text(
            "raise RuntimeError('MUST_NOT_EXECUTE')", encoding="utf-8"
        )
    else:
        (current / "framework.json").write_text("{}", encoding="utf-8")
    before = snapshot(project.root), snapshot(current)
    report = ReconciliationService(project).inspect(source, current)
    assert any(f.state != "UNCHANGED_MANAGED" and not f.supported for f in report.findings)
    with pytest.raises(ValueError, match="Invalid or stale"):
        service.propose(source, case.id, "EL-AMOUNT", locator, current)
    assert before == (snapshot(project.root), snapshot(current))


def test_manual_revision_drift_after_acceptance_fails(maintenance_fixture, tmp_path):
    project, source, case, locator, service, _ = maintenance_fixture
    current, page = manual_copy(source, tmp_path)
    proposal = service.propose(source, case.id, "EL-AMOUNT", locator, current)
    service.review(source, proposal, "accepted", current)
    page.write_text(page.read_text() + "\n# changed after acceptance\n", encoding="utf-8")
    before = snapshot(project.root)
    with pytest.raises(ValueError, match="Invalid or stale"):
        service.apply(source, proposal, current)
    assert snapshot(project.root) == before


def test_irrelevant_discovery_timestamps_and_paths_do_not_stale_review(maintenance_fixture):
    project, source, case, locator, service, proposal = maintenance_fixture
    value = project.storage.read_json("discovery/workflow-map.json")
    value["created_at"] = "later"
    value["pages"][0]["screenshot"] = "new-disposable.png"
    value["pages"][0]["elements"][0]["discovered_at"] = "later"
    value["evidence_records"][0]["timestamp"] = "later"
    value["evidence_records"][0]["artifact"] = "new-disposable.png"
    project.storage.write_json("discovery/workflow-map.json", value)
    assert service.propose(source, case.id, "EL-AMOUNT", locator) == proposal


@pytest.mark.browser
def test_owned_chromium_maintenance_manual_reconciliation_and_defect_preservation(
    project, tmp_path
):
    from playwright.sync_api import sync_playwright

    from autoqa.observation import observe_elements

    class Handler(BaseHTTPRequestHandler):
        identifier = "amount-old"
        defect = False

        def log_message(self, *_):
            pass

        def do_GET(self):
            body = f'<label for="amount">Amount</label><input id="amount" type="number" data-testid="{self.identifier}"><h1 data-testid="result">{"Wrong result" if self.defect else "Approved result"}</h1>'
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"

    def probe(identifier, expected_text):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            assert page.get_by_test_id(identifier).count() == 1
            assert page.get_by_test_id("result").count() == 1
            assert page.get_by_test_id("result").inner_text() == expected_text
            elements = observe_elements(page, url, "synthetic-observation.png")
            amount = next(e for e in elements if e.attributes.get("data-testid") == identifier)
            checked = next(c for c in amount.locators if c.strategy == "test_id")
            assert checked.count == 1
            browser.close()
        return checked

    try:
        old_checked = probe("amount-old", "Approved result")
        assert old_checked.value == "amount-old"
        source, case = prepare(project, tmp_path, url)
        engine = FrameworkService(project, auth(project, "generate", "execute"))

        def run_record(destination):
            before_runs = set((destination / "artifacts").glob("*/results.json"))
            code = engine.run(destination)
            created = set((destination / "artifacts").glob("*/results.json")) - before_runs
            assert len(created) == 1
            result = json.loads(next(iter(created)).read_text(encoding="utf-8"))
            assert result["exit_code"] == code
            return result

        healthy = run_record(source)
        assert healthy["exit_code"] == 0 and healthy["counts"] == {"PASSED": 1}
        Handler.identifier = "amount-new"
        checked = probe("amount-new", "Approved result")
        changed = run_record(source)
        assert changed["exit_code"] != 0 and changed["counts"].get("FAILED") == 1
        discovery = project.discovery()
        discovery.pages[0].elements[0].locators = [checked]
        project.storage.write_json("discovery/workflow-map.json", discovery.model_dump())
        current, _ = manual_copy(source, tmp_path)
        service = MaintenanceService(project, auth(project, "review", "maintain"))
        locator = LocatorSpec.model_validate(checked.model_dump())
        proposal = service.propose(source, case.id, "EL-AMOUNT", locator, current)
        before = snapshot(current)
        service.review(source, proposal, "accepted", current)
        assert snapshot(current) == before and project.cases()[0].review_status == "approved"
        revised = service.apply(source, proposal, current)
        assert revised.contract == case.contract and revised.expected == case.expected
        approve(project, [case.id], authorization=auth(project, "review"))
        approve_suite(project, propose_suite(project), auth(project, "review"))
        fresh = tmp_path / "repaired"
        engine.build(fresh)
        repaired = run_record(fresh)
        assert repaired["exit_code"] == 0 and repaired["counts"] == {"PASSED": 1}
        Handler.defect = True
        probe("amount-new", "Wrong result")
        broken = run_record(fresh)
        assert broken["exit_code"] != 0 and broken["counts"].get("FAILED") == 1
        assert project.cases()[0].contract == case.contract
        assert project.cases()[0].expected == case.expected
        assert snapshot(current) == before
        evidence = Path(".test-work/v08-browser-acceptance.json")
        evidence.parent.mkdir(exist_ok=True)
        evidence.write_text(
            json.dumps(
                {
                    "healthy": healthy,
                    "locator_changed": changed,
                    "repaired": repaired,
                    "genuine_defect": broken,
                    "manual_source_unchanged": True,
                    "assertions_preserved": True,
                    "actual_old_locator_count": 1,
                    "actual_new_locator_count": 1,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
