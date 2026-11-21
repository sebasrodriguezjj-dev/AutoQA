# V0.4 framework builder design

Baseline: annotated v0.3.0 / d26f9088f12b369ea222da6ea3c02176f93b7474.
Before editing: 180 non-browser tests passed, 14 browser cases deselected; Ruff lint
and format passed. Frozen archives remain unchanged. No prior V0.4 branch existed.

## Boundaries

FrameworkService is additive to ApplicationEngine. It requires project-bound generate
authorization and matching independent approval receipts before producing output.
Existing generate/run and historical domain/report/manifest formats are preserved.
New CLI commands build-framework, validate-framework and run-framework are independent
of the existing automation directory. Running via AutoQA additionally checks current
project approvals; standalone delivery checks its exported reviewed snapshot/receipts.

A typed blueprint describes pages, locator properties, reusable operation methods,
scenario sequences and unsupported approved scenarios. Rendering uses existing trusted
functional validation and templates, never AI code. Unsupported scenarios are reported
explicitly and do not become placeholder tests. No export is allowed if none qualify.

The destination must not exist, cannot traverse links/junctions, cannot overlap the
source project, and is published from a sibling temporary directory after validation.
Exports never replace unrelated files. File hashes, reviewed-case signatures and receipt
bindings form a local integrity manifest; this is not protection against hostile writers
who control both manifest and content. Validation rejects unmanaged executable files.

## Standalone layout

- pages/: one Page Object per observed page, locator properties and reusable methods.
- tests/: approved scenario functions composed from Page Object operations.
- qa_runtime/: self-contained config/scope guard, step recorder, pytest fixture,
  integrity validation, collection/execution and escaped HTML/JSON reporting.
- config/environment.json: reviewed non-secret browser/network configuration.
- review/: only selected scenario snapshots and matching receipts, no raw discovery.
- framework.json / blueprint.json: integrity and generation provenance.
- pyproject.toml / requirements.txt / pytest.ini / README.md: standalone dependencies,
  setup, collection, execution and evidence instructions.

The exported runtime imports no AutoQA package. Network scope derives from the existing
trusted Scope implementation, copied with a standalone validated Config model. Browser
cookies/state and client artifacts are never copied. Dependency pins come from the
builder's resolved runtime distributions; the standalone environment resolves its own lock.

## Evidence and lifecycle

Each executed navigation, action and assertion has its own step context, sequence,
run/test identity, status, UTC timestamp, duration and generic error. Only entered
operations emit records; absent operations never acquire outcomes. Skips and interrupts
are distinct. Screenshot policies remain every_step/failures_only/disabled; traces have
separate controls and may include sensitive DOM/images. Capture failures are separate
from assertion failures. No input values or raw assertion errors enter step descriptions.

Runner validates first, collects before execution, uses a restricted subprocess
environment and bounded timeout, ingests actual JUnit and emits NOT_EXECUTED for missing
cases. Reports bind evidence to the current run and test and escape untrusted content.
This remains trusted-local execution, not an OS sandbox or authenticated service.

## Acceptance strategy

Unit tests cover authorization, receipts, unsupported scenarios, unsafe paths, integrity,
step failures/skips/interrupts, capture policies and CLI compatibility. Owned-local
browser acceptance exports functional scenarios, resolves standalone dependencies,
collects/runs without AutoQA installed, and demonstrates pass/defect/restore outcomes.
Final audit reports actual verification per requirement, preserving frozen fixtures.
