# AutoQA V0.5.0 stable release gate

Review date: 2026-11-23. Branch: `feat/v05-development`. Existing PR: #3.
Approved candidate: `e0887ded21cdcf52f24538403de5246fe9fbc219` / 0.5.0rc1.
Retained v0.4.0/main baseline: `41b940642c389bb426cd6fb836178a99453f4792`.
Target package/import/export version: **0.5.0**.

## Decision and operating scope

This promotion prepares the existing implementation for stable release review within
its verified trusted-local professional QA Automation Engineering scope. AutoQA
supports its owner's services; it is not a SaaS platform or certification of arbitrary
client infrastructure. No V0.6 work is included.

A fresh fetch verified the clean approved candidate branch, correct origin, unchanged
main baseline and complete V0.4 ancestry. PR #3 was open against main, mergeable and
at the approved HEAD. Exact-candidate CI run 45272107793 succeeded. That prior result
is not substituted for the promoted HEAD's required new hosted CI.

The [candidate audit](v05-release-candidate.md) remains unchanged historical evidence,
including its initial and subsequent review results. Historical V0.4 audits and
fixtures remain unchanged. The [architecture](v05-architecture.md) describes the
retained design; this gate supersedes its candidate package-version statements.

## Delivered functionality

- Strict versioned API request, response assertion, environment, authentication
  reference, data fixture, sensitivity and result contracts. Existing project-bound
  manual review and independent approval receipts bind the complete API contract.
- Approved GET/POST/PUT/PATCH/DELETE generation with literal paths, query parameters,
  nonsecret headers, JSON bodies, status/header/JSON field and basic shape assertions.
  Non-GET methods require an explicit reviewed mutation statement. Unsupported approved
  cases are reported; pending/rejected cases never become executable tests.
- Bearer, HTTP Basic and cookie credentials supplied through declared AUTOQA_SECRET_*
  environment references. Missing credentials fail. Reviewed legitimate browser session
  cookies are supported without session acquisition, login bypass or AutoQA user identity.
- Named JSON rows, local seeded synthetic IDs, isolated mappings and parameterized
  results. Named reviewed environments supply nonsecret values; unknown selection fails.
- Combined standalone UI Page Objects, API service classes, tests, shared fixtures,
  reviewed configuration, declared dependencies and setup instructions. AutoQA is not
  needed for independent validation, collection or execution.
- Collection-first bounded runner, actual parameterized JUnit/JSON outcomes, entered
  operation evidence, conservative diagnostics and escaped HTML reports. API/authenticated
  exports restrict persistent capture to safe summaries and disable screenshots/traces.
- Additive plan-api and retained build-framework/validate-framework/run-framework CLI;
  existing V0.4 interfaces remain. Legacy generate/run stays UI-only with coarse steps.
- Reusable release script for metadata, Ruff, locked consistency, regression, frozen
  compatibility, build, installed-wheel smoke and standalone export validation/collection.

See [README](../README.md), [CLI reference](cli-reference.md) and
[security boundaries](security.md) for exact usage and prerequisites.

## Stable version alignment

Only metadata, the existing version assertion and current documentation change.
No runtime algorithm, approval contract, architecture or dependency resolution changes.

| Surface | Required value |
| --- | --- |
| pyproject.toml project | 0.5.0 |
| autoqa.__version__ | 0.5.0 |
| uv.lock root editable package | 0.5.0 |
| Installed distribution metadata and import | 0.5.0 |
| New framework.json and exported pyproject.toml | 0.5.0, inherited from package version |
| Version-specific regression assertion | 0.5.0; behavioral assertions retained |

The exporter already derives both version surfaces from autoqa.__version__; it needs
no implementation change. Historical domain/manifest schema versions and historical
exports are not rewritten. A parsed lock comparison verifies the root version is the
only change; all 37 package dependency resolutions remain unchanged.

## Current local verification

The complete reusable release script returned **exit 0** on Windows/Python 3.14.3.
Disposable outputs use ignored `.test-work/release-gate-22uohfvy` directories. Exact
promoted HEAD and hosted CI results are recorded in PR #3 and the delivery report,
avoiding claims based on earlier heads.

| Gate | Actual result |
| --- | --- |
| Full intended non-browser regression, live AI ignored | **251 passed / 18 deselected in 160.48s** |
| Focused reliability regressions before promotion | **12 passed in 3.35s**, including native Windows handle |
| Ruff lint and format | Passed; **61 files** already formatted |
| Lock consistency and resolution comparison | Passed; **37 packages**, root version is the only lock change |
| Root project/import/installed editable metadata | **0.5.0** |
| Wheel and sdist | Built as **0.5.0**; private/disposable paths excluded by inventory gate |
| Isolated installed wheel | Site-packages import/distribution version **0.5.0** and CLI help passed |
| Approved API export from installed wheel | Pending import, explicit approval, build and validation passed |
| Export manifest and generated pyproject | Both **0.5.0**, asserted by the reusable script |
| Independent framework | Dependencies installed; AutoQA absent; validation and collection passed |
| Frozen compatibility | Archives and every member hash match; no fixture tree changes |
| Historical audits and runtime | Unchanged; only package version changes in source |
| Scoped credential/tracked inventory review | No conventional credential matches or private/disposable tracked directories |

Exports pin the builder's direct runtime requirements and resolve their own transitive
dependencies with uv sync; they do not reuse the root lock as a standalone lockfile.
No missing prerequisite or failing test was converted to success. API regression includes
actual owned-loopback defect/restoration, missing credentials and artifact sensitivity
checks. Browser acceptance is preserved historical evidence, not a new browser run.

## Reliability protections and residual risk

Before promotion, the existing focused reliability suite passed **12 tests in 3.35s**
on Windows, including the native CreateFileW sharing-handle test. It was not skipped.

Duplicate JUnit identities produce ERROR rather than allowing a later pass to hide
an earlier failure. PASSED requires nonempty supporting operation records from the
current run/test, with contiguous sequence/step identities and passed states. Missing
or foreign/inconsistent evidence fails. Missing JUnit remains NOT_EXECUTED and nonzero.
Real failures remain failures; no test assertion or execution failure is suppressed.

Atomic persistence closes the temporary file before replacement and retries only
PermissionError at most three times, with 25ms/50ms waits. Permanent denial remains
visible. Tests verify distinct run/row isolation and 256 completed steps with four
workers. Same-identity concurrent writers, hostile filesystem mutation and power-loss
durability are unsupported. Retries do not repeat assertions or HTTP/browser requests.

**The original intermittent API/evidence/JUnit incident's exact root cause was not
demonstrated.** Separate deterministic persistence and reconciliation repros establish
their own behaviors, not the historical cause. This residual historical observation
remains explicit during stable review. No claim of complete historical resolution is made.

## Preserved acceptance and compatibility

Owned-local independent API acceptance verifies **2 PASS / 2 FAIL with controlled
response defect / 2 PASS restored**; missing bearer credentials yield two real failures
before HTTP. Current non-browser regression reruns these actual contracts with synthetic
data, checks masking and parameter identities and asserts AutoQA is absent independently.

Preserved Windows/Chromium combined standalone acceptance verifies two passes with
valid supplied cookie and one API pass plus one UI error without it, with no sensitive
capture or credential values in artifacts. Metadata-only promotion does not change
browser behavior; browser suites and historical external benchmarks are not repeated.
The historical V0.4 **9 PASS / 7 PASS + 2 FAIL / 9 PASS** evidence remains untouched.

All original V0.4 and V0.5 commits remain ancestors. Frozen V0.1/V0.2 archive hashes,
every member hash and fixture tree remain intact. V0.4 UI contracts, CLI interfaces,
approval receipt format, legacy generated formats and report readers are preserved.
Current API/UI non-browser regression checks the existing implementation; it does not
claim full browser/platform certification. Linux hosted checks are non-browser only.

## Security and final inventory review

API contracts review exact origins, methods, paths, expected responses and mutation
scope. DNS answers are classified; connections use validated pinned addresses with TLS
hostname verification/SNI retained. Redirects are prohibited. Private LAN/metadata
targets and wildcard grants are unsupported. Remote API and authenticated UI require
HTTPS except explicitly allowed owned loopback. API ignores the legacy UI base override.
Socket/read limits, the parent subprocess deadline and 1 MiB response cap remain.
OS DNS resolution has no separate cancellation primitive.

Only declared environment credential references are exported and forwarded. Credentials
are not embedded in generated Python, manifests or approvals. Source-backed execution
rechecks current receipts; independent delivery validates its review snapshot and cannot
observe later source revocation. Paths reject traversal, links/junctions, source overlap
and existing output destinations; unmanaged code/integrity changes fail validation.

Summary-only API/authenticated evidence omits HTTP bodies and header values, sanitizes
JUnit failure details before serialization and suppresses raw persistent console details.
Header names appear masked. Status, duration and run/test/row/operation associations
remain genuine. Screenshots/traces are disabled rather than claimed redacted. Summaries
remain until operator removal; automatic age-based purging is absent. Unauthenticated
UI-only and legacy capture retain their historical sensitivity limitations.

The trust model remains a local operator and trusted filesystem, unsigned approval
receipts, single-writer storage and no authenticated multi-user identity guarantee.
There is no OS sandbox. Windows descendant-process cancellation is limited. Conventional
sensitive keys are rejected, but universal secret/PII detection and arbitrary-value
redaction are absent. Operators must review client inputs and evidence before sharing.

Tracked and package inventories are reviewed for credentials, private projects, local
venvs, generated frameworks, screenshots, run evidence and disposable build output.
Synthetic declarative examples and frozen archives remain intentional source fixtures.
Scoped pattern/inventory checks do not constitute a forensic audit of all Git history.
Only owned services and synthetic credentials/data are used for acceptance; dependency
registries are the only external installation dependency. No client system is tested.

## Unsupported functionality and recommendation

No full JSON Schema/OpenAPI engine, API discovery, pagination/streaming/multipart,
request retries, remote setup/teardown or rollback, automatic login/session refresh,
cloud dashboard, remote multi-user operation or arbitrary AI-generated execution.
Richer redaction/retention, authenticated approval history, stronger isolation and
additional platform acceptance remain deferred opportunities, not implemented claims.

Recommend **0.5.0 for stable release within the documented verified trusted-local
scope**, subject to successful exact-promoted-head CI and final owner review of the
explicit limitations and historical residual risk. No unresolved reproducible material
blocker is identified by these gates. Arbitrary client/platform readiness is not claimed.

This workflow updates the existing branch and PR #3 only. It does not merge the PR,
push main, create v0.5.0, publish a GitHub Release, delete branches or begin V0.6.
