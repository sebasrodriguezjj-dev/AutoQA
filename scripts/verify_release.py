"""Reusable local/CI release gates. Every failed command raises and exits nonzero."""

import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import threading
import tomllib
import zipfile
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, timeout=600):
    print("GATE:", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, check=True, timeout=timeout)


def metadata():
    from autoqa import __version__

    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    assert next(p["version"] for p in lock["package"] if p["name"] == "autoqa-agent") == version
    assert __version__ == importlib.metadata.version("autoqa-agent") == version
    print("Package/import/lock/installed version:", version, flush=True)
    return version


@contextmanager
def owned_endpoint():
    """Synthetic loopback only; always close the listener and join its thread."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            parsed = urlsplit(self.path)
            self.send_response(200 if parsed.path == "/health" else 404)
            self.end_headers()
            sample = parse_qs(parsed.query).get("sample", [""])[0]
            self.wfile.write(json.dumps({"healthy": True, "sample": sample}).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def planning_smoke(python, output, project, manifest):
    """Exercise installed V0.7 adapters without changing reviewed executable cases."""

    def snapshot():
        return {
            p.relative_to(project).as_posix(): p.read_bytes()
            for p in project.rglob("*")
            if p.is_file()
        }

    def cli(*args):
        result = subprocess.run(
            [str(python), "-m", "autoqa", *map(str, args), "--project", str(project)],
            cwd=output,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=30,
        )
        return json.loads(result.stdout)

    source = {
        "id": "SRC-PACKAGE",
        "reference": "Reviewed synthetic fixture",
        "description": "Owned package acceptance",
    }
    specification = {
        "sources": [source],
        "requirements": [
            {
                "id": "REQ-HEALTH",
                "title": "Healthy synthetic API",
                "description": "Reviewed fixture health contract",
                "source_id": source["id"],
                "review_status": "approved",
                "kind": "API",
                "expected_behavior": "The reviewed synthetic healthy response matches",
            },
            {
                "id": "REQ-MISSING",
                "title": "Unknown owned UI flow",
                "description": "No scenario or verified expected behavior supplied",
                "source_id": source["id"],
                "kind": "UI",
            },
        ],
        "mappings": [
            {
                "requirement_id": "REQ-HEALTH",
                "case_id": "TC-API-PACKAGE",
                "case_signature": manifest["cases"]["TC-API-PACKAGE"],
                "review_status": "approved",
                "rationale": "Explicit fixture-owner mapping",
            }
        ],
    }
    spec = output / "requirements-v07.json"
    spec.write_text(json.dumps(specification), encoding="utf-8")
    before = snapshot()
    plan = cli("intelligent-plan", "--requirements", spec)
    coverage = cli("coverage-report", "--requirements", spec)
    assert snapshot() == before, "Analysis and coverage must not write project files"
    assert plan["execution_coverage"] == coverage["execution_coverage"] == "NOT_ASSESSED"
    assert plan["coverage_scope"] == "SUPPLIED_REQUIREMENTS_ONLY"
    assert plan["summary"]["confirmed_mapped_requirements"] == 1
    assert plan["summary"]["missing_requirements"] == 1
    cli("requirements-import", spec)
    stored = cli("intelligent-plan")
    assert stored["id"] == plan["id"], "Explicit import does not invent a different plan"
    proposal = stored["proposals"][0]["id"]
    reviewed = cli("plan-review", stored["id"], "--accept", proposal)
    assert (
        next(p for p in reviewed["proposals"] if p["id"] == proposal)["review_status"] == "accepted"
    )
    assert reviewed["summary"] == stored["summary"], "Planning disposition is not test approval"
    assert all(snapshot()[name] == data for name, data in before.items())
    after_review = snapshot()
    rejected = subprocess.run(
        [
            str(python),
            "-m",
            "autoqa",
            "plan-review",
            "PLAN-" + "0" * 64,
            "--accept",
            proposal,
            "--project",
            str(project),
        ],
        cwd=output,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert rejected.returncode != 0 and snapshot() == after_review
    print(
        "Installed V0.7 planning/read-only coverage/import/snapshot-bound review gates passed",
        flush=True,
    )


def maintenance_smoke(python, output, project, export):
    """Exercise actual installed V0.8 workflows, preserving existing package checks."""

    def cli(*args, selected=project, structured=True):
        result = subprocess.run(
            [str(python), "-m", "autoqa", *map(str, args), "--project", str(selected)],
            cwd=output,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=60,
        )
        return json.loads(result.stdout) if structured else result.stdout

    def write(name, value):
        path = output / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def snapshot(root):
        return {
            p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*")
            if p.is_file() and ".venv" not in p.relative_to(root).parts
        }

    first_run = next((export / "artifacts").glob("*/results.json"))
    before = snapshot(project)
    diagnosis = cli("diagnose-run", first_run)
    assert any(f["category"] == "HEALTHY_RECORDED_EXECUTION" for f in diagnosis["findings"])
    obj = {
        "id": "API-HEALTH",
        "kind": "api_contract",
        "source_location": "api.json",
        "semantics": {"path": "/health"},
        "case_ids": ["TC-API-PACKAGE"],
    }
    old = write("impact-before.json", {"project_id": project.name, "objects": [obj]})
    new = write(
        "impact-after.json",
        {"project_id": project.name, "objects": [obj | {"semantics": {"path": "/v2/health"}}]},
    )
    impact = cli("impact-review", old, new)
    assert impact["findings"][0]["potential_case_ids"] == ["TC-API-PACKAGE"]
    assert impact["findings"][0]["verified_runtime_impact"] is False
    assert snapshot(project) == before
    data = write(
        "data-v08.json",
        {
            "project_id": project.name,
            "definitions": [
                {
                    "alias": "datasets.health",
                    "kind": "value",
                    "environments": ["local"],
                    "sensitivity": "SYNTHETIC",
                    "values": [{"sample": f"owned-alias-consumed-{i}"} for i in range(3)],
                }
            ],
        },
    )
    cli("test-data", "inspect", "--input", data)
    cli("test-data", "import", data)
    cli("test-data", "inspect")
    assert cli("test-data", "validate", "datasets.health", "--environment", "local")["valid"]
    pending = cli(
        "test-data",
        "bind",
        "datasets.health",
        "TC-API-PACKAGE",
        "--environment",
        "local",
        "--authorized",
    )
    assert pending["review_status"] == "pending"
    assert pending["contract"]["data"]["rows"] == [
        {"sample": f"owned-alias-consumed-{i}"} for i in range(3)
    ]
    cli("plan", "--approve", "TC-API-PACKAGE", structured=False)
    suite = write("suite-v08.json", cli("suite-propose"))
    cli("suite-approve", suite, structured=False)
    fresh = output / "data-framework"
    cli("build-framework", fresh, "--approved", structured=False)
    run("uv", "sync", cwd=fresh)
    independent = fresh / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(
        independent,
        "-c",
        "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
        cwd=fresh,
    )
    run(independent, "-m", "qa_runtime.runner", "run", "--all", cwd=fresh)
    consumed = json.loads(
        next((fresh / "artifacts").glob("*/results.json")).read_text(encoding="utf-8")
    )
    assert consumed["exit_code"] == 0 and consumed["counts"] == {"PASSED": 3}
    # The API assertion checks the echoed alias value; this is actual data consumption.
    assert len(consumed["steps"]) == 6
    # Installed H05: historical evidence, not the current project's mutable cases,
    # establishes complete scope. Remove matching operations and conceal trivial counts.
    complete = write("h05-installed-complete.json", consumed)
    assert any(
        f["category"] == "HEALTHY_RECORDED_EXECUTION"
        for f in cli("diagnose-run", complete)["findings"]
    )
    for index in range(3):
        altered = json.loads(json.dumps(consumed))
        missing = f"TC-API-PACKAGE--row-{index}"
        altered["records"] = [r for r in altered["records"] if r["id"] != missing]
        altered["steps"] = [s for s in altered["steps"] if s["test_id"] != missing]
        altered["counts"] = {"PASSED": 2}
        path = write(f"h05-installed-missing-{index}.json", altered)
        assert not any(
            f["category"] == "HEALTHY_RECORDED_EXECUTION"
            for f in cli("diagnose-run", path)["findings"]
        )
    altered = json.loads(json.dumps(consumed))
    altered["steps"].pop()
    path = write("h05-installed-missing-operation.json", altered)
    assert not any(
        f["category"] == "HEALTHY_RECORDED_EXECUTION" for f in cli("diagnose-run", path)["findings"]
    )

    setup = subprocess.run(
        [
            str(python),
            str(ROOT / "examples/validate_v08_maintenance.py"),
            str(output / "ui-maintenance"),
        ],
        cwd=output,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=90,
    )
    fixture = json.loads(setup.stdout)
    ui = Path(fixture["project"])
    source, manual = Path(fixture["source"]), Path(fixture["manual_source"])
    originals = snapshot(source), snapshot(manual)
    reconciliation = cli("reconcile-source", source, manual, selected=ui)
    assert any(f["supported"] for f in reconciliation["findings"])
    proposal = cli(
        "maintenance",
        "propose",
        source,
        fixture["case_id"],
        fixture["element_id"],
        fixture["locator"],
        "--manual-source",
        manual,
        selected=ui,
    )
    proposal_file = write("maintenance-proposal.json", proposal)
    case_before = (ui / "test-cases/test-matrix.json").read_bytes()
    decision = cli(
        "maintenance",
        "review",
        source,
        proposal_file,
        "--decision",
        "accepted",
        "--manual-source",
        manual,
        selected=ui,
    )
    assert decision["decision"] == "accepted"
    assert (ui / "test-cases/test-matrix.json").read_bytes() == case_before
    revised = cli(
        "maintenance",
        "apply",
        source,
        proposal_file,
        "--authorized",
        "--manual-source",
        manual,
        selected=ui,
    )
    assert (
        revised["review_status"] == "pending"
        and revised["expected"] == proposal["original_behavior"]
    )
    assert (snapshot(source), snapshot(manual)) == originals
    assert revised["maintenance_revision"]
    discovery_path = ui / "discovery/workflow-map.json"
    reviewed_discovery = discovery_path.read_bytes()
    changed = json.loads(reviewed_discovery)
    element = next(
        e for page in changed["pages"] for e in page["elements"] if e["id"] == fixture["element_id"]
    )
    element["locators"] = [{"strategy": "test_id", "value": "amount-other", "name": "", "count": 1}]
    discovery_path.write_text(json.dumps(changed), encoding="utf-8")
    before_rejection = snapshot(ui)
    rejected = subprocess.run(
        [
            str(python),
            "-m",
            "autoqa",
            "plan",
            "--approve",
            fixture["case_id"],
            "--project",
            str(ui),
        ],
        cwd=output,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert rejected.returncode != 0 and snapshot(ui) == before_rejection
    assert (snapshot(source), snapshot(manual)) == originals
    discovery_path.write_bytes(reviewed_discovery)
    cli("plan", "--approve", fixture["case_id"], selected=ui, structured=False)
    ui_suite = write("ui-suite-v08.json", cli("suite-propose", selected=ui))
    cli("suite-approve", ui_suite, selected=ui, structured=False)
    trusted = output / "ui-repaired-fresh"
    cli("build-framework", trusted, "--approved", selected=ui, structured=False)
    run(python, "-m", "autoqa", "validate-framework", trusted, cwd=output)
    page_source = "\n".join(p.read_text(encoding="utf-8") for p in (trusted / "pages").glob("*.py"))
    assert "amount-new" in page_source and "amount-other" not in page_source
    discovery_path.write_text(json.dumps(changed), encoding="utf-8")
    before_rejection = snapshot(ui)
    rejected_destination = output / "h04-unreviewed-export"
    rejected = subprocess.run(
        [
            str(python),
            "-m",
            "autoqa",
            "build-framework",
            str(rejected_destination),
            "--approved",
            "--project",
            str(ui),
        ],
        cwd=output,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert rejected.returncode != 0 and not rejected_destination.exists()
    assert snapshot(ui) == before_rejection
    assert (snapshot(source), snapshot(manual)) == originals
    discovery_path.write_bytes(reviewed_discovery)
    print(
        "Installed V0.8 diagnosis/impact/data consumption/reconciliation/review/apply/fresh export gates passed",
        flush=True,
    )


def package():
    version = metadata()
    work = ROOT / ".test-work"
    work.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="release-gate-", dir=work))
    dist = output / "dist"
    run("uv", "build", "--out-dir", dist)
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1 and len(list(dist.glob("*.tar.gz"))) == 1
    for archive in dist.iterdir():
        if archive.suffix == ".whl":
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
        elif archive.name.endswith(".tar.gz"):
            with tarfile.open(archive) as bundle:
                names = bundle.getnames()
        else:
            continue
        assert not any(
            set(name.split("/")) & {"projects", ".test-work", ".venv", ".env", "artifacts"}
            for name in names
        )
    env = output / "installed"
    run("uv", "venv", env, "--python", sys.executable)
    python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    requirements = output / "runtime.txt"
    run(
        "uv",
        "export",
        "--locked",
        "--no-dev",
        "--no-emit-project",
        "--no-hashes",
        "--output-file",
        requirements,
    )
    run(
        "uv",
        "pip",
        "install",
        "--python",
        python,
        "-r",
        requirements,
        wheels[0],
        "ruff==" + importlib.metadata.version("ruff"),
    )
    run(
        python,
        "-c",
        f"import autoqa, importlib.metadata; assert autoqa.__version__ == importlib.metadata.version('autoqa-agent') == {version!r}; assert 'site-packages' in autoqa.__file__; print(autoqa.__version__)",
        cwd=output,
    )
    run(python, "-m", "autoqa", "--help", cwd=output)
    with owned_endpoint() as origin:
        # Only this owned, synthetic endpoint is contacted during package acceptance.
        payload = [
            {
                "id": "TC-API-PACKAGE",
                "title": "Synthetic package smoke",
                "request": {"path": "/health", "query": {"sample": "${sample}"}},
                "expect": {"status": 200, "json_values": {"healthy": True, "sample": "${sample}"}},
                "data": {"name": "original", "rows": [{"sample": "baseline"}]},
                "environments": [{"name": "local", "origin": origin, "allow_localhost": True}],
                "environment": "local",
            }
        ]
        spec = output / "api.json"
        spec.write_text(json.dumps(payload), encoding="utf-8")
        parent = output / "sources"
        run(python, "-m", "autoqa", "init", "synthetic", "--parent", parent, cwd=output)
        project = parent / "synthetic"
        run(python, "-m", "autoqa", "plan-api", spec, "--project", project, cwd=output)
        run(
            python,
            "-m",
            "autoqa",
            "plan",
            "--approve",
            "TC-API-PACKAGE",
            "--project",
            project,
            cwd=output,
        )
        proposed = subprocess.run(
            [str(python), "-m", "autoqa", "suite-propose", "--project", str(project)],
            cwd=output,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        inventory = output / "suite.json"
        inventory.write_text(proposed.stdout, encoding="utf-8")
        run(python, "-m", "autoqa", "suite-approve", inventory, "--project", project, cwd=output)
        export = output / "framework"
        run(
            python,
            "-m",
            "autoqa",
            "build-framework",
            export,
            "--approved",
            "--project",
            project,
            cwd=output,
        )
        run(python, "-m", "autoqa", "validate-framework", export, cwd=output)
        manifest = json.loads((export / "framework.json").read_text())
        assert (
            manifest["version"]
            == tomllib.loads((export / "pyproject.toml").read_text())["project"]["version"]
            == version
        )
        planning_smoke(python, output, project, manifest)
        run("uv", "sync", cwd=export)
        independent = export / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run(
            independent,
            "-c",
            "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
            cwd=export,
        )
        run(independent, "-m", "qa_runtime.runner", "validate", cwd=export)
        run(independent, "-m", "qa_runtime.runner", "collect", cwd=export)
        for selection in [["--case", "TC-API-PACKAGE"], ["--pack", "API"], ["--all"]]:
            run(independent, "-m", "qa_runtime.runner", "run", *selection, cwd=export)
        results = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in (export / "artifacts").glob("*/results.json")
        ]
        assert len(results) == 3
        for result in results:
            assert result["exit_code"] == 0 and result["counts"] == {"PASSED": 1}
            assert len(result["steps"]) == 2
            assert result["accounting"]["selected"] == result["accounting"]["passed"] == 1
        assert {r["selection_mode"] for r in results} == {"case", "pack", "all"}
        maintenance_smoke(python, output, project, export)
        print(
            "Package/install/approved export/standalone/single/pack/full gates passed:",
            output,
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["all", "checks", "package"], default="all")
    args = parser.parse_args()
    if args.phase in {"all", "checks"}:
        metadata()
        run(sys.executable, "-m", "ruff", "check", "src", "tests", "scripts")
        run(sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "scripts")
        run("uv", "lock", "--check")
        run(
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-m",
            "not browser",
            "--ignore=tests/test_live_ai.py",
            "-q",
        )
    if args.phase in {"all", "package"}:
        package()


if __name__ == "__main__":
    main()
