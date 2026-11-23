# Security boundaries

V0.2 adds optional declarative contracts for reviewed functional actions. Initial discovery remains passive. Action locators must have checked uniqueness, selections must use observed options, sensitive fields/dangerous controls are rejected, and unknown expectations remain manual. Search clicks are limited to observed search controls; other button clicks require explicit local-only permission. All network writes remain blocked. Imported data is quoted into fixed templates, not evaluated as code. No AI Python is accepted.

Additional configuration can narrow scope using excluded_paths and permitted-request spacing. The external practice-site attempt honored its published path exclusions and retained the same-origin policy; separate API requests were blocked. Scope observations are recorded without full request URLs or query strings. Do not remove these restrictions just to make an acceptance demonstration pass.

Only test applications and repositories you are authorized to inspect. The explicit `--authorized` flag records the operator's confirmation; it cannot establish ownership. Initial discovery navigates links and observes pages, with no form submission, clicks on buttons, purchases, account creation or access-control bypass.

Scope is the initial HTTP(S) scheme, hostname and port. Credentials and query strings are rejected. HTTP methods other than GET/HEAD, cross-origin resources, service workers and websockets are blocked. Common modifying/credential routes are excluded, including percent-encoded variants. DNS results are checked against public address classification; all non-public addresses are rejected except loopback explicitly enabled for controlled local testing. Chromium is pinned to a validated destination address and launched without proxy routing to reduce DNS rebinding exposure. This sacrifices CDN failover; unsupported network configurations may fail safely. IPv6 literals, unusual DNS names and browser/OS network behavior have not all been exhaustively verified. Use a network-restricted environment for sensitive engagements.

GET requests are not inherently side-effect-free. Applications can implement unsafe GET endpoints under arbitrary names. Path exclusions are conservative heuristics, not proof of safety. Review application scope and use dedicated staging/demo environments with least-privilege data. Browser JavaScript still executes within Chromium and may attempt GET requests; same-origin allowed GET requests remain possible. No general crawler can prove that arbitrary application navigation is read-only.

One browser page, explicit page/depth limits, per-navigation limits, bounded element/text extraction and a cooperative overall timeout constrain discovery. DNS resolution, browser startup and some Playwright operations may extend the cooperative deadline. Subprocess test execution has a timeout; descendant process cleanup on forced termination is not guaranteed on Windows. Do not treat these limits as a hostile-site containment sandbox.

Project names reject traversal and Windows reserved names. Workspaces have separate directories, registry entries and JSON audit logs. Linked artifact directories are rejected. Local workspace content must be trusted; this is not a multi-tenant filesystem boundary, and concurrent mutation of project files is unsupported. Reports autoescape untrusted HTML. Source inspection skips hidden/vendor folders, links, oversized files and obvious secret filenames; it never executes code. Heuristic skipping is not comprehensive secret detection.

Keys belong in environment variables or a secret manager. `.env` and project artifacts are ignored by Git. AutoQA does not load auth state in v0.1. Discovery stores visible text, URLs, screenshots and traces: these may include sensitive application data even when no key is logged. Use synthetic staging data, protect the project directory, and review/redact deliverables before client sharing. Artifact retention/deletion is currently manual.

Optional AI receives only reduced workflow IDs and visible element text after explicit `plan --ai`. Text is untrusted data, the provider has no execution tools, and recommendations are validated against known evidence IDs. Schema validation does not prove that recommendations are correct or immune to semantic prompt injection. They remain REQUIRES_REVIEW and cannot change approvals or executable tests. Requests use the official API endpoint, bounded timeout/retry settings and `store=False`; provider data policies still apply.

The test runner accepts only AutoQA template outputs with matching manifest hashes and approvals. It disables plugin autoload, controls Pytest configuration, removes unrelated environment variables and uses `shell=False`. It is process isolation, not a sandbox: Python and Chromium retain host-user privileges. Do not place untrusted code in the QA workspace or edit manifests to bypass checks. No AI-generated code is accepted for execution.

Generated CI has read-only repository permissions, immutable action revisions, no secret references, no credential persistence and no pull_request_target trigger. Review all workflows before committing. Pull-request code still executes on the runner: use public/synthetic targets and restricted environments. Do not introduce staging credentials into untrusted pull-request jobs.


## V0.5 standalone API/authenticated execution

V0.5 adds reviewed API requests through the framework builder, not to passive UI
exploration. Mutating methods require a reviewed mutation statement and the complete
scenario is bound to manual approval receipts. Exact origins/methods/paths and named
environments are reviewed; DNS is validated and pinned, redirects are rejected and
remote API credentials require HTTPS. Private LAN/metadata targets remain unsupported.
Authenticated browser cookies are externally supplied legitimate sessions, restricted
to the exact UI origin and HTTPS except owned loopback. There is no AutoQA user login.

Only AUTOQA_SECRET_* environment references are exported. Conventional sensitive keys
are rejected in JSON/header data; arbitrary client PII detection is not implemented.
Review every fixture/input value. API/authenticated exports restrict persistent capture
to safe summaries: HTTP payload/header values omitted, failure/log details suppressed,
screenshots/traces disabled. Results remain genuine. Unauthenticated UI-only and legacy
capture retain their historical privacy limits. Summaries require manual retention
management; no automated age-based purge or full screenshot/trace redaction is claimed.

The subprocess remains unsandboxed, receipts unsigned, filesystem trusted and storage
single-writer. Local Windows/Chromium and loopback HTTP evidence do not certify arbitrary
client services, public HTTPS infrastructure or other platforms. See [V0.5 audit](v05-release-candidate.md).
