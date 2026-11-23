# V0.6 test management and selective execution

Current candidate: **0.6.0rc1**. Historical matrices/contracts remain unchanged.
The additive schema 0.6 suite sidecar references stable existing TC-* IDs. A project
has one suite and multiple packs, with deterministic deduplicated case selection.

## Operator workflow

```powershell
# First plan/review scenarios with the existing UI or API workflow.
uv run autoqa suite-propose --project projects/owned | Set-Content -Encoding utf8 suite.json
# Inspect/edit JSON: packs.case_ids, cases.tags, priority, enabled, and suite id.
uv run autoqa suite-approve suite.json --project projects/owned
uv run autoqa build-framework ../owned-framework --approved --project projects/owned
uv run autoqa run-framework ../owned-framework --case TC-API-HEALTH --project projects/owned
uv run autoqa run-framework ../owned-framework --pack SMOKE --project projects/owned
uv run autoqa run-framework ../owned-framework --suite DEFAULT --project projects/owned
uv run autoqa run-framework ../owned-framework --tag smoke --project projects/owned
uv run autoqa run-framework ../owned-framework --all --project projects/owned
```

Run commands require the owned authorized application and any declared credentials
to be available. Use UTF-8 when saving JSON; the CLI prints unwrapped JSON. The
proposal is pending and does not write the project. suite-approve is the explicit
operator authorization to persist membership and its receipt/event snapshot; it
cannot change case content/signature, type or scenario review state. A changed
scenario inventory or manually edited membership invalidates the saved receipt.
Re-review membership and export a fresh destination after legitimate changes.

Initial proposals contain SMOKE, SANITY and REGRESSION packs with no inferred
membership. API membership derives only from the actual API type; CRITICAL_PATH
proposes only explicit Critical priorities. Every proposal still requires review.
Unknown category membership remains unassigned. Example: SMOKE=[TC-A,TC-B] and
SANITY=[TC-B] reference TC-B once; no case or generated implementation is copied.
Tags and other compatible pack IDs are operator-assigned metadata.

Inside an export with independent dependencies installed:

```text
uv sync
uv run python -m qa_runtime.runner validate
uv run python -m qa_runtime.runner collect --pack SMOKE
uv run python -m qa_runtime.runner run --case TC-A
uv run python -m qa_runtime.runner run --pack SMOKE --pack SANITY
uv run python -m qa_runtime.runner run --suite DEFAULT
uv run python -m qa_runtime.runner run --tag smoke
uv run python -m qa_runtime.runner run --all
```

One mode per invocation; repeat case, pack or tag within a mode. Default no flags
retains regression execution. Exact generated node IDs are derived internally from
reviewed identities and passed as subprocess arguments. Unknown case/pack/suite,
empty pack/tag selection, disabled case or pending/rejected case returns nonzero
before requests, without fallback. Disabled explicit selections report NOT_EXECUTED
in the rejection diagnostic; rejected selections are not recorded as executed runs.
All/suite selects the actual approved-enabled inventory. Unsupported approved cases
produce UNSUPPORTED outcomes and nonzero, including an unsupported-only selection.

## Run accounting and history

Each immutable-by-workflow run directory contains selection_snapshot, inventory
digest, project_id, suite_id, pack_ids, selected_case_ids, selection_mode and UTC
start/completion timestamps in results.json. The `execution_run` envelope is validated
through the schema 0.6 ExecutionRun/ExecutionResult contracts before serialization. Prior run directories are retained;
there is no centralized editable history database. The exported reviewed inventory
and hashes supply reproducibility metadata. Reports link JUnit and per-case evidence.

`accounting` counts logical cases: global eligible approved-enabled inventory, selected,
executed/observed outcome cases, passed, failed, error, skipped, not_executed,
unsupported, UI/API composition and coverage within selected scope. `records` and
legacy `counts` count actual expected invocations, including API parameter rows.
One case with two rows therefore has two invocation records and one logical outcome;
its outcome uses the worst state ERROR/FAILED/NOT_EXECUTED/UNSUPPORTED/SKIPPED/PASSED.
Skipped and error JUnit outcomes count as observed/executed, not as passed coverage.
Coverage is observation coverage, not application code coverage or a pass percentage.

Single/pack/tag/suite results are SELECTED_SCOPE, even if their IDs equal all eligible
cases. Only all/default is labeled FULL_REGRESSION. A selected-scope pass is never
reported as a fully passed regression. Missing/duplicate/malformed/unexpected JUnit,
missing/foreign/inconsistent/incomplete operation evidence, failed/error/skipped or
unsupported scope cannot produce a successful complete run. Actual statuses remain
PASSED, FAILED, ERROR, SKIPPED, NOT_EXECUTED and UNSUPPORTED. JSON and escaped HTML
show scope/accounting; existing row-level evidence and privacy controls remain.

Trusted operator/filesystem, unsigned receipts, single writer and manual retention
remain required. Historical exports use the legacy manifest scope, not a silently
migrated project inventory. Later source approval or membership revocation cannot
be observed by an already delivered independent snapshot.

Historical standalone runners do not gain new flags retroactively: source-backed
no-flag/all execution forwards their original command without new arguments.
Selective execution against such an export fails with a request to review/re-export.


## Collection scope integrity (independent audit H02)

`collect` now reconciles every selected expected invocation against Pytest's emitted
node identities, including parameter rows. Pytest exit 0 alone is insufficient.
Approved unsupported selections, missing or duplicate identities, unexpected nodes (including other Python modules)
or a collection-process failure produce nonzero and INCOMPLETE_OR_FAILED diagnostics.
Fully supported complete scope retains exit 0. Unknown/empty selections still fail
before subprocess execution. An unsupported-only selection does not invoke Pytest.

Each collection writes collection.json with the selection snapshot, expected/observed
invocation counts, unsupported case IDs, missing/duplicate expected node IDs and an
unexpected-node count. Protected output retains summary-only policy; arbitrary
unexpected node names are not copied into this structured diagnostic. Collection
creates no execution results, JUnit outcomes or operation evidence and never invokes
target-request/browser fixtures. Its status is collection completeness, not PASSED
test execution. Actual execution/JUnit/evidence reconciliation remains unchanged.

Compatibility is explicit: the updated runner can adapt historical manifests with
no management inventory, checking only their declared executable scope. It cannot
infer unsupported source cases absent from that historical snapshot. Previously
exported runtime files are not patched retroactively; re-export to obtain the fix.
The exporter also avoids initializing UI scope/discovery for a non-automatable
manual case in an API project; that case remains unsupported in the reviewed scope.

Collection reconciliation targets the pinned generated Pytest node-ID format,
including its integer parameter-row IDs. Arbitrary third-party collectors/plugins
are not supported; plugin autoload remains disabled. Collection output is not
execution evidence and never certifies a target application's behavior.
