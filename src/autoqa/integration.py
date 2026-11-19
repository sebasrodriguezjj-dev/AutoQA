"""Reviewable CI generation with immutable, officially resolved action revisions."""

import re
from pathlib import Path

from autoqa.core import Project, load_json


def integrate(project: Project) -> str:
    manifest = load_json(project.root / "automation/manifest.json")
    if not manifest["cases"]:
        raise ValueError("Generate an approved suite before integrating.")
    # Require repository-relative paths; workflow content must never contain absolute host paths.
    workspace = Path.cwd().resolve()
    if not (workspace / "uv.lock").is_file() or not (workspace / "pyproject.toml").is_file():
        raise ValueError(
            "Run integrate from the AutoQA repository containing pyproject.toml and uv.lock."
        )
    try:
        relative = project.root.relative_to(workspace).as_posix()
    except ValueError:
        raise ValueError("Project must be inside the QA repository for CI generation.") from None
    if not re.fullmatch(r"[A-Za-z0-9_/-]+", relative):
        raise ValueError(
            "CI project path must contain only letters, digits, underscores, hyphens or slashes."
        )
    if not re.fullmatch(r"[A-Za-z0-9_-]+", project.root.name):
        raise ValueError("Unsafe project directory name for a workflow filename.")
    destination = workspace / ".github/workflows" / f"autoqa-{project.root.name}.yml"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError(f"Workflow already exists; review it manually: {destination}")
    workflow = """name: AutoQA approved UI suite
on:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  qa:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
        with:
          version: "0.13.9"
      - name: Require provisioned project and authorized target
        env:
          AUTOQA_BASE_URL: ${{ vars.AUTOQA_BASE_URL }}
        run: |
          test -n "$AUTOQA_BASE_URL" || { echo "::error::Configure AUTOQA_BASE_URL before dispatch"; exit 1; }
          for file in config.yaml discovery/workflow-map.json test-cases/test-matrix.json automation/manifest.json automation/conftest.py automation/test_observed.py; do
            test -f "PROJECT_PATH/$file" || { echo "::error::Missing provisioned project file: $file"; exit 1; }
          done
      - run: uv sync --locked
      - run: uv run playwright install --with-deps chromium
      - name: Run approved tests against the configured staging application
        env:
          AUTOQA_BASE_URL: ${{ vars.AUTOQA_BASE_URL }}
        run: uv run autoqa run --project PROJECT_PATH
      - name: Render report even when tests fail
        if: always()
        run: uv run autoqa report --project PROJECT_PATH --format html
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        if: always()
        with:
          name: autoqa-results
          path: |
            PROJECT_PATH/reports/
            PROJECT_PATH/artifacts/
          retention-days: 7
"""
    workflow = workflow.replace("PROJECT_PATH", relative)
    destination.write_text(workflow, encoding="utf-8")
    project.audit("Generated reviewable GitHub Actions workflow locally")
    return str(destination)
