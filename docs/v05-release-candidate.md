# AutoQA V0.5 release candidate — 0.5.0rc1

Local engineering review date: 2026-11-23. Development branch:
`feat/v05-development`. Official base: annotated `v0.4.0`, target
`41b940642c389bb426cd6fb836178a99453f4792`.

AutoQA is a local professional QA Automation Engineering tool for its owner's
consulting work. This is a release candidate, not a stable release, hosted SaaS
platform or universal client-system certification. The initial delivery was local-only.
The subsequent engineering review authorizes publishing feat/v05-development and
one review PR into main, with hosted CI verification. Merge, stable promotion, tags,
GitHub Release, visibility changes and V0.6 implementation remain unauthorized.

## Functionality classification

| Capability | Classification | Verified scope / boundary |
| --- | --- | --- |
| Versioned API contracts | VERIFIED | Strict 0.5 request/assertion/auth/data/environment/evidence/result models |
| Approval integrity | VERIFIED | Same manual approval receipts; full API contract signature; changed input returns pending |
| HTTP API generation | VERIFIED | GET/POST/PUT/PATCH/DELETE, query, headers, JSON bodies, explicit mutation review |
| Response assertions | VERIFIED | Exact status/header/JSON fields and basic dotted-path JSON shape/types; actual failures preserved |
| Application authentication | VERIFIED | No auth, env bearer, env Basic and supplied session cookie against owned loopback fixtures |
| Browser session authentication | VERIFIED | Legitimate supplied cookie, focused Windows/Chromium combined standalone acceptance |
| Deterministic test data | VERIFIED | Named JSON rows, seeded synthetic IDs, isolated mappings and parameterized cases |
| Remote setup/teardown | NOT IMPLEMENTED | Operator owns remote state lifecycle; local fixture lifetime cleans up owned resources |
| Sensitive evidence restriction | VERIFIED | Summary-only API/auth exports; masked headers, no raw payload/console/JUnit detail or browser capture |
| Universal PII/screenshot/trace redaction | NOT IMPLEMENTED | Capture is restricted; no pixel/trace sanitization claim |
| Retention | PARTIALLY VERIFIED | Summary-only retention implemented; summaries retained until manual removal; no age-based purge |
| Combined export/independence | VERIFIED | UI Page Objects and API service/tests share standalone runtime; AutoQA absent in independent execution |
| Network boundaries | VERIFIED | Local refusal, DNS pinning, no redirect, reviewed environment/method/path, size/timeout controls |
| Hosted HTTPS deployment | PARTIALLY VERIFIED | Standard-library TLS verification retained; no owned hosted HTTPS integration/certificate/platform acceptance |
| Reusable quality gates | VERIFIED | Local script and reviewed CI definition; failures propagate |
| Hosted V0.5 CI | BLOCKED | Publication was not authorized for the initial local-only delivery; see subsequent review below |
| Historical compatibility | VERIFIED | Frozen V0.1/V0.2 members and unchanged archives; legacy UI/non-browser regression; focused V0.4 browser case |
| Broad browser/platform/client certification | NOT IMPLEMENTED | Focused Windows/Python 3.14/Chromium only |

## Initial local delivery verification (historical)

| Final gate | Actual result |
| --- | --- |
| Non-browser regression (live AI ignored) | **241 passed / 18 deselected, 111.71s** |
| Ruff lint and format | Passed; **60 files** already formatted |
| uv lock consistency | Passed; **37 packages**, unchanged dependency resolutions |
| Package/import/root lock/installed metadata | **0.5.0rc1** |
| Wheel and sdist | Built; path inventories exclude private/disposable directories |
| Isolated installed wheel | Import/distribution version and CLI help passed from site-packages |
| Installed-wheel approved export | CLI import → pending → explicit approval → build → validation passed |
| Standalone package smoke | Dependencies installed, AutoQA absent, integrity validation and collection passed |
| Independent API execution | Actual 2 PASS / 2 FAIL / 2 PASS plus missing-auth failure, assertions retained |
| Focused combined authenticated browser | 1 acceptance test passed, 30.94s (2 child passes; missing cookie yields 1 pass + 1 error) |
| Focused V0.4 browser regression | 1 acceptance test passed, 51.26s |
| Frozen compatibility | Both archive hashes and every member hash match; no fixture/audit changes |
| Editor diagnostics, YAML, examples | No diagnostics in reviewed files; workflow and example contract validation passed |
| Scoped tracked-file credential review | No conventional credential-pattern matches |

The final reusable checks stage completed successfully. The package stage also passed
in a fresh `.test-work/release-gate-ns1c7__m` environment; its wheel Python sources were
compared against the final implementation. A subsequent UTF-8 restoration affects only
the historical project-name error text; final delivery packages are rebuilt from the
committed tree. No runtime behavioral change is hidden behind documentation updates.

Earlier checkpoints passed 93 contract/domain/compatibility tests, 25 V0.4 non-browser
framework tests, 11 first API acceptance tests, 21 security-focused tests and 25
focused evidence/contract tests. These overlap; their counts are not summed.

Package version, Python import and uv.lock root metadata agree on 0.5.0rc1. The
standard-library HTTP client adds no dependency; dependency resolutions remain
unchanged from V0.4 (37 lock packages). New manifest and exported pyproject versions
derive the package version. Framework validation checks approval snapshots,
parameter counts and protected evidence settings.

## Observed API and combined acceptance

Owned ThreadingHTTPServer fixtures use only loopback and synthetic identities/data.
The standalone API acceptance installs declared dependencies into its own environment
and asserts AutoQA is absent. Two parameter rows execute the same reviewed contract:

| Run | Actual result | Recorded operations | Meaning |
| --- | --- | ---: | --- |
| Healthy | 2 PASSED | 4 | Request and assertion for each row |
| Controlled response defect | 2 FAILED | 4 | Responses violate reviewed healthy JSON expectation |
| Restored | 2 PASSED | 4 | Same immutable export; target restored |
| Missing bearer credential | 2 FAILED | 2 | Request operations fail before HTTP; assertions not invented |

Referenced local evidence is kept under ignored `.test-work/v05-api-repro/` and
the final regression's Pytest temporary directories. Representative immutable
reproduction run IDs: `20261123T182759-a5864f99` healthy,
`20261123T182804-35bc930f` defective, `20261123T182811-29cbd5c3` restored and
`20261123T182819-9469e28d` missing credential. These are actual observed outcomes,
not invented snapshots; no generated project/evidence is committed.

Focused combined UI/API acceptance independently installed the export and verified
AutoQA absence. With valid synthetic cookie: 2 PASSED. With missing UI cookie:
1 PASSED API + 1 ERROR UI, nonzero process exit. No screenshot/trace was persisted
and synthetic cookie values were absent from all run artifacts. The final focused
security version of this test passed in 30.94s on Windows/Chromium.

The retained V0.4 headless CLI acceptance passed in 51.26s: actual healthy UI pass,
controlled UI failure and failures-only screenshot/trace behavior. The historical
V0.4 independent 9 PASS / 7 PASS + 2 FAIL / 9 PASS evidence remains unchanged;
its expensive benchmark was not repeated.

## Development failures and focused repairs

- Initial new-contract test used Pytest's reserved `request` parameter. Renamed
  the test parameter; all contract/domain/compatibility tests passed.
- A new browser acceptance test referenced an import removed earlier by Ruff.
  Used the existing ApplicationEngine interface; the focused acceptance passed.
- Extending CI added scripts linting and package/install/export verification.
  The workflow's exact-command assertion initially failed. Updated its expected
  command list while retaining all permission, pinned-action and failure checks.
  The focused workflow test passed; the next full run passed 237 tests / 18 deselected.
- Final response review reproduced a false positive for nested JSON boolean/integer
  values (`true` versus `1` inside an object) under Python container equality. A
  failing regression demonstrated it. Canonical JSON value comparison now preserves
  nested type distinctions; the affected contract/response tests passed (23 tests).
- One intermediate independent API run recorded successful operations but one
  failed JUnit case. Its original sanitized error did not retain the exception
  category, so its exact cause is **not established**. The unchanged acceptance
  passed on focused reproduction and in subsequent full regression. Diagnostics
  now retain phase/exception class without sensitive messages. A separate controlled
  persistence repro confirmed that a transient PermissionError during atomic replace
  immediately failed evidence persistence. The producer now retries only that write
  up to three times (25/50ms waits); permanent failure still raises. Both behaviors
  have explicit tests. This is a bounded persistence repair, not an HTTP/assertion
  retry or proof of the original intermittent cause. Keep this residual observation
  visible during wider Windows acceptance before stable promotion.

## Security and privacy review

API contracts bind exact environment origins, literal request paths, verbs, expected
responses, mutation statements, authentication references, data and evidence policy
to manual receipts. Rejected/pending cases do not execute. Changing the full contract
invalidates approval; source-backed execution rechecks current receipts. Standalone
delivery validates its immutable review snapshot and cannot observe later source
revocation. Trusted writers can alter unsigned receipts/manifests: these are local
integrity checks, not cryptographic reviewer identity.

All DNS answers are checked; only global addresses or explicitly allowed loopback
are supported. The connection uses a validated address and keeps HTTPS hostname
verification/SNI. Redirects never follow; no proxy/wildcard/private LAN access is
granted. Request/read timeouts and the overall child deadline are bounded; response
body is capped at 1 MiB. OS DNS resolution itself has no separate cancel primitive.
No real external application or live AI target was contacted during acceptance;
public package registries are used for installation only.

Credentials are AUTOQA_SECRET_* environment references, not source/manifest/receipt
values. Missing/invalid credentials fail before sending HTTP. Basic/bearer/cookie
positive and missing-auth cases use synthetic local values only. Authenticated UI
is origin-restricted and requires HTTPS except explicitly allowed loopback. No login
bypass, refresh flow, AutoQA identity service or storage-state import exists.

Summary-only evidence omits every HTTP body/header value and restricts raw persistent
console/JUnit diagnostics. Marked header names are shown masked; run/test/row/operation
status and duration remain. Screenshots/traces are disabled rather than claimed
redacted. Permanent evidence I/O failure remains visible. Summaries require manual
retention management. Unauthenticated UI-only and legacy capture remain subject to
their historical privacy risks. Conventional sensitive keys are rejected, but arbitrary
PII/secret strings under innocuous keys still need operator review.

The existing path traversal/link/junction, overlap, overwrite, unmanaged-code and
approval integrity guards remain. No client workspace, credential, generated framework,
venv, report, screenshot or trace is staged. Synthetic declarative examples and frozen
archives are intentional source fixtures. A scoped credential scan and package path
inventory review do not establish a forensic guarantee over all Git history.

## Known limits and V0.6 opportunities

- Trusted single local operator; no authenticated review identity, multi-user transaction
  model or OS sandbox. Windows descendant-process cancellation is still limited.
- JSON shape checking is basic, not complete JSON Schema/OpenAPI validation. No API
  discovery, pagination, multipart/files, streaming, redirect grants or request retries.
- Remote setup/teardown, transaction rollback and production-state reset are not automatic.
- No automatic session acquisition, OAuth refresh or advanced application-authentication flow.
- Sensitive capture is restricted; universal PII detection, fine-grained redaction and
  automatic age-based artifact cleanup remain future work.
- Browser acceptance is focused Windows/Chromium. Public HTTPS infrastructure and other
  platforms require separately owned/authorized acceptance before claims expand.
- Legacy execution retains coarse steps. Unified historical contracts, richer safe
  diagnostics, stronger isolation and durable authenticated approval history are V0.6
  opportunities, not delivered capabilities.
- The intermediate Windows evidence/JUnit discrepancy was not conclusively root-caused;
  no permanent failing acceptance remains, but broader stress acceptance is warranted
  before stable promotion.

## Local delivery decision

Readiness is based on the final gates recorded above, within the bounded local operating
scope only. Mandatory local acceptance gates pass: **ready for local release-candidate
engineering review**, with no permanent failing local test identified. This is not an unconditional stable
release recommendation for arbitrary client infrastructure. Hosted CI/platform coverage
and the residual intermittent observation must remain visible in any later promotion.
The initial delivery evidence above remains historical. The review below supersedes
its local-only publication status; no stable promotion or V0.6 work is included.


## Subsequent engineering review and publication gate

Reviewed baseline HEAD: `cd35aa452ad7b5ae59b78a83dc2a97b35a9ae023`.
A fresh fetch confirmed origin/main remains the exact v0.4.0 baseline. The three
reported development commits, package/import/lock version 0.5.0rc1, frozen archives
and every frozen member hash were verified. Dependency resolutions are unchanged.
The initial working tree was clean. No V0.4 historical audit was edited.

### Reliability findings and bounded repairs

The original intermediate API/JUnit failure was not reproduced during this review.
Its original exception category is unavailable, so **its exact cause remains unknown**.
Do not equate the separate sharing-violation repro with proof of that historical cause.

A real Windows CreateFileW handle with read/write sharing but no delete sharing
reproduced PermissionError on atomic replacement. Closing that handle on the first
bounded retry allowed the completed step to persist. Existing tests verify exactly
three attempts for transient replacement and visible permanent failure. Writes close
the temporary file before replacement. Retries apply only to persistence, not test
assertions, HTTP calls or browser operations; configured waits are 25ms and 50ms.

A bounded ThreadPoolExecutor stress test used four workers, eight run directories,
four row identities per run and eight sequential completed steps per identity:
**256 steps**, all persisted with contiguous identities and genuine PASSED status.
Readback checked every intermediate snapshot. Reading a different run ID returned
no records. Supported concurrency is distinct identities/runs, not multiple writers
for the same test/run file. Same-identity concurrent writers, power-loss durability
and adversarial filesystem mutation remain outside the single-writer trust model.

Two deterministic result-integrity defects were demonstrated with failing tests and
repaired in one focused attempt each:

1. A duplicate JUnit testcase name could overwrite a previous failure with a later
   pass. Duplicate identities now produce ERROR regardless of record order, and a
   nominal zero child exit becomes nonzero. No assertion was weakened.
2. A nominal passing JUnit record with absent or foreign-run step records could pass
   without supporting evidence. Passing results now require nonempty current-run,
   matching-test operation records with contiguous sequence/step identity and PASSED
   state. Missing/inconsistent evidence produces ERROR. Real failed/error JUnit records
   remain failed/error; absent JUnit remains NOT_EXECUTED and nonzero.

The focused contract/reliability set passed **29 tests in 2.66s**. The authenticated
combined standalone browser acceptance passed **1 test in 52.73s**, exercising actual
2 PASS with valid cookie and 1 PASS + 1 ERROR without it, with AutoQA absent.
The original V0.4 9/7+2/9 benchmark was not repeated.

These guards prevent the reproduced false-positive paths. They do not establish a
root cause for the original isolated failure or guarantee crash durability. Residual
historical risk is retained for stable-promotion review; no material unresolved result
corruption path was identified within the tested trusted-local operating scope.

### Current local quality gates

The full reusable checks stage passed on the reviewed implementation:
**251 passed / 18 deselected in 151.26s** (Python 3.14.3, Windows). Ruff lint and
format passed (61 files); locked consistency passed (37 packages), with version
0.5.0rc1 throughout. Browser/live AI suites were excluded from this regression;
the focused authenticated browser result is recorded separately above.

The reusable package stage also passed in `.test-work/release-gate-mxi14c1n`:
wheel/sdist build and inventory checks, isolated wheel import/distribution/CLI,
approved API export/validation, independent dependency installation, AutoQA-absence
assertion and standalone collection all succeeded. Only ignored disposable outputs
were produced. The complete reusable script returned exit 0.

### Security, inventory and CI expectations

Source review and owned-loopback acceptance retain exact reviewed origins/methods/paths,
explicit mutation statements, redirect rejection, DNS classification and pinned socket
connections. Bearer/Basic/cookie credentials are explicit environment references.
Missing-secret, response assertion, unauthorized-target, bounded response/timeout,
seeded data and parameter identities remain covered by the complete non-browser suite.
Authenticated UI routes reject cross-origin resources; its browser capture is disabled.
No real client service, credential or evidence is used in this review.

Tracked inventory and scoped credential-pattern checks found no private workspace,
venv, disposable output or real credential material. Package inventories are checked
by the reusable script. Synthetic contracts/tests and frozen archives are intentional.
These checks are not universal secret/PII detection or a forensic audit of Git history.

Hosted CI must install locked dependencies, run Ruff on src/tests/scripts, run the full
non-browser suite with live AI excluded and execute package/install/export/standalone
smoke gates. The native Windows handle test is expected to skip on Linux; it was
executed locally on Windows. No flaky test is skipped. Linux non-browser success does
not certify Linux browser behavior. The final exact-head hosted result belongs in the
PR and delivery report; an earlier head or pending run cannot satisfy that gate.

All previous security boundaries remain: trusted local operator/filesystem, unsigned
receipts, no AutoQA identity or OS sandbox, limited descendant-process cancellation,
manual summary retention, no universal redaction, no remote setup/teardown and no
arbitrary hosted/client/platform certification. Keep 0.5.0rc1 until a separately
approved stable-promotion decision. No merge, tag or GitHub Release is performed.
