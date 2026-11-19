"""Reproducible standard-CLI acceptance run against the independent owned application."""

import argparse
import json
import shutil
import subprocess
import sys
import threading
from collections import Counter
from http.server import ThreadingHTTPServer
from pathlib import Path

from autoqa.core import Project, load_json, save_json
from autoqa.independent_demo import SupplyHandler
from examples.independent_contracts import reviewed_contracts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="independent-v02")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    project_path = Path("projects") / args.name
    if project_path.exists():
        raise SystemExit(
            "Use a new project name; existing evidence is never overwritten by this harness."
        )

    # The fixture is owned; fault injection changes only this application instance.
    class Handler(SupplyHandler):
        regression = ""

    def cli(*arguments, expected=0):
        result = subprocess.run(
            [sys.executable, "-m", "autoqa", *arguments],
            shell=False,
            text=True,
            capture_output=True,
            timeout=180,
        )
        print(result.stdout)
        if result.returncode != expected:
            print(result.stderr)
            raise RuntimeError(f"CLI {arguments[0]} exit {result.returncode}; expected {expected}")

    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            cli("init", args.name)
            target = ("--project", str(project_path))
            cli(
                "explore",
                "--url",
                f"http://127.0.0.1:{server.server_port}/inventory",
                "--authorized",
                "--allow-localhost",
                *target,
            )
            project = Project(project_path)
            discovery = project.discovery()
            contracts = reviewed_contracts(discovery)
            path = project.root / "test-cases/owned-fixture-requirements.json"
            save_json(path, contracts)
            cli("plan", "--requirements", str(path), *target)
            cases = project.cases()
            ids = [c.id for c in cases if c.kind == "functional"]
            ids += [next(c.id for c in cases if c.kind == "link" and c.target == "Moss Journal")]
            flags = [value for test_id in ids for value in ("--approve", test_id)]
            cli("plan", *flags, *target)
            cli("generate", "--approved", *target)
            runs = {}
            for stage, regression, exit_code in [
                ("healthy", "", 0),
                ("regression", "search", 1),
                ("restored", "", 0),
            ]:
                Handler.regression = regression
                cli("run", *target, expected=exit_code)
                cli("diagnose", *target)
                cli("report", "--format", "html", *target)
                cli("report", "--format", "json", *target)
                result = load_json(project.root / "reports/latest-run.json")
                artifact = project.root / result["artifact_dir"]
                html = (project.root / "reports/qa-report.html").read_text(encoding="utf-8")
                (artifact / "qa-report.html").write_text(
                    html.replace('href="../', 'href="../../'), encoding="utf-8"
                )
                shutil.copy2(project.root / "reports/qa-report.json", artifact / "qa-report.json")
                runs[stage] = {
                    "run_id": result["run_id"],
                    "exit_code": result["exit_code"],
                    "counts": dict(Counter(r["status"] for r in result["records"])),
                    "duration": result["duration"],
                    "artifact_dir": result["artifact_dir"],
                    "failed_ids": [r["id"] for r in result["records"] if r["status"] == "FAILED"],
                }
            assert runs["healthy"]["counts"] == {"PASSED": 9}
            assert runs["regression"]["counts"] == {"PASSED": 7, "FAILED": 2}
            assert runs["restored"]["counts"] == {"PASSED": 9}
            known_workflows = {"search", "filter", "sorting", "form", "product"}
            found = {w.kind for w in discovery.workflows} & known_workflows
            benchmark = {
                "project": str(project_path),
                "pages": len(discovery.pages),
                "workflows": len(discovery.workflows),
                "semantic_elements": sum(len(p.elements) for p in discovery.pages),
                "controls": sum(
                    sum(
                        e.kind in {"a", "button", "input", "select", "textarea"} for e in p.elements
                    )
                    for p in discovery.pages
                ),
                "proposed": len(cases),
                "approved": len(ids),
                "generated": len(ids),
                "workflow_baseline": sorted(known_workflows),
                "workflow_types_found": sorted(found),
                "discovery_recall": {"found": len(found), "known": len(known_workflows)},
                "scenario_review": {
                    "reviewed_fixture_contracts": len(contracts),
                    "valid_fixture_contracts": 8,
                    "all_proposals_precision": "Not measured; inferred manual scenarios remain unverified",
                },
                "manual_intervention": {
                    "reviewed_requirement_files": 1,
                    "approved_scenarios": len(ids),
                    "generated_selector_edits": 0,
                    "assertion_weakening": 0,
                },
                "runs": runs,
                "report": str(project_path / "reports/qa-report.html"),
            }
            save_json(Path("docs/v02-benchmarks.json"), benchmark)
            print(json.dumps(benchmark, indent=2))
        finally:
            server.shutdown()
            thread.join(timeout=3)


if __name__ == "__main__":
    main()
