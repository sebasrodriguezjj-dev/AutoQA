# AutoQA Agent 0.2.0

A private Python CLI for evidence-driven QA automation. AutoQA explores an authorized application, records visible UI evidence, proposes reviewable scenarios, generates approved Playwright tests, executes them with Pytest, and renders actual results as HTML or JSON. It works offline; optional AI produces review-only recommendations.

V0.2 adds passive functional control discovery, browser-checked semantic locators, typed behavior contracts, positive/negative/boundary cases, functional Python templates, pre-execution Ruff and collection checks, richer diagnostics and reports from execution snapshots. Unknown behavior stays pending review. Authentication, remote repository access and autonomous maintenance remain unsupported. See [V0.2 functional testing](docs/v0.2-functional-testing.md) for the exact contract schema, independent-demo benchmark and external validation limitations.

The V0.1 report and run history in projects/demo-project are preserved. New V0.2 acceptance evidence is isolated in projects/independent-v02 and projects/toolshop-v02.

## Requirements and installation

Windows 11, Python 3.14, internet for initial package/browser downloads, and a browser-capable desktop session. The package deliberately supports Python 3.14 only in this release. Python 3.14.3 was used for local verification.

```powershell
Set-Location C:\Users\sebas\Desktop\AutoQA
python -m pip install uv
# If uv is not found, reopen the terminal or use python -m uv in its place.
python -m uv sync --locked
python -m uv run playwright install chromium
python -m uv run autoqa --help
```

Standard commands, when uv is on PATH:

```powershell
uv sync
uv run autoqa --help
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run playwright install chromium
```

Dependencies are locked in `uv.lock`; application and development dependencies are separated in `pyproject.toml`. Stable releases were resolved from the package registry, imports tested, and Chromium launched on Python 3.14. These exact versions were installed: Playwright 1.65.2, Pytest 9.2.0, pytest-playwright 0.10.0, Typer 0.29.1, Rich 15.0.0, Pydantic 2.14.3, PyYAML 6.0.3, Jinja2 3.1.6, Ruff 0.17.5, uv 0.13.9. Optional OpenAI SDK: 3.54.0. Browser: Chromium 159.0.8154.6, Playwright revision 1255. See [versions](docs/versions.json) and [verification](docs/verification.md).

For VS Code, open this folder, install the Python and Ruff extensions, and select `.venv\Scripts\python.exe` using **Python: Select Interpreter**. No virtual environment activation is required with `uv run`.

## Run the demo workflow

Terminal 1 (leave running):

```powershell
Set-Location C:\Users\sebas\Desktop\AutoQA
python -m uv run autoqa demo
```

Terminal 2:

```powershell
Set-Location C:\Users\sebas\Desktop\AutoQA
python -m uv run autoqa init my-demo
python -m uv run autoqa explore --url http://127.0.0.1:8000 --authorized --allow-localhost
python -m uv run autoqa plan
Get-Content projects\my-demo\test-cases\test-matrix.md
# Review these actual scenarios before approving. IDs below refer to the included demo.
python -m uv run autoqa plan --approve TC-001 --approve TC-003 --approve TC-006 --approve TC-010 --approve TC-013
python -m uv run autoqa generate --approved
python -m uv run autoqa run
python -m uv run autoqa diagnose
python -m uv run autoqa report --format html
Start-Process projects\my-demo\reports\qa-report.html
```

Initialization never overwrites a project. Use a new name on subsequent runs, or select an existing project using `--project projects\my-demo` on each command. From inside a project directory, AutoQA uses that project. From the repository root, the last project created in `projects/` is active. Artifacts stay within the selected project. Paths are supported in PowerShell, including spaces when quoted.

The included app has home, catalog, two product detail pages, client-side search, and a contact form using native required/email validation. It has deterministic data and no external services. Discovery never fills or submits the form. Generated MVP tests do not assert unconfirmed search/form behavior.

## Commands and configuration

| Command | Implemented behavior |
| --- | --- |
| `init NAME` | Isolated workspace, YAML config, SQLite registry, active selection |
| `demo` | Original local app; `--variant independent --port 8001` starts Supply Lab |
| `explore --url URL --authorized` | Bounded Chromium observations, screenshots, route graph, workflows |
| `explore --repo PATH --authorized` | Bounded read-only local source inspection |
| `explore --repo PATH --url URL --authorized` | Both inspections plus inferred path correlation |
| `plan` | JSON and Markdown matrix; all new cases pending review |
| `plan --approve ID` | Persist approval for selected IDs; repeat flag for multiple IDs |
| `plan --requirements FILE` | Import reviewed behavior contracts bound to observed elements; cases remain pending |
| `plan --reject ID` | Persist rejected scenarios without deleting them |
| `plan --ai` | Explicitly send reduced workflow evidence for optional AI recommendations |
| `generate --approved` | Evidence-checked, syntax-validated Python templates only |
| `run` | Real Pytest execution with JUnit, screenshots, traces, logs and JSON results |
| `diagnose` | Conservative classification of actual failures; no test modification |
| `report --format html` | Escaped Jinja2 client report; `json` also supported |
| `integrate --provider github` | Local reviewable workflow; never pushes remotely |

See [CLI reference](docs/cli-reference.md). Every project operation accepts `--project PATH`. Commands return nonzero on errors; `run` propagates Pytest failure status. Interruption returns 130, preserving completed artifacts; an interrupted discovery may not produce a final discovery file.

`config.yaml` is validated with Pydantic and rejects unknown keys:

| Setting | Default / meaning |
| --- | --- |
| `name` | Project display name |
| `application_url`, `repository` | Set by discovery |
| `mode` | `ui`, `repository` or `hybrid` |
| `allowed_domains` | Empty until discovery; then exact application hostname |
| `allow_localhost` | `false`; `--allow-localhost` explicitly persists demo permission |
| `max_pages`, `max_depth` | 10 and 2; caps 100 and 5 |
| `navigation_timeout_ms` | 15000 |
| `overall_timeout_seconds` | 120; upper bound 600 |
| `request_interval_ms` | 150; minimum spacing between permitted requests; use 500 for external validation |
| `headless` | `true` |
| `auth_reference` | `null`; non-null rejected by v0 discovery |
| `ai_provider`, `ai_model` | `offline`, `null` |
| `test_preferences` | Chromium; other browsers not implemented |

For another authorized host, use a separate client project or update `allowed_domains` deliberately. Scope is stricter than the hostname list: all requests must retain the initial scheme, host and port. Query URLs, credential URLs, private networks other than explicitly enabled loopback, external resources, modifying HTTP methods and sensitive route names are excluded. These restrictions may prevent some SPAs from loading correctly. Read [security boundaries](docs/security.md) before using client applications.

## Optional AI

Offline discovery, planning, generation, execution, diagnosis and reports require no key. AI only proposes extra ideas; it cannot approve scenarios, generate executable code, run commands or alter assertions. Structured outputs use the maintained official SDK, per [official OpenAI documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

```powershell
python -m uv sync --extra ai
# Set OPENAI_API_KEY in this terminal using your secret manager.
# Choose an account-accessible model supporting Responses structured outputs.
$env:AUTOQA_AI_MODEL = 'YOUR_SUPPORTED_MODEL_ID'
# In projects/my-demo/config.yaml, set ai_provider: openai.
python -m uv run --extra ai autoqa plan --ai --project projects\my-demo
```

The SDK reads `OPENAI_API_KEY`. No model is silently selected. `.env.example` is documentation; `.env` is not automatically loaded. `plan --ai` explicitly sends workflow IDs and visible control/heading text to OpenAI. Review client data policies before invoking it. Source files, screenshots, credentials and traces are not attached. Website text remains untrusted; output is schema-validated and evidence IDs checked. Suggestions live in `test-cases/ai-recommendations.json`, separate from executable cases. Live provider access was not verified; tests use mocked responses and no credentials.

## Repository analysis and CI

```powershell
python -m uv run autoqa explore --repo .\src --authorized --project projects\my-demo
# Use both flags for hybrid analysis; local source is never executed or installed.
python -m uv run autoqa explore --repo .\src --url http://127.0.0.1:8000 --authorized --allow-localhost --project projects\my-demo
```

Static inspection identifies languages, selected manifests/frameworks, Python/JS route candidates, Next app pages, JSX/TSX components, Python model candidates and existing tests. It is bounded to 3,000 files, approximately 20 MB of text, 256 KB per file and depth 12. Hidden/vendor/build folders, symlinks/junctions and obvious credential filenames are skipped. It is a heuristic inventory, not a security scanner or measured test coverage. Repository-only plans contain manual review cases; URL evidence is required for generated UI tests.

After approval and generation:

```powershell
python -m uv run autoqa integrate --provider github --project projects\my-demo
```

This creates `.github/workflows/autoqa-my-demo.yml` in the QA repository. Inspect it before committing. See [CI setup](docs/ci.md) for files to include, staging URL scope and the limitations of the generated workflow. Hosted execution has not been verified. The application under test can live in a separate repository.

## Architecture and artifacts

```text
pyproject.toml / uv.lock          package and reproducible dependencies
src/autoqa/
  cli.py / __main__.py           Typer entry points
  core.py                       Pydantic contracts, project storage, SQLite registry
  security.py                   URL scope and request policy
  demo.py                       local application
  exploration.py                Chromium observations and workflow extraction
  repository.py                 bounded source inspection and path correlation
  planning.py                   matrix and persisted approvals
  testing.py                    templates, integrity checks, Ruff/collection, runner, parser
  observation.py                passive semantic evidence and checked locator candidates
  functional.py                 typed reviewed contracts and functional template generation
  independent_demo.py           owned independent search/filter/sort/form application
  llm.py                        optional structured-output recommendations
  reporting.py / templates/     diagnosis, escaped Jinja2 report
  integration.py                local GitHub Actions generation
tests/                          unit and real browser integration tests
skills/                         internal QA guidelines (no executable privileges)
docs/                           architecture, security, CLI, CI, roadmap, verification
projects/NAME/                  isolated private artifacts (Git-ignored)
```

Each project contains `config.yaml`, `discovery/`, `test-cases/`, `automation/`, `reports/`, `screenshots/`, `artifacts/` and `logs/`. Workflow maps retain OBSERVED or INFERRED status; source inspection retains SOURCE status. Reports describe discovery counts, not requirements coverage percentages. Runs have unique IDs and retain screenshots/traces for all tests. `reports/latest-run.json` is the most recent completed run; `reports/qa-report.html` is regenerated explicitly.

## Development, verification and troubleshooting

```powershell
python -m uv sync --locked --extra ai
python -m uv run --extra ai pytest --junitxml=docs/internal-test-results.xml
python -m uv run ruff check .
python -m uv run ruff format --check .
```

The test suite includes real browser passes, a deliberately changed application baseline that must fail, request/redirect blocking, exploration bounds, config isolation, approval persistence, source inspection, generation, JUnit parsing, escaped reports, mocked AI and CI syntax checks. Intentional failures are asserted inside passing integration tests; they are not hidden or weakened. Details and actual counts are in [verification](docs/verification.md).

- **uv not recognized:** reopen the terminal or use `python -m uv`.
- **Browser executable missing:** run `python -m uv run playwright install chromium`.
- **Connection refused:** start the demo in another terminal and verify its URL/port.
- **Scope rejection:** confirm authorization and exact origin; use localhost permission only for the owned demo. Internal/private network targets are unsupported.
- **No active project:** pass `--project projects\NAME` or run from the selected workspace.
- **No approved tests:** read the matrix, approve feasible IDs, then generate with `--approved`.
- **Modified suite rejected:** preserve edits elsewhere, review, then regenerate. AutoQA refuses to replace modified Python suite files or execute them through its controlled runner.
- **Package upgrade cannot replace autoqa.exe on Windows:** stop running AutoQA commands before `uv sync`; Windows locks an active executable.
- **Run timed out:** inspect the run's `pytest.log` and JUnit file. Missing cases become NOT_EXECUTED, never PASSED. On Windows, forced timeout cleanup of descendant browser processes is not guaranteed.

No remote clones, auth configuration command, self-healing, scheduling, API test generation, cloud dashboard or arbitrary AI code execution is provided. Functional contracts support observed fill/select/check/uncheck actions, limited safe button clicks, exact result lists/counts/text, visibility, native validity and numeric ordering. They cannot run arbitrary scripts. See [V0.2 guide](docs/v0.2-functional-testing.md) and [roadmap](docs/roadmap.md).
