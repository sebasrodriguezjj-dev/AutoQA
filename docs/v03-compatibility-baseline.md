# V0.3 Stage 0 compatibility baseline

Stage 0 characterizes the current implementation before introducing contracts/readers in Stage 1 of the [architecture plan](./architecture-v03-plan.md). Production code, dependencies, package version and existing project artifacts are unchanged.

## Frozen inputs

[V0.1 archive](../tests/fixtures/compatibility/v01.zip) contains byte-for-byte selected files from [demo-project](../projects/demo-project/): 27 cases, five approved/generated cases, an unversioned manifest and a five-pass run without snapshots. [V0.2 archive](../tests/fixtures/compatibility/v02.zip) comes from [independent-v02](../projects/independent-v02/): 31 cases, nine approved/generated cases, manifest version `0.2.0` and a nine-pass run with snapshots.

Each archive contains the original configuration, discovery map, matrix, generated test/fixture, manifest, latest-run and its actual JUnit XML. [baseline.json](../tests/fixtures/compatibility/baseline.json) records provenance and SHA-256 hashes for archives and individual members. No artifact was normalized, regenerated or rewritten. Archives prevent Pytest from discovering saved browser tests and make checks independent of ignored local projects. Tests extract disposable copies; they never import/execute the frozen suites or dereference the saved repository path. Screenshots, traces, Markdown and full histories are outside these small fixtures.

## CLI contract

The installed entry point remains `autoqa = autoqa.cli:app`; all nine command signatures and command help are protected by [characterization tests](../tests/test_compatibility_baseline.py). `python -m autoqa` also delegates to this app in the existing package; this invocation path was inspected, not separately subprocess-tested.

| Command | Positional arguments/options and defaults |
| --- | --- |
| `init` | Required `NAME`; `--parent projects` |
| `demo` | `--host 127.0.0.1`, `--port 8000`, `--variant original` |
| `explore` | Optional `--url`, `--repo`, `--project`; `--authorized` and `--allow-localhost` default false |
| `plan` | Optional `--project`, repeatable `--approve`/`--reject` preserving ID order, `--requirements`; `--ai` false |
| `generate` | Optional `--project`; `--approved` false and required by the operation |
| `run`, `diagnose` | Optional `--project` |
| `report` | Optional `--project`; `--format html` |
| `integrate` | Optional `--project`; `--provider github` |

Boolean options also expose their existing `--no-…` counterparts. Unspecified paths/URLs/review lists default to `None`. Help exits 0; missing arguments, unknown commands/options, invalid integer input and no command exit 2. Handled `ValueError`, `OSError` and Playwright errors exit 1; interruption exits 130. `run` propagates process outcomes, tested for 0–5 and timeout 124 through a stubbed executor. Successful help and repeated review dispatch exit 0. Conflicting approve/reject, approval plus AI, unapproved generation and missing exploration authorization exit 1 without changing the project.

Selection precedence is explicit path → configuration in the exact current directory → `projects/.autoqa/active.json` under the exact current directory → error. An invalid explicit path fails without fallback. Selection does not walk ancestors. Initializing another project updates active selection, but a project-local current directory still wins. Existing [core tests](../tests/test_core.py) also cover no-project errors, initialization, isolation and configuration validation.

## Artifact, approval and execution contracts

| Contract | Protected behavior |
| --- | --- |
| Configuration/discovery/matrix | YAML configuration, object-shaped discovery JSON, array-shaped case JSON; existing additive model defaults allow old inputs to load. V0.1 has no functional extensions, V0.2 has contracts/evidence metadata. Reading does not persist new defaults. |
| Approval signature | SHA-256 of sorted-key `json.dumps` of the current model projection. Excludes `review_status`; nonfunctional cases also exclude `test_data`, `evidence_refs`, `workflow_id`, `contract`. Those four fields affect functional signatures. Expected-behavior changes affect all case signatures. All 14 frozen manifest signatures still match approved cases. |
| Manifest/integrity | Legacy manifest has `files`/`cases`; V0.2 adds `version`. Managed Python names are exactly `conftest.py` and `test_observed.py`. Digests use UTF-8 decoded text via the existing digest function. Extra manifest entries, nested unmanaged Python, modified content and withdrawn approvals are rejected before execution. |
| Generated runtime | Saved fixture imports `autoqa.core.Project`, `autoqa.security.Scope` and Playwright; resolves the project at its parent directory; exposes `qa_page`, `AUTOQA_BASE_URL`, `AUTOQA_RUN_DIR`. Suites require AutoQA installed and the current artifact layout. AST inspection avoids executing fixture code. |
| Test results | Actual JUnit names/statuses agree with saved run records. Record fields remain `id`, `name`, `status`, `duration`, `error`. Existing parser tests cover PASSED/FAILED/ERROR/SKIPPED and missing XML. Missing generated cases become NOT_EXECUTED, never implicit passes. |
| Run persistence | Base fields are run ID, creation time, exit code, duration, records, artifact directory and base URL. V0.2 also stores case/planning/discovery snapshots. New controlled runs verify both result copies, snapshots, collection-first behavior, exit 2/124 handling, logs and missing records. Browser execution and lint validation are stubbed only in these orchestration tests. |
| Runtime environment | Controlled runner tests confirm `shell=False`, plugin autoload disabled, base-URL propagation and removal of ambient Pytest options/arbitrary secret variables. Existing allowlisted OS environment behavior remains unchanged. |
| JSON boundary | Discovery edges are tuples in an in-memory run and arrays after JSON serialization. Assertions compare persisted runs to JSON-normalized results; no production normalization was added. |
| Reports | Disposable copies verify current-plan fallback for V0.1 and snapshot precedence for V0.2 after matrix changes. Reporting writes report JSON, diagnosis JSON and audit events; it is not a read-only operation. Existing [contract tests](../tests/test_contracts.py) protect snapshot metrics and explicit NOT_EXECUTED reporting without a fabricated run; [pipeline tests](../tests/test_pipeline.py) cover HTML escaping and approval drift. |

Repeated `Project` construction, selection, `cases()`, `discovery()`, JSON loading and signature computation preserve the extracted trees' contents, mtimes, approvals and file inventories. Separately, before/after SHA-256 checks found no changes to 197 existing production/dependency/project files. Original project suites were not rebuilt or executed.

The established path layout remains configuration at project root; discovery under `discovery/`; cases under `test-cases/`; managed automation under `automation/`; per-run output under `artifacts/<run_id>/`; latest-run, diagnosis and client reports under `reports/`; audit under `logs/events.jsonl`. The new fixture hashes freeze representative paths; existing tests exercise creation and temporary-project generation. This is not exhaustive binary/report-layout coverage.

## Verification

Executed with the existing local virtual environment:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_compatibility_baseline.py tests/test_core.py tests/test_contracts.py tests/test_pipeline.py -m 'not browser' -q --junitxml=docs/v03-characterization-tests.xml
.venv/Scripts/python.exe -m ruff check tests/test_compatibility_baseline.py
.venv/Scripts/python.exe -m ruff format --check tests/test_compatibility_baseline.py
```

Result: **102 passed, four browser tests deselected**, including **57 new characterization cases**. Ruff check and format check passed. [JUnit evidence](./v03-characterization-tests.xml) records the combined run. An initial six new assertions incorrectly equated tuple-bearing runtime data with JSON data; correcting the assertions captured the existing serialization behavior. No production failure required a fix.

No external tests, live AI calls, builds, dependency changes or existing-suite regeneration were performed. The owned 9-pass → two-regression → 9-pass acceptance history remains historical evidence; it was not rerun in Stage 0.

## Compatibility gaps and Stage 1 readiness

- There are no schema envelopes or version rejection rules today; even manifest version is not checked by the runner. Stage 1 must add explicit readers without changing current legacy acceptance silently.
- Unknown new configuration keys fail validation. New model defaults can change signatures; preserve the exact legacy projections and golden approvals before adding fields.
- V0.1 has no run snapshots, and neither version has per-step results. Preserve fallback and missing-data semantics; do not invent historical evidence or step success.
- CLI authorization is not a universal library-service guard. This stage characterizes the CLI checks; central enforcement remains a later migration task.
- Pytest collection failures and partial JUnit can contain runner-level records. The tests protect missing planned cases and observed outcomes, not a redesigned failure model. The parser alone cannot recover every ID containing underscores; the runner's manifest-name mapping remains necessary.
- Full binary evidence, exact HTML presentation, concurrent writers, all subprocess environment keys, every CLI diagnostic string and the complete acceptance workflow are outside this targeted baseline. The fixture archives deliberately retain old runtime dependencies and absolute repository metadata as data.

**Ready for Stage 1 contracts/readers work**, subject to retaining this baseline and adding explicit conversion/version tests. No Stage 1 implementation is included or started.
