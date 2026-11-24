# AutoQA V0.6 release candidate - 0.6.0rc1

Engineering date: 2026-11-23. Branch: feat/v06-development.
Baseline: official annotated v0.5.0 at 590832c229f9177c20eb4b928f78beac42488523.
PR #3 was merged with parents v0.4.0 and approved V0.5 HEAD
43b6555cb2005817042f82020c0ae33215830e52, preserving all V0.5 commits.
Remote annotated tag object: 67e37cf6dccef436567e6a1618bcb7a8f6446041.
Its peeled target equals integrated main. V0.5 exact-head CI run 45277071807 succeeded.
No GitHub Release entry was created. Historical V0.4/V0.5 audits are retained.

## Delivered scope

| Capability | Classification | Evidence/boundary |
| --- | --- | --- |
| Static framework analyzer and create/improve decision | VERIFIED | Owned empty/supported/unsupported/read-only/blocked repositories; no execution/install/write |
| Versioned suite/pack/case/selection/plan/run/result contracts | VERIFIED | Strict additive 0.6 models; historical data not rewritten |
| Reviewed membership and proposal builder | VERIFIED | Digest-bound sidecar, full audit snapshot, factual API/priority proposals, explicit assignment |
| Single, pack, suite, tag and full selection | VERIFIED | Stable identities, deterministic overlap deduplication, rejection without requests |
| Independent exported selection | VERIFIED | Fresh environment without AutoQA; real owned loopback API execution |
| Scope-aware JSON/HTML accounting | VERIFIED | Separate logical case and parameter invocation counts; missing/ambiguous/unsupported failure |
| V0.5 reliability protections | VERIFIED | Existing duplicate/current-run/Windows persistence regressions retained; complete operation-count check added |
| Arbitrary framework understanding/refactoring | NOT IMPLEMENTED | Heuristic static inspection only; no automatic client source modifications |
| Multiple managed suites per project | NOT IMPLEMENTED | One named suite, multiple reusable packs initially |
| Multi-platform browser acceptance | PARTIALLY VERIFIED | Windows/Chromium focused acceptance only; Linux CI is non-browser |
| OS sandbox, multi-user identity, signed receipts, universal redaction | NOT IMPLEMENTED | Trusted-local boundaries retained |

## Acceptance and quality evidence

Local reusable release script completed with exit **0**, Windows/Python 3.14.3:

- Full intended non-browser regression: **280 passed / 18 deselected in 271.17s**;
  live AI explicitly excluded. No unexpected failure or skip on Windows.
- Ruff lint/format: passed, **66 files**. Lock check: passed, 37 resolved packages;
  dependency resolutions unchanged, only root version moves to 0.6.0rc1.
- Focused final typed-run/reliability regression: **19 passed in 19.74s**, including
  native Windows sharing-handle behavior and bounded 256-step distinct-writer stress.
- Focused CLI UTF-8/BOM suite approval and conflicting selection check: **1 passed
  in 3.13s**. JSON proposal remains parseable and scenario approval stays separate.
- Focused combined independent Windows/Chromium acceptance: **1 passed in 73.21s**.
  With cookie: 2 passes; without cookie: 1 API pass + 1 UI error. Additional UI
  single-case and UI pack each pass with 2 operation records and selected-scope label.
- Wheel/sdist, isolated installed-package version/import/CLI, approved API export,
  independent dependency installation, validation and collection passed.
- Final post-serialization package verification: passed with exit **0**; fresh wheel/sdist/install/export and independent single/pack/all each passed (1 case, 1 invocation, 2 operations per run).
- Package/import/root lock/installed distribution/export manifest/generated pyproject
  all assert **0.6.0rc1**. Independent environment asserts AutoQA is absent.
- Frozen v0.1/v0.2 archive and every member hash verified by compatibility regression;
  Git diff against v0.5.0 confirms frozen fixtures and V0.4/V0.5 audits unchanged.
- Scoped tracked/new inventory: **127 files** reviewed; no conventional credential
  matches, private projects, evidence, screenshots, local venv or disposable output.
  Wheel and sdist inventories independently exclude private/disposable directories.

The complete regression preceded the additive typed ExecutionRun serialization and
UTF-8 input edge-case assertions; affected focused regressions and final package
verification were rerun afterwards. Hosted CI exercises the final committed tree.
No pending check is treated as successful. Tests use synthetic data and owned local services;
no client system, external benchmark or live AI provider is contacted.

The new independent API acceptance inventory contains four cases: two eligible
approved-enabled cases (one with two rows), one disabled approved case and one
pending case. Single: 2 passed invocations / 4 operations / 1 logical passed case.
Pack: 3 passed invocations / 6 operations / 2 logical passed cases. Overlapping
packs execute 3 invocations, not 4. Tag and named suite are separately exercised.
Complete regression: 3 PASS / introduced defect 3 FAIL / restored 3 PASS, six actual
operations each. Invalid/disabled/pending/empty requests produce no server hits.
Current source membership changes invalidate a prior source-backed export.

Deterministic reconciliation acceptance covers partial selections, missing and
malformed JUnit, duplicate identities, unexpected identities, missing operation
tails, skipped outcomes and unsupported/mixed scope. A failed or incomplete run
remains nonzero; no assertion was weakened to obtain a green result.

V0.5 owned API/auth/data and V0.4 interface/frozen compatibility remain regression
gates. Historical V0.4 9 PASS / 7 PASS + 2 FAIL / 9 PASS evidence is preserved, not
presented as a newly repeated benchmark. The original intermittent V0.5 incident's
exact root cause remains historically unproven; deterministic repairs do not prove
that cause or justify claiming complete historical resolution.

## Security and compatibility audit

Analyzer source is never executed or installed; traversal, links/junctions, unreadable
paths and budgets block incomplete inspection. Existing framework files are never
overwritten. Suite review modifies only explicit AutoQA metadata, not client tests.
Selection accepts reviewed stable IDs rather than shell/Pytest expressions. Scenario
receipts remain independent of membership approval. Source execution rechecks
scenario and membership snapshots. Run IDs and parameter-row identities remain
isolated; missing/duplicate/foreign evidence cannot become PASSED. Atomic persistence
retries remain bounded and permanent errors visible; same-identity writers unsupported.

API exact origins/methods/paths, DNS classification/pinning, redirect rejection,
HTTPS/loopback boundary, timeout/response-size limits and environment-only secret
references remain unchanged. API/authenticated capture remains summary-only; no
raw credentials/payloads, screenshots or traces are added by management reporting.
Tags/inventory and unauthed/legacy evidence still need operator sensitivity review.

Trusted local operator/filesystem; unsigned approval receipts; no OS sandbox or
multi-user identity guarantee; no universal PII redaction; manual retention; limited
Windows process-tree cancellation; no complete cross-platform browser verification.
Dependency registries are contacted only for installation. Static inspection is
heuristic, not complete framework/runtime coverage. Standalone snapshots cannot
observe later source revocation. Legacy execution retains coarse steps.

## Deferred work and readiness

Deferred: richer static configuration/plugin understanding, multiple managed suites,
stronger identity/signatures and concurrency, richer redaction/retention, OS isolation,
process-tree cancellation and additional browser/platform acceptance. These are not
implemented or claimed. No V0.7 development is included.

This remains **0.6.0rc1**, not stable. Stable promotion requires independent review of
this scope and residual risks plus successful final-head CI. No V0.6 merge, tag or
GitHub Release is authorized by this delivery.


## Hosted verification

The existing pull-request workflow remains independent of client/demo execution:
Python 3.14, locked uv install, Ruff lint/format, full non-browser regression excluding
live AI, and the reusable package phase. The extended package phase now includes
owned-loopback single/pack/full execution as well as wheel/install/independent smoke.
It uses no client secrets or external websites and preserves nonzero failures.

Implementation HEAD **c44b02386e2b33987a87d95f49a1a75de7608362** passed hosted CI:
[run 45284318611](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45284318611),
job 138076545053, completed **success**. Actual job logs inspected:

- CPython **3.14.4 / Linux**, locked install of autoqa-agent **0.6.0rc1**.
- Ruff lint/format passed, **66 files**.
- **279 passed / 1 skipped / 18 deselected in 36.04s**, zero unexpected failures.
  Expected skip: native Windows file-handle test, which passed locally on Windows.
- Wheel/sdist, isolated installed package/import/distribution/CLI, approved export,
  independent dependencies with AutoQA absent, validation/collection all succeeded.
- Independent case/pack/all each exited **0**, with 1 invocation / 2 operations.
- Every job step completed successfully. Linux non-browser results do not certify
  Linux browser execution or arbitrary client compatibility.

[PR #4](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/4) is open against main,
with 25 scoped changed files inspected. Main remains the verified v0.5.0 commit;
GitHub reports no merge conflicts. This documentation-only evidence commit triggers
another run; its exact-final-head result is recorded in the PR delivery status.
No old-head or pending result is treated as final-head success.

**Recommendation:** ready for independent V0.6 candidate review within this explicit
scope, subject to the final documentation-head CI check. No reproducible mandatory
release blocker remains in the executed gates. Stable 0.6.0 promotion is a separate
review decision; this delivery remains 0.6.0rc1 and does not merge/tag the candidate.


## Independent audit remediation: H01 and H02

Audited baseline: 878c2af100cb6a879f2a9822bfebb52a145c31b0, PR #4.
This section supersedes the earlier readiness recommendation for these findings;
the previous local/hosted observations remain historical evidence, not proof that
the findings were absent.

Before repairs, focused reproductions yielded **13 failed / 8 passed in 1.46s**:
plain application manifests and non-collected Python helpers were misclassified;
Cypress TypeScript config was missed; mixed/unsupported or missing/foreign/duplicate
collection output could receive exit 0. These were actual reproducible defects.

H01: build metadata is inspected as bounded data, with recognized test dependency/
configuration indicators distinct from ordinary applications. Default Pytest
module/function/class structure is required for static test candidates. Uncertain
helpers/custom collection or mixed tooling remain partial. No inspected code is
imported/executed, no repository dependency installed and no existing file modified.

H02: collection-only mode reconciles expected parameterized node IDs and the entire
selected inventory, not only the supported subset sent to Pytest. Unsupported,
missing, duplicate, unexpected or failed collection returns nonzero with a separate
collection.json diagnostic. Fully supported collection still succeeds. Historical
manifest scope is adapted explicitly, not silently expanded. Execution-mode JUnit,
current-run evidence and permanent-persistence safeguards remain unchanged.

The independent export acceptance also reproduced an adjacent prerequisite defect:
a non-automatable manual case in an API-only project triggered UI setup with no URL.
A bounded exporter condition now prepares UI scope only for feasible UI candidates;
the manual case remains unsupported rather than disappearing from full scope.
The original manual-case acceptance is retained, not replaced by an easier inventory.

An expanded boundary reproduction additionally yielded **3 failed / 22 deselected
in 2.54s**: default-excluded build/hidden directories still became test facts, and
an unexpected collection node in another Python module was ignored. The second
focused H01/H02 repairs use actual default Pytest directory exclusions and reconcile
foreign Python modules as unexpected. Those three regressions then passed (**3
passed / 22 deselected in 3.14s**). No prior assertion was removed or weakened.

Final repaired-tree non-browser regression on Windows/Python 3.14.3:
**305 passed / 18 deselected in 303.82s**. The suite includes all **25 new audit
regressions**, existing management/overlap/rejection acceptance, owned API healthy/
defect/restored execution, UI standalone collection, JUnit/evidence/persistence
reliability and frozen compatibility. Ruff lint/format passed (**67 files**), lock
consistency passed, and editor diagnostics reported no errors. Package/import/lock
version remains 0.6.0rc1; dependency resolutions are unchanged.

An intermediate full run had **1 failed / 301 passed / 18 deselected in 392.81s**,
reproducing the manual-case exporter condition described above. It was not treated
as success; the original scenario is retained and passes after the bounded fix.
The final full regression above follows both audit boundary repairs.

The complete reusable release script (`--phase all`) finished with **exit 0**.
Wheel and sdist built; isolated installed distribution/import/CLI assert 0.6.0rc1;
approved API export and independent dependency installation passed with AutoQA absent.
Standalone validation and fully supported collection passed (COMPLETE, no missing,
unsupported, duplicate or unexpected nodes). Single/pack/all execution each passed
with one invocation and two actual operations. Package inventories exclude private
projects, local environments, evidence and disposable output.

No full browser benchmark was repeated: the changed runner branch is collection-only,
and existing non-browser API execution plus real UI collection exercise the affected
boundaries. Prior Windows/Chromium execution evidence remains historical; these
repairs do not add platform/browser certification. Scoped inventory review covered
128 tracked/new files, with no conventional credential or private/disposable path
findings. Frozen fixtures, V0.5 historical audits, package version and lock are
unchanged against the audited HEAD.

The tests use owned loopback services, synthetic cases and fresh independent
exports. Collection asserts zero server requests, no execution results and no step
evidence for supported, unsupported, mixed/full and rejected selections. No client
system or real credential is used. Historical V0.5 audits/data and frozen fixtures
remain unchanged; version remains **0.6.0rc1**, with no dependency changes.

Remediation implementation HEAD **e90921663a0915f953422dd71f543f7cb31310ab** passed
[Actions run 45291754560](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45291754560),
job 138101980841, completed **success**. Actual job logs inspected:

- Python **3.14.4 / Linux**, locked installation, Ruff lint/format (**67 files**).
- **304 passed / 1 skipped / 18 deselected in 42.99s**, zero unexpected failures.
  The native Windows handle test skips on Linux and passed in the local Windows run.
- Wheel/sdist, isolated installed CLI/package version **0.6.0rc1**, approved export,
  independent dependency installation with AutoQA absent, validation/collection and
  single/pack/full execution all succeeded. Every workflow job step passed.

The existing PR #4 targets main and includes all corrections. Only seven files differ
from the audited baseline; existing assertions, historical audits and fixtures remain.
This documentation-only evidence commit triggers a further run; the PR delivery
status records its actual final-head result. No earlier-head or pending CI result
is treated as final-head success.

H01 and H02 are **VERIFIED within the documented scope**; no reproduced mandatory
blocker remains after these repairs. Recommend a new independent candidate audit,
subject to the final documentation-head CI check. This remains **0.6.0rc1**; stable
promotion and merge require separate review/authorization. Linux non-browser CI
adds no Linux browser certification.

No stable promotion, merge, V0.6 tag, main push or new release entry is included.
Static-analysis and trusted-local limitations remain as documented; these repairs
do not prove complete framework coverage, sandboxing or multi-platform browser
readiness. The historical V0.5 intermittent incident remains unroot-caused.
