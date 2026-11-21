# CLI reference

Use `python -m uv run autoqa COMMAND --help` for exact options. All project commands accept `--project PATH`. Run from a project directory or use the registry's active project when invoking from the QA repository root.

| Command | Notes |
| --- | --- |
| `init NAME --parent DIRECTORY` | Default parent: projects; no overwrites; Windows-safe project names |
| `demo --host 127.0.0.1 --port 8000` | Blocks until Ctrl+C; local server intended only for testing |
| `demo --variant independent --port 8001` | Independent owned Supply Lab fixture |
| `explore --url URL --authorized` | Explicit authorization required; strict initial origin scope |
| `explore --url URL --authorized --allow-localhost` | Enables loopback only; does not permit private LAN/metadata addresses |
| `explore --repo PATH --authorized` | Existing local path only; no scripts or dependency installation |
| `explore --repo PATH --url URL --authorized` | Hybrid UI/source inspection and inferred path matches |
| `plan` | Rebuild matrix from latest discovery; preserve identical approvals |
| `plan --approve TC-001 --approve TC-003` | Persist selected approvals; all IDs validated before changes |
| `plan --requirements FILE` | Import a reviewed JSON behavior-contract array; proposals remain pending |
| `plan --reject ID` | Persist rejection without deleting the scenario |
| `plan --ai` | Send reduced workflow evidence to configured cloud provider; saves review-only suggestions |
| `generate --approved` | Generate approved supported heading/navigation and reviewed functional scenarios |
| `run` | Exit 0 only when Pytest succeeds; retain per-run JUnit and JSON |
| `diagnose` | Analyze latest run; no automatic repairs |
| `report --format html` | Client-facing HTML with escaped application text |
| `report --format json` | Structured project/run summary |
| `integrate --provider github` | Generate workflow from QA repository root; refuses overwrite |
| `build-framework DESTINATION --approved --project PATH` | Export supported approved scenarios and Page Objects into a new standalone directory |
| `validate-framework DESTINATION` | Check file hashes, Python syntax and exported approval snapshot; no execution |
| `run-framework DESTINATION --project PATH` | Recheck current source approvals, collect and run; propagate failure exit status |

Order: init → explore → plan → review → approve → generate → run → diagnose → report. `maintain` and `auth configure` are intentionally absent until implemented. There are no commands that print placeholder success.

Repository-only discovery cannot generate executable UI cases. AI suggestions cannot be approved through test IDs: they require independent review and implementation. AutoQA never executes AI output as Python. V0.2 behavior contracts are documented in v0.2-functional-testing.md. Reports can also be generated before execution; they explicitly state NOT_EXECUTED and contain no fabricated test records.

## Standalone framework workflow (V0.4)

Use the existing project selection and review commands first. `build-framework` requires
`--approved`, valid independent receipts and browser evidence for supported scenarios.
Its destination parent must exist; the destination itself must be absent and outside the
source project, without traversal or link/junction components. It never overwrites an
existing export. Unsupported approved scenarios are listed explicitly; no test is emitted
for them. At least one supported approved scenario is required.

After export, install the dependencies in its own environment using `uv sync`, install
Chromium with `uv run playwright install chromium`, then use:

```powershell
uv run python -m qa_runtime.runner validate
uv run python -m qa_runtime.runner collect
uv run python -m qa_runtime.runner run
```

These commands run from the exported directory without AutoQA installed. The application
must be running separately. Browser/environment settings are reviewed snapshots; update
the source config and export to a new directory when they change. `AUTOQA_BASE_URL` is
the optional authorized target override, still constrained by exported network policy.

`run-framework` uses AutoQA's interpreter and additionally checks current project approval
state before calling the export runner. Direct standalone execution validates only the
exported snapshot; it cannot observe later source revocation. Unique run directories
contain real JUnit, JSON outcomes, per-operation evidence, diagnosis.json and report.html.
Ruff is needed in the builder environment, but not in the standalone runtime.

Failures return nonzero; collection failure/timeout cannot become passing records.
See [release candidate](v04-release-candidate.md) for verification and operating limits.
