# AutoQA V0.4 release candidate

Candidate: **0.4.0rc1**. Local branch: `feat/v04-development`.
Base: annotated `v0.3.0`, main `d26f9088f12b369ea222da6ea3c02176f93b7474`.
Implementation milestone: `6b7faf1` (full final history is reported at delivery).
Work session started 2026-11-20 America/Costa_Rica; acceptance timestamps below are UTC.

## Assessment

**Verified local release candidate for the documented trusted-operator, Python 3.14,
Windows/Chromium scope.** The requested framework builder, approved-scenario compilation,
CLI, standalone execution and operation evidence have working integrated verification.
No mandatory blocker remains identified within that scope. This is not a claim of
universal application compatibility, hosted CI certification or a published release.

AutoQA remains an internal professional QA Automation Engineering tool supporting its
owner's consulting work. No SaaS, billing, dashboard, FastAPI or MCP service was added.
No V0.4 push, PR, merge or tag was performed. Main and v0.3.0 remain unchanged.

## Architecture and implementation

[FrameworkService](../src/autoqa/framework.py) is an additive application service;
[ApplicationEngine](../src/autoqa/application.py) exposes build/run operations and the
CLI grants project-bound generation/execution intent. It reuses existing planning,
independent receipts, scenario signatures, browser evidence, functional-contract
validation and trusted rendering. It does not regenerate approvals.

Validated V0.4 blueprints define pages, checked locator properties, reusable operations,
scenario sequences and explicit unsupported results. Relationships and normalized case
identities are checked. Heading/navigation expectations must match the trusted observed
baseline; functional expectations must match the canonical reviewed contract. Unsupported
approved scenarios are listed, never emitted as placeholders. No supported cases means
export fails. Pending/rejected scenarios do not become tests.

Page Objects encapsulate named locator properties and reusable navigation/action/assertion
methods. Method suffixes are deterministic code identities; readable prefixes describe
the operation. Generated scenario tests compose those methods. Source is compiled from
trusted templates and AST transformations, formatted and linted without importing it.
Values use Python literals; no AI output or arbitrary blueprint code is accepted by CLI.

The runtime is copied into the export with self-contained Pydantic config and the existing
Chromium Scope guard. Its fixture, step recorder, integrity checks, bounded runner and
escaped reports require no AutoQA installation. Only reviewed config/case/receipt data is
exported; source code repositories, raw discovery, browser auth state and prior evidence
are excluded. [Architecture design](v04-architecture.md) documents the boundaries.

## Actual CLI workflow

First use the existing init/explore/plan workflow and review the matrix before explicitly
approving IDs. For functional cases, import reviewed behavior contracts with
`plan --requirements FILE` before approval. Then, from the AutoQA repository:

```powershell
uv sync --locked
uv run playwright install chromium
# The destination parent must already exist. Use a new directory for every export.
uv run autoqa build-framework .test-work/client-framework --project projects/client-a --approved
uv run autoqa validate-framework .test-work/client-framework
uv run autoqa run-framework .test-work/client-framework --project projects/client-a
```

The application must be running separately. Destination traversal (`..`), existing
directories, symlink/junction components and overlap with the source project are rejected.
The builder stages and validates output before renaming a new sibling directory; it never
replaces an existing export or unrelated files. Ruff must be installed in the builder
environment; default `uv sync --locked` includes the dev dependency.

Independent delivery, from inside the export:

```powershell
uv sync
uv run playwright install chromium
uv run python -m qa_runtime.runner validate
uv run python -m qa_runtime.runner collect
uv run python -m qa_runtime.runner run
```

Direct dependency versions are pinned to the builder's resolved distributions; standalone
uv resolves transitive dependencies into its own lockfile. Pip installation from
requirements.txt is also documented in every export. AutoQA's own lock resolutions are
unchanged; only the root package version changed to 0.4.0rc1.

`run-framework` uses AutoQA's interpreter and rechecks the selected project's **current**
case approvals/receipts. The independent runner validates only its exported snapshot.
Collection and execution failures propagate nonzero exit codes; missing JUnit cases
remain NOT_EXECUTED. Collection never creates fabricated passing results.

## Generated layout

```text
framework.json                  unsigned file/case integrity manifest
blueprint.json                  page/operation/scenario map and unsupported list
config/environment.json         reviewed browser/network environment snapshot
review/cases.json                selected supported approved case snapshots
review/receipts.json             matching independently persisted receipts
pages/page_<identity>.py         Page Objects, checked locator properties, operations
tests/test_approved.py           composed approved scenario functions
tests/conftest.py                reusable runtime fixture import
qa_runtime/config.py            standalone validated configuration
qa_runtime/security.py          existing exact-origin/read-only Chromium policy
qa_runtime/fixture.py            browser lifecycle, trace and recorder integration
qa_runtime/evidence.py           per-entered-operation recording
qa_runtime/integrity.py          paths, file digests and approval binding
qa_runtime/runner.py             validate/collect/run, diagnosis and HTML/JSON reports
pyproject.toml / requirements.txt / pytest.ini / README.md / .gitignore
artifacts/RUN_ID/                actual JUnit/logs/results/diagnosis/report and evidence
```

## Acceptance evidence

Owned Supply Lab was served on loopback with explicit localhost permission. Discovery
observed its pages/controls. Eight reviewed functional contracts plus an observed product
navigation scenario were explicitly approved, then exported. The standalone environment
was created with `uv sync --offline` using declared dependencies. A subprocess assertion
confirmed `importlib.util.find_spec('autoqa') is None`, while importing its declared
Playwright/Pytest/Pydantic/YAML dependencies. Nine tests were successfully collected.

| Independent execution | Outcomes | Recorded operations | Screenshots | Traces |
| --- | --- | ---: | ---: | ---: |
| Healthy `20261121T001605-85a25e43` | 9 passed | 34 | 34 | 9 |
| Search defect `20261121T001637-69d7a4df` | 7 passed / 2 failed | 32 | 32 | 9 |
| Restored `20261121T001738-4c91f1a7` | 9 passed | 34 | 34 | 9 |

Only TC-F-search-found and TC-F-search-empty failed under the controlled search defect.
Their assertion steps failed, later unentered steps were absent, and diagnostics linked
only their own current-run evidence. Assertions were not weakened. The suite exercised
search, empty states, select/filter, ordering, native form validity, boundary input,
explicit local form validation and product navigation. Every screenshot/trace reference
was checked for existence. HTML and JSON reports were produced for all three runs.

Evidence remains under ignored `.test-work/v04-independent-verified/`. Initial acceptance
with an artificially reduced 1500 ms navigation timeout also recorded a product-link
navigation timeout despite arriving at its destination. The test was corrected to use
the normal project timeout; the complete pass/defect/restore acceptance then passed in
157.72s. No failing outcome was hidden. Later hardening added canonical expectation
checks and readable method/locator names; final source regression and the installed-wheel
builder/validation/collection smoke verified those changes without repeating all browsers.

## Verification results

| Gate | Actual result |
| --- | --- |
| V0.3 baseline before edits | 180 passed, 14 browser tests deselected; lint/format passed |
| Final non-browser regression | **203 passed, 17 browser tests deselected**, 82.60s |
| Standalone pass/defect/restore acceptance | **1 passed**, 157.72s; internal outcomes above |
| New browser configuration/CLI + legacy vertical/failure tests | **4 passed**, 158.92s |
| Export determinism and final CLI/integrity smoke | **1 passed**, 19.33s |
| Ruff check / format | Passed; 52 files formatted |
| Root lock consistency | Passed offline; same 37 package resolutions |
| Wheel and sdist | Built successfully as 0.4.0rc1 |
| Isolated installed package | Import from site-packages, installed/import version 0.4.0rc1 and console help passed |
| Installed-wheel builder | Built/validated another 9-case export; all 9 collected |
| Editor diagnostics on changed Python | No errors reported |
| Frozen compatibility | Both archive and internal member hashes unchanged; no diff from v0.3.0 |
| Workflow preservation | No change to either existing GitHub Actions workflow |

The new browser configuration test covered real headless failures-only capture and real
headed execution with screenshots/traces disabled, including expected failed heading
assertions. Unit tests additionally cover every screenshot-policy pass/fail combination,
capture errors, skips, interruption and absent steps. Process-failure tests verify
collection failures and execution timeouts cannot become passing cases.

The first isolated package install lacked cached Ruff and failed offline; a normal
dependency download installed the exact requirements plus Ruff successfully. Installed
smoke commands initially demonstrated rejection of a `..` destination and an incorrect
working directory; absolute destination and export-directory invocation succeeded as
documented. No package fix or assertion bypass was needed.

Commands used (all output disposable and ignored):

```powershell
.venv/Scripts/python.exe -m pytest tests -m 'not browser' --ignore=tests/test_live_ai.py -q -p no:cacheprovider --basetemp=.test-work/v04-final-regression
.venv/Scripts/python.exe -m pytest tests/test_framework.py::test_standalone_framework_pass_defect_restore -q -p no:cacheprovider --basetemp=.test-work/v04-independent-verified
.venv/Scripts/python.exe -m pytest tests/test_framework.py::test_framework_browser_configuration_and_cli tests/test_pipeline.py::test_real_browser_vertical_slice tests/test_pipeline.py::test_real_failure_and_report -q -p no:cacheprovider --basetemp=.test-work/v04-browser-compat
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m ruff format --check src tests
uv lock --check --offline
uv build --offline --out-dir .test-work/v04-final-dist
git diff --check
```

## Final review against the mission

This is a separate final review pass in the same development session, using observed
tests/artifact inspection; no external reviewer or separate review agent is claimed.

| Requirement | Classification | Evidence |
| --- | --- | --- |
| Baseline/history/CLI/receipts/fixtures inspected | VERIFIED | Clean tagged base and pre-edit regression |
| Modular additive architecture | VERIFIED | Service/application/CLI tests; retained legacy regression |
| Deterministic complete standalone framework | VERIFIED | Equal manifests for repeated exports; installed-wheel export; independent environment |
| POM/locators/fixtures/config/dependencies/docs | VERIFIED | Artifact inspection, generated-code validation and real acceptance |
| Only supported approved tests; unsupported explicit | VERIFIED | Receipt, unapproved, manual and unrepresentable-expectation tests |
| Per-operation evidence and capture policies | VERIFIED | 34/32/34 actual operations, policy/skip/interruption/error tests and headed/headless tests |
| CLI build/validate/run and review workflow | VERIFIED | Real CLI browser tests, help/signatures and installed-console smoke |
| Standalone dependency resolution/collection/browser execution | VERIFIED | No AutoQA installed; actual 9 / 7+2 / 9 outcomes |
| Readable run-scoped report/diagnostics | VERIFIED | Actual output and cross-run/test/escape regression tests |
| Approval/path/file integrity preserved | VERIFIED | Source and exported receipt mutation, unmanaged code, changed file and path/link tests |
| Historical compatibility and local delivery | VERIFIED | Full non-browser regression, legacy browser slice, unchanged fixture hashes and local commits |
| Browser execution on other OS/platform versions | PARTIALLY VERIFIED | New runtime tested on Windows/Chromium only; portable source is not cross-platform certification |
| Every supported functional action branch in a real browser | PARTIALLY VERIFIED | Owned contract set exercised above; check/uncheck/hidden branches reuse templates but have no new browser acceptance |
| Authenticated/multi-user/hostile-filesystem/OS sandbox features | NOT IMPLEMENTED | Explicitly deferred; not part of this local engine candidate |

## Security review and limits

Project-bound generate/execute checks reject absent/mismatched authorization. Building
requires receipts that match current case signatures/revisions. Running through AutoQA
rechecks source approvals. Exported standalone validation checks matching snapshots,
receipts and file hashes; updating a single receipt-file digest cannot repair a changed
scenario-signature binding. No approval is inferred from AI or silently regenerated.

Unsigned local manifests/receipts are not tamper-proof against a writer controlling all
inputs. Standalone exports cannot receive later source revocation. Configuration is an
immutable reviewed snapshot for integrity purposes: changes require a new export.
AuthorizationContext remains intent rather than authenticated identity. Storage/export
assume a trusted single writer; hostile concurrent path replacement is not solved.
Subprocesses are bounded and use a reduced environment, not an OS sandbox. Complete
descendant-process cancellation on Windows remains a known limit.

Step descriptions/errors omit input values and raw assertion details. Screenshot/trace
capture errors remain separate from scenario outcomes. Raw JUnit/logs and browser
images/DOM can still contain sensitive data; standalone screenshot disabling does not
disable trace images. Sensitivity metadata, redaction and retention automation remain
future work. File-backed evidence is scoped to its unique run and corresponding case.

Common private-key/GitHub/OpenAI/AWS credential-pattern scans found no hits in inspected
source/docs/examples/tests or decompressed frozen fixtures. Exports also reject common
credential material before writing. This is not a general DLP/secret detection guarantee;
operators must review contract values and evidence. No production/client evidence or
credentials were used. Projects, venvs, acceptance evidence and package output remain
ignored. The wheel contains package/template/metadata only, not test or client artifacts.

The legacy generate/run evidence format remains coarse by design; the upgraded operation
model applies to V0.4 standalone exports. Existing V0.3 domain versions, signatures,
wire manifests, reports and frozen archives remain readable and unchanged. Hosted V0.4
CI, live AI, external sites, auth sessions, remote clones and arbitrary scripts were not
tested or added. They must not be represented as delivered capabilities.

## V0.5 recommendations

1. Unify framework blueprints/operation results with historical domain contracts while
   preserving legacy read semantics and actual missing/skipped/interrupted outcomes.
2. Add richer sensitivity annotations, reviewed redaction and artifact retention controls.
3. Add authenticated approval identity, durable revision/revocation history and concurrency
   control before exposing the engine to multiple users or remote interfaces.
4. Verify process-tree cancellation and OS isolation across supported platforms.
5. Expand controlled browser acceptance to the remaining functional-action branches and
   eventually verify hosted CI. Keep client provisioning manual/private and explicit.

No blocker remains for local RC review in the verified scope. Public publication,
additional platforms and production-client adoption require their own review decisions.
