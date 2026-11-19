import copy
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from autoqa.core import Project, load_json, save_json
from autoqa.exploration import explore
from autoqa.functional import BehaviorContract, validate_contract
from autoqa.independent_demo import SupplyHandler
from autoqa.planning import approve, plan, reject
from autoqa.reporting import diagnose, report
from autoqa.testing import generate, run
from examples.independent_contracts import reviewed_contracts


@pytest.fixture
def independent_server():
    class Handler(SupplyHandler):
        regression = ""

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/inventory", Handler
        finally:
            server.shutdown()
            thread.join(timeout=3)


@pytest.fixture
def functional_project(project, independent_server):
    url, handler = independent_server
    project.config.allow_localhost = True
    project.config.request_interval_ms = 0
    discovery = explore(project, url)
    path = project.root / "test-cases/reviewed-demo-requirements.json"
    save_json(path, reviewed_contracts(discovery))
    return project, discovery, path, handler


@pytest.mark.browser
def test_functional_discovery_and_contract_security(functional_project):
    project, discovery, path, _ = functional_project
    kinds = {w.kind for w in discovery.workflows}
    assert {"search", "filter", "sorting", "form", "product"} <= kinds
    assert all(e.discovered_at and e.id and e.evidence for p in discovery.pages for e in p.elements)
    assert any(e.required and e.input_type == "email" for p in discovery.pages for e in p.elements)
    assert any(e.options for p in discovery.pages for e in p.elements)
    pending = plan(project)
    assert any(c.test_type == "Negative" and not c.feasible for c in pending)
    cases = plan(project, path)
    functional = [c for c in cases if c.kind == "functional"]
    assert len(functional) == 8
    assert {c.test_type for c in functional} >= {"Positive", "Negative", "Boundary"}
    assert all(c.review_status == "pending" for c in functional)
    approve(project, [functional[0].id])
    assert (
        plan(Project(project.root))[
            next(i for i, c in enumerate(cases) if c.id == functional[0].id)
        ].review_status
        == "approved"
    )
    reject(project, [functional[-1].id])
    assert next(c for c in plan(project) if c.id == functional[-1].id).review_status == "rejected"
    raw = load_json(path)[0]
    bad = copy.deepcopy(raw)
    bad["evidence_ids"] = ["unknown-evidence"]
    with pytest.raises(ValueError, match="unknown"):
        validate_contract(BehaviorContract.model_validate(bad), discovery, local=True)
    bad = copy.deepcopy(raw)
    bad["steps"][0]["element_id"] = "unknown-element"
    with pytest.raises(ValueError):
        validate_contract(BehaviorContract.model_validate(bad), discovery, local=True)
    bad = load_json(path)[-1]
    with pytest.raises(ValueError, match="controlled-local"):
        validate_contract(BehaviorContract.model_validate(bad), discovery, local=False)


@pytest.mark.browser
def test_independent_functional_pass_defect_restore(functional_project):
    project, discovery, path, handler = functional_project
    cases = plan(project, path)
    ids = [c.id for c in cases if c.kind == "functional"]
    product = next(c for c in cases if c.kind == "link" and c.target == "Moss Journal")
    ids.append(product.id)
    approve(project, ids)
    assert set(generate(project)) == set(ids)
    source = (project.root / "automation/test_observed.py").read_text()
    assert "to_have_text" in source and "to_have_count(0)" in source
    assert "typeMismatch" in source and "sorted(" in source
    assert "sleep(" not in source and ".first" not in source.split("def test_TC_F_")[1]
    healthy = run(project)
    assert healthy["exit_code"] == 0, (
        project.root / healthy["artifact_dir"] / "pytest.log"
    ).read_text()
    assert len(healthy["records"]) == 9
    handler.regression = "search"
    broken = run(project)
    assert broken["exit_code"] == 1
    failures = [r for r in broken["records"] if r["status"] == "FAILED"]
    assert {r["id"] for r in failures} == {"TC-F-search-found", "TC-F-search-empty"}
    findings = diagnose(project)
    assert findings and all(f["human_review_required"] for f in findings)
    failure_report = Path(report(project, "html"))
    assert "FAILED: 2" in failure_report.read_text()
    handler.regression = ""
    restored = run(project)
    assert restored["exit_code"] == 0
    assert all(r["status"] == "PASSED" for r in restored["records"])
    assert Path(report(project, "html")).is_file()
    payload = json.loads(Path(report(project, "json")).read_text())
    assert payload["counts"] == {"PASSED": 9}
