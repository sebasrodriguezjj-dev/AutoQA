# AutoQA V0.3 Batch A delivery

## Outcome

Stages 1–3 implemented and verified on `feat/v03-batch-a`, based on clean development
HEAD `1853c35b5a666b1c1680d9dc0684014452f82430`. Origin was verified as
`https://github.com/sebasrodriguezjj-dev/AutoQA.git`. All changes and commits are local;
no push, merge or pull request was made.

| Stage | Commit | Verified change |
| --- | --- | --- |
| 1 | `b7566a6a331c9bbb416e64d4a7700280c084c442` | Versioned domain contracts and read-only legacy projections |
| 2 | `5bcba16d6a7f6951692a8093838802a2c2f4c79b` | Local storage, registration and selection boundary |
| 3 | `545a2456c4e912c712c2a31cd413a76a7b67f78f` | Pure diagnostics/projections, typed report data, separate HTML rendering |

The subsequent documentation-only commit records these actual stage SHAs; its own SHA
is intentionally not embedded in itself. See the [checkpoint](./v03-batch-a-checkpoint.md).

## Architecture and files changed

- [domain.py](../src/autoqa/domain.py): `Project`, `TestSuite`, `TestCase`, `TestStep`,
  `TestRun`, `TestResult`, `StepResult`, `Evidence`; explicit `0.3` schema, opaque persistent
  IDs, relationship validation, UTC-aware timestamp validation, project-relative references,
  provenance/sensitivity and independent review/generation/execution enums. JSON round trips
  retain identities. Pure path syntax validation uses standard-library lexical paths only;
  no filesystem access, browser, CLI, subprocess or provider dependency.
- [legacy.py](../src/autoqa/legacy.py): explicit case, derived-suite and run projections.
  Callers supply project/suite identities; no historical project identity or revision is
  invented or written. Original case/run payloads remain available as copied JSON data.
  Unknown functional behavior remains preserved in legacy payloads and non-executable.
  Historical step detail is `NOT_RECORDED`, not a pass. Unsupported schema versions fail.
- [storage.py](../src/autoqa/storage.py): `LocalProjectStorage`, JSON utilities, atomic text
  replacement, SQLite registration and exact existing selection precedence. Every adapter
  path is confined and checked for links/junctions. JSON serialization precedes mutation;
  successful writes flush/fsync a unique sibling temporary file before replacement, and failed
  replacements clean the temporary file while preserving the original. Completed run
  directories with `results.json` are read-only through the adapter.
- [core.py](../src/autoqa/core.py): compatibility facade delegates configuration, cases,
  discovery, audit, registration and selection to storage. Existing public model/import names,
  JSON utilities and project layout remain available. Existing legacy model definitions are
  unchanged so signed projections do not acquire domain defaults.
- [diagnostics.py](../src/autoqa/diagnostics.py): pure `classify_failure`, immutable typed
  `Classification`, and diagnostics projection using explicitly supplied available evidence.
  Classification ordering and cautious root-cause language remain unchanged.
- [report_projection.py](../src/autoqa/report_projection.py): pure `project_report`, typed
  `ReportData` and separate historical `StepEvidence` availability projection. Preserves metrics,
  statuses, workflow groups and snapshot-based automation counts. Does not infer coverage.
- [report_rendering.py](../src/autoqa/report_rendering.py): Jinja HTML rendering with existing
  template and HTML autoescaping; no persistence or metric calculation.
- [reporting.py](../src/autoqa/reporting.py): public `diagnose`/`report` orchestration retains
  snapshot/fallback loading, existing links and artifact selection, diagnosis/report writes
  and audit events. JSON/HTML persistence now uses the storage adapter.
- [test_domain.py](../tests/test_domain.py): nine new contract/conversion cases.
- [test_storage.py](../tests/test_storage.py): 12 new storage cases.
- [test_reporting_boundaries.py](../tests/test_reporting_boundaries.py): ten new pure
  classification/projection/rendering/orchestration cases.
- This delivery document and the [checkpoint](./v03-batch-a-checkpoint.md).

No dependencies, templates, existing approval/generation/security implementation, frozen
archives, baseline hashes or historical approved suites were modified.

## Verification

Existing environment: `.venv/Scripts/python.exe`, Python 3.14.3, no dependency changes.
Commands below ran from the repository root. All test commands used `-p no:cacheprovider`
and distinct disposable `--basetemp=.test-work/batch-a-…` directories on successful runs.

| Gate | Test selection (`python -m pytest … -m 'not browser' -q`) | Result |
| --- | --- | --- |
| Stage 1 | `tests/test_domain.py tests/test_compatibility_baseline.py tests/test_core.py tests/test_contracts.py tests/test_pipeline.py` | 111 passed, 4 deselected |
| Stage 1 final model additions | `tests/test_domain.py` | 9 passed |
| Stage 2 | `tests/test_storage.py tests/test_compatibility_baseline.py tests/test_core.py tests/test_contracts.py tests/test_pipeline.py` | 112 passed, 1 skipped, 4 deselected |
| Stage 2 final link/junction checks | `tests/test_storage.py` | 12 passed, no skips |
| Stage 3 | `tests/test_reporting_boundaries.py tests/test_compatibility_baseline.py tests/test_contracts.py tests/test_pipeline.py` | 87 passed, 4 deselected |
| Final combined | Command below | **167 passed, 12 deselected, no skips** |

```powershell
.venv/Scripts/python.exe -m pytest tests -m 'not browser' --ignore=tests/test_live_ai.py -q -p no:cacheprovider --basetemp=.test-work/batch-a-final --junitxml=.test-work/batch-a-final-results.xml
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m ruff format --check src tests
git diff 1853c35b5a666b1c1680d9dc0684014452f82430 -- tests/fixtures projects pyproject.toml
```

Ruff lint passed; format verification passed for 35 files. The artifact/dependency diff was
empty. Editor diagnostics also reported no errors for the seven inspected new/changed
production modules. Final JUnit is disposable local verification output, not historical evidence.

The final selection includes all 31 new tests, the complete Stage 0 102-test non-browser
regression selection, and 34 additional existing non-browser security/offline-AI/CI cases.
Stage 0 tests recheck frozen archive/member hashes, all 14 approval signatures, manifest
integrity refusal, CLI/selection contracts, byte/mtime preservation on legacy reads,
run snapshots, missing execution statuses, report fallback and snapshot precedence,
and documented report/diagnosis/audit side effects.

The first sandboxed Stage 1 command produced 46 passes and 65 fixture-setup errors because
pytest could not access its temporary directory. The required elevated rerun passed; no
assertions were weakened. The initial Stage 2 real-symlink setup skipped under Windows
privilege restrictions. It was replaced with deterministic per-component symlink/junction
branch tests, both passing in the final run. Actual OS symlink creation is not claimed.

### Explicit exclusions

The live provider module [test_live_ai.py](../tests/test_live_ai.py), containing one test, was
explicitly ignored, independent of environment opt-in variables. No model API call occurred.
The following 12 browser cases were deselected:

- External-compatibility local API/resource/redirect test.
- Four bounded-readiness variants: `/delayed-CONTENT_STABLE`, `/busy-TIMEOUT`,
  `/shell-TIMEOUT`, `/status-STATUS_STABLE` (four variants).
- External-compatibility readiness persistence test.
- Functional discovery/contract security test.
- Independent functional pass/defect/restore test.
- Pipeline real browser vertical slice.
- Pipeline real failure/report.
- Pipeline real scope redirect/write blocking.
- Pipeline exploration depth/page bound.

Four readiness cases plus eight other browser cases total 12. No external website benchmarks
or browser acceptance reruns occurred.
The historical 9-pass → 2-regression → 9-pass acceptance remains historical, not a new result.

## Compatibility and limitations

- Legacy reads are opt-in projections, not migrations. Existing engine producers still write
  their V0.1/V0.2 formats. New domain identities persist when explicitly serialized, but no
  project IDs or suite revisions are automatically assigned to historical disk artifacts.
- Legacy prose (including current rendered functional step descriptions) stays descriptive.
  Detailed original functional contracts are preserved as legacy data, not promoted into
  executable domain actions. Execution wiring and new step instrumentation are deferred to
  the generation/execution stage; no historical step measurements are fabricated.
- New reporting DTOs are Python typed dictionaries, not an API or independently versioned
  wire protocol. Existing nested legacy dictionaries remain flexible. Step availability is
  exposed separately so current report JSON/HTML does not acquire inferred outcomes.
- Storage is single-writer. Atomic replacement does not implement concurrent writers or
  rollback of an entire project initialization/registry transaction. Link checks are not a
  defense against a concurrent hostile filesystem mutation between check and use.
- Completed-run protection applies through the new project storage adapter. Trusted runner
  code still directly creates/writes its fresh run directory; generic compatibility JSON
  helpers cannot infer project ownership. Broader runner extraction is deferred.
- Existing tracked project artifacts and frozen fixtures have no changes from the base.
  Tests used disposable projects; original ignored project directories were not regenerated
  or executed. No comprehensive before/after hash inventory of ignored binary evidence was
  captured, so this is not claimed as binary-evidence audit coverage.
- No FastAPI, frontend, MCP, queue, cloud backend, permissions expansion or live AI was added.

## Batch B readiness

Ready to build the next application/planning-review boundaries on these contracts and local
adapters while retaining the frozen compatibility gate. Approval/security centralization,
discovery orchestration, generation/execution extraction, explicit migrations and complete
shared engine composition remain later work in the [architecture plan](./architecture-v03-plan.md).
Before declaring the complete V0.3 migration release, run the owned browser acceptance gate;
Batch A's verified scope is the non-browser contracts/storage/reporting batch.
