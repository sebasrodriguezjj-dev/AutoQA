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
            self.send_response(200 if self.path == "/health" else 404)
            self.end_headers()
            self.wfile.write(b'{"healthy": true}')

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
                "request": {"path": "/health"},
                "expect": {"status": 200},
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
