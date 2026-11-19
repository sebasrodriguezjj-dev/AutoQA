# V0.2.1 targeted external compatibility review

Status: implementation patch prepared and verified only on controlled local fixtures. **Awaiting human review of the proposed allowlist.** No external exploration or tests were rerun. No project permissions were broadened, dependencies updated, package rebuilt, or MCP/frontend implementation started. Package metadata remains 0.2.0 pending release handling outside this review.

## Root causes and limits of historical evidence

V0.2 routes every request through the same URL predicate used for page navigation. That predicate rejects all query URLs and every origin other than the initial application origin. A separate documented read-only API therefore cannot load. The HTTP method gate independently rejects everything except GET and HEAD; the observed QUERY requests remain rejected.

The saved workflow-map.json has only origin, method and a generic denial message. No HAR or network trace was saved for external discovery. The exact historical paths, query keys/values, request bodies, redirect chains, ports beyond default origins, and first failing predicate **cannot be recovered**. Do not label documented API endpoints as the paths of those historical requests.

| Stored origin | Method | Recorded count | What is established |
| --- | --- | --- | --- |
| https://api.practicesoftwaretesting.com | GET | 28 | Outside navigation origin; queries may also have failed first. Exact paths/reason order unknown. |
| https://api.practicesoftwaretesting.com | QUERY | 10 | Rejected by the method gate before URL permission. Paths and bodies unknown. |
| https://practicesoftwaretesting.com | GET | 8 | Same origin; exact path/query/sensitive-path/DNS reason was discarded. |
| https://static.cloudflareinsights.com | GET | 8 | Outside scope; no analytics permission is proposed. Exact paths unknown. |

SPA discovery previously waited an arbitrary request_interval_ms after domcontentloaded, then captured the DOM. That could capture a shell, blocked/error UI or unfinished render. Successful HTTP navigation was not proof of completed application rendering.

Redirect handling also needed tightening: official Playwright documentation says a route handler may see only the first URL of an HTTP redirect. Relying on route callbacks to validate every hop is insufficient. Sources: [Playwright routing](https://playwright.dev/python/docs/api/class-page#page-route), [Chromium Fetch response-stage interception](https://chromedevtools.github.io/devtools-protocol/tot/Fetch/).

## Exact proposed API allowlist — not applied

The candidate configuration is **v021-api-allowlist.proposed.yaml**. Every entry has enabled: false and a pending approval reference. Existing projects/toolshop-v02/config.yaml remains unchanged, with no api_resources entries.

| Exact origin | Method | Exact path | Allowed query parameters |
| --- | --- | --- | --- |
| https://api.practicesoftwaretesting.com:443 | GET | /products | None |
| https://api.practicesoftwaretesting.com:443 | GET | /brands | None |
| https://api.practicesoftwaretesting.com:443 | GET | /categories | None |
| https://api.practicesoftwaretesting.com:443 | GET | /categories/tree | None |

The origin is written without the default :443 in YAML; permission is still tied to the exact effective scheme/host/port. The official OpenAPI document describes these GET operations as catalog/brand/category retrieval: [Toolshop OpenAPI](https://api.practicesoftwaretesting.com/docs?api-docs.json). Only documentation was read; none of these data endpoints was exercised in this review. Their documentation is not evidence that the frontend made those exact historical requests.

Permission would apply only to browser fetch/xhr resource requests. It would **not** expand page navigation or allowed_domains. No wildcard hosts, path prefixes, parameter patterns, product IDs, dynamic detail routes, search terms, request bodies, headers carrying credentials, cookies, redirects, OPTIONS, QUERY or write methods are proposed. Query-bearing variants, /products/search, authentication, contact, checkout, cart/payment/admin/user resources and analytics remain blocked. In particular, approving this initial GET-only list will not resolve the ten QUERY requests and is not a promise that Toolshop will become fully usable.

After explicit approval, the operator may copy only the reviewed entries into the selected project's config, set enabled: true and record the real approval reference. Do not simply extend allowed_domains or disable origin validation. A later denied-request capture can identify actual remaining paths and redacted query keys; any additional queries, IDs or methods require a separate exact proposal and behavior review.

## Narrow implementation patch

- **core.py**: an additive APIResourceRule contract and default-empty api_resources. Each rule has an exact origin/path, GET/HEAD-only method vocabulary, bounded exact query values, default-disabled state and required approval reference. New readiness settings are bounded. max_requests adds a conservative per-Scope egress cap (default 300; maximum 1000), alongside existing page/depth/time/rate limits.
- **security.py**: navigation validation remains unchanged. Only enabled exact resource rules grant fetch/xhr exceptions. Approved resource hosts receive validated DNS checks and Chromium hostname pins; credentials, bodies, sensitive endpoints and private destinations stay denied. Query values and userinfo are not logged. Future denials retain origin including non-default port, non-sensitive path, redacted query-key names and a specific reason. Sensitive paths are redacted rather than leaking identifiers.
- **security.py redirect guard**: Chromium response-stage interception blocks 301/302/303/307/308 before another destination is contacted, including redirects toward otherwise allowlisted paths. This is deliberately fail-closed, not automatic redirect approval. It does not use route.fetch/APIRequestContext, which would require separate DNS-containment analysis. If the response interceptor cannot be installed, the request is aborted. Chromium remains the supported browser; sites depending on redirects remain a compatibility limitation.
- **readiness.py**: MutationObserver plus animation-frame polling records content/status stability, visible busy indicators, document state and observed counts. Quiet-window stability is a UI condition, not a fixed sleep. The wait has an explicit timeout and is capped by remaining exploration time. No networkidle assumption or app-specific selector is used. Content, status and timeout observations all retain application_completeness: UNVERIFIED.
- **exploration.py**: replaces the fixed delay with readiness evidence, persists it per page, and records readiness timeout as incomplete UI evidence while preserving passive capture. No active functional action is added.
- **tests/test_external_compatibility.py**: local-only policy, DNS, authentication/body, query, budget, redirect-egress and readiness tests. Public-hostname unit tests use mocked DNS; browser tests use two owned loopback servers. No real API origin is enabled in tests.

Service workers and websockets remain blocked by the existing browser setup. Existing allowed domains, authentication references, page/depth/time limits and request spacing are not broadened. The independent 9-pass / 2-detected-regression / 9-pass artifacts are untouched; this targeted review deliberately does not rerun the complete acceptance workflow or the full suite.

## Targeted verification

Final selected run: **48 passed in 12.25 seconds**, no failures/errors/skips. Targeted Ruff lint and formatting checks also passed. Historical acceptance artifacts still record 9 passes, the intentional 7-pass/2-failure phase, and 9 restored passes; they were read and hashed, not rerun or rewritten.

The exact executed selection is recorded in v021-verification.json and JUnit in v021-targeted-tests.xml. Only the new compatibility tests and existing URL/DNS/path/redirect boundary tests were selected. Ruff was limited to the four affected source files and the new test file. No uv installation, dependency update or build command was run.

Coverage includes inactive/default-empty rules, exact API resource permission without navigation permission, denied writes/QUERY/OPTIONS, alternate origins/ports/schemes/near-match paths, bounded exact queries, duplicate query keys, credentials and bodies, private/rebound DNS, request-budget exhaustion, audit redaction, and redirects whose destination counters remain zero. Readiness covers delayed rendered content, permanently busy UI, a navigation-only shell, stable status/error UI and persisted exploration evidence.

The first new-test run caught an expected audit-redaction mismatch: the test initially expected literal /admin, but the logger intentionally redacts sensitive paths. The assertion was corrected to require that redaction and an explicit redirect denial; destination-egress assertions remained unchanged. Subsequent targeted runs passed.

## Behavior contracts still required

API connectivity never establishes business behavior. Search match and empty-state expectations require approved input/result criteria; filters require reviewed category membership semantics; sorting requires reviewed keys, direction, locale and pagination scope; detail validation requires observed product identity and approved exact resource IDs. Loading/error/empty UI expectations also require review. The current 22 external scenarios remain pending/manual; neither network permission nor readiness evidence approves them.

## Human approval boundary

Review the four exact GET-only, no-query resources in the proposal before any permission is enabled or external validation resumes. Remaining blockers are lost historical path/body evidence, continued QUERY rejection, likely unreviewed query/detail resource needs, unverified behavior contracts and actual external readiness under the proposed scope. This patch does not claim external compatibility success.
