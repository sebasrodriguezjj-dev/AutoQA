# AutoQA V0.3 release finalization

Date: 2026-11-19. Branch: `feat/v03-batch-c`, based on verified Batch C `7d2d599`.

## Decision and scope

**Ready for integration as version 0.3.0**, within the trusted, synchronous local-engine
scope documented in the [release audit](./v03-release-audit.md). No release-blocking defect
remains identified in that scope. This finalization fixes diagnostic screenshot references,
adds regression coverage, aligns release metadata, and commits the audit locally.
No PR, push, merge, tag, live AI call or external website benchmark was performed.

## Corrected diagnostics and compatibility

[Diagnostic evidence projection](../src/autoqa/diagnostics.py) and
[filesystem lookup](../src/autoqa/reporting.py) share the same evidence-reference function.
They retain historical `<test>.png`, `<test>.zip` and run-level `pytest.log` references,
and now include `.png`/`.zip` filenames recorded by steps belonging to the matching test.
Step filenames are resolved only inside the current run's artifact directory. Explicit
step run IDs must match the run being diagnosed; traversal, absolute and non-filename
references are ignored. File existence and existing storage path/link checks still apply.
Duplicate references are removed. Missing files do not produce evidence links.

Four new cases in [reporting boundary tests](../tests/test_reporting_boundaries.py) cover
current step screenshots, legacy screenshots without step records, missing evidence,
and isolation between tests/runs (including stale and escaping references). The first
focused repro had **2 failed / 2 passed**, confirming the new-step omission before the
fix. Existing assertions were preserved. Final non-browser regression passes all four.
A real owned-localhost failure/report run also passed; its persisted diagnosis was
independently checked to contain the actual `test_TC_001-step-1.png`, trace and pytest log.
Diagnostic output remains a projection, not proof against forged local step metadata.

## Version and installation

[Package metadata](../pyproject.toml), [import version](../src/autoqa/__init__.py), and the
editable project entry in [uv.lock](../uv.lock) are **0.3.0**. The lockfile diff changes
only the root package version; dependency resolutions/hashes are unchanged.
`uv lock --check --offline` succeeded (37 packages).

Offline `uv build` produced `autoqa_agent-0.3.0.tar.gz` and
`autoqa_agent-0.3.0-py3-none-any.whl`, building the wheel from the source distribution.
The wheel was installed with `uv pip install --no-deps --offline` in a disposable venv.
Import inspection confirmed `autoqa.__version__` and installed distribution metadata
both equal `0.3.0`, with the imported file inside that venv's site-packages rather than
the checkout. The console entry point remains `autoqa = autoqa.cli:app`.

The initial dependency-free installation correctly could not launch the CLI without
Typer. Locked runtime requirements were exported with `uv export --locked --no-dev
--no-emit-project`; the offline install lacked cached greenlet. An authorized download
installed the exact 25 locked runtime dependencies into that disposable environment.
No project lock resolutions were changed. The installed `autoqa --help` and
`python -m autoqa --help` smoke checks then passed, displaying **AutoQA Agent 0.3.0**.
These checks do not claim an offline dependency installation from a complete cache.

## Verification evidence

Existing regression interpreter: `.venv/Scripts/python.exe`, Python 3.14.3.

| Gate | Actual finalization result |
| --- | --- |
| All non-browser tests, live AI module explicitly ignored | **179 passed, 14 deselected**, 24.26s |
| Owned-localhost Chromium failure/report test | **1 passed**, 21.79s |
| New diagnostic cases | All 4 passed in the non-browser run |
| Frozen legacy compatibility/signatures/read preservation | Passed in the non-browser run |
| Ruff lint and format | Passed; 43 files formatted |
| Lock consistency | Passed offline |
| sdist / wheel | Built successfully as 0.3.0 |
| Installed package/import/CLI metadata | 0.3.0, correct console entry point and successful help |
| Editor diagnostics for changed Python files | No errors reported |

Commands (outputs are disposable and ignored):

```powershell
.venv/Scripts/python.exe -m pytest tests -m 'not browser' --ignore=tests/test_live_ai.py -q -p no:cacheprovider --basetemp=.test-work/v030-final-nonbrowser --junitxml=.test-work/v030-final-nonbrowser.xml
.venv/Scripts/python.exe -m pytest tests/test_pipeline.py::test_real_failure_and_report -q -p no:cacheprovider --basetemp=.test-work/v030-browser --junitxml=.test-work/v030-browser.xml
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m ruff format --check src tests
uv lock --check --offline
uv build --offline --out-dir .test-work/v030-release-dist
git diff --check
```

Initial sandboxed repro attempts encountered pytest temporary-directory `WinError 5`;
authorized reruns supplied the evidence above. The earlier audit's complete 189-test run
(including all then-existing 14 browser cases and defect/restore acceptance) remains
historical evidence, not a claim that all browser tests were rerun in finalization.

## Preservation and remaining limits

Historical compatibility ZIPs, their baseline, approved suites, legacy manifests and
project evidence are unchanged. No original project suite was regenerated or executed;
all new execution used disposable test projects. Fixture hashes remain those recorded
in the audit. New test/build/install evidence stays under ignored `.test-work/` and is
excluded from release contents. Wheel/sdist inventories are inspected before commit;
the sdist intentionally contains tracked docs and frozen demo compatibility archives.

Instrumentation still wraps **one generated scenario in one coarse step**. Per-action
Playwright timings/outcomes, typed executable step contracts, richer sensitivity metadata,
and more complete skipped/interrupted step semantics remain future development. This
fix does not change screenshot policies or browser instrumentation. Local authorization
is caller intent, and receipts/manifests depend on trusted local writers. Storage remains
single-writer; browser evidence still requires review before distribution.

## Local Git state and proposed integration

All Batch A commits (`b7566a6`, `5bcba16`, `545a245`, `c5e71f4`), Batch B commits
(`eb57329`, `d6e2614`, `8e6dc67`, `e55b824`), and Batch C commits
(`4c9eace`, `bf70190`, `119dfad`, `7d2d599`) remain ancestors of the finalization commit.
The audit document and verified finalization changes are committed together locally;
the resulting SHA is reported in the completion message rather than embedded in itself.

Local main/cached origin/main were `1853c35`; remote state has not been refreshed.
After explicit authorization and with a clean working tree, preserve the full history:

```powershell
git fetch origin
git switch main
git merge --ff-only origin/main
git merge-base --is-ancestor main feat/v03-batch-c
# Continue only if every preceding command succeeds:
git merge --ff-only feat/v03-batch-c
```

If ancestry or fast-forward checks fail, stop and inspect remote changes. Prepare a
separate integration branch and validate the combined tree before seeking approval;
do not reset, discard, force-push or cherry-pick only Batch C. No push, PR, merge or
`v0.3.0` tag is authorized by this local finalization. Publishing/tagging requires a
separate explicit instruction.
