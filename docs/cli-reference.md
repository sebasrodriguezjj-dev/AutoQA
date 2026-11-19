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
| `generate --approved` | Generate only approved, feasible heading/navigation scenarios |
| `run` | Exit 0 only when Pytest succeeds; retain per-run JUnit and JSON |
| `diagnose` | Analyze latest run; no automatic repairs |
| `report --format html` | Client-facing HTML with escaped application text |
| `report --format json` | Structured project/run summary |
| `integrate --provider github` | Generate workflow from QA repository root; refuses overwrite |

Order: init → explore → plan → review → approve → generate → run → diagnose → report. `maintain` and `auth configure` are intentionally absent until implemented. There are no commands that print placeholder success.

Repository-only discovery cannot generate executable UI cases. AI suggestions cannot be approved through test IDs: they require independent review and implementation. AutoQA never executes AI output as Python. V0.2 behavior contracts are documented in v0.2-functional-testing.md. Reports can also be generated before execution; they explicitly state NOT_EXECUTED and contain no fabricated test records.
