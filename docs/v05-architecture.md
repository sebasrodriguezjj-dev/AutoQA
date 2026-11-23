# AutoQA V0.5 architecture — 0.5.0rc1

## Verified baseline and contract checkpoint

Development starts at the official annotated v0.4.0 target
`41b940642c389bb426cd6fb836178a99453f4792`, with clean main and unchanged
frozen V0.1/V0.2 archive/member fixtures. No existing V0.5 branch or user edits
were present. Development is local on `feat/v05-development`.

The V0.4 framework builder, ApplicationEngine, project storage, manual review
and independent approval receipts remain the integration boundaries. The legacy
V0.3 domain contracts and serialized fixtures are not migrated.

V0.5 declarative API contracts live in `framework_runtime/contracts.py`, copied
verbatim into standalone exports. `TestCase.kind=api` binds the complete contract
to existing receipt signatures, including environment origins, request/mutation
scope, assertions, authentication references, data and evidence policy. Historical
non-API signatures retain their previous algorithm.

`plan-api REQUIREMENTS --project PATH` performs no network requests and creates
pending scenarios. Existing `plan --approve ID` / `--reject ID` remain the review
interface. Changed API contracts return to pending. No AI path approves a case.

First checkpoint validation: 93 tests passed across API contracts, domain,
contracts and frozen compatibility (non-browser). One initial test collection
error used Pytest's reserved parameter name `request`; it was corrected to
`request_spec` without weakening assertions.

## Integration and contracts

`api_service.plan_api` validates a bounded JSON requirements list and maps each
APIScenario into the existing TestCase. ApplicationEngine and the additive
`plan-api` CLI delegate to that service. Existing review authorization and
`plan --approve/--reject` create/retain the same receipt format. UI replanning
retains API cases. No automatic historical data migration occurs. The full JSON
matrix, including contracts, must be reviewed; its Markdown is only a summary.

V0.5 contracts validate HTTP requests, expected responses, named environments,
authentication references, seeded data, sensitivity policy and APIResult.
No executable Python, shell, JSONPath expression, arbitrary callback or full
JSON Schema program is accepted in requirements. Only complete `${name}`
placeholders in query/body/expected JSON resolve from reviewed data rows and
environment values. Per-row copies and a local seeded RNG avoid shared data
mutation. Remote setup/teardown is deliberately not automated.

The legacy `generate` command fails explicitly if approved API cases are present,
directing the operator to `build-framework`. It cannot silently emit partial API
tests. Existing UI-only behavior remains unchanged.

## Combined standalone export

FrameworkService extends the existing trusted compiler, staging directory and
AST/Ruff checks. UI operations still become Page Object methods. API scenarios
become parameterized Pytest functions calling a reusable ReviewedAPI service.
No secret values enter generated Python. The following files are hashed in the
same framework manifest and receipts remain bound to full selected cases:

```text
framework.json                 version, selected case signatures, hashes, parameter counts
blueprint.json                 UI pages/operations and API scenarios
review/{cases,receipts}.json    exported approved snapshot only
config/environment.json        reviewed legacy UI settings
config/authentication.json     UI cookie reference, never a credential value
pages/page_*.py                 UI Page Objects when selected
services/api_service.py        reusable API contract service when selected
tests/{conftest,test_approved}.py
qa_runtime/                    independent config, scope, runner, evidence, integrity
  contracts.py                 validated V0.5 contracts
  api.py                       pinned direct HTTP client and safe assertions
  api_fixture.py               isolated parameter-row recorder
  privacy.py                   sanitize reports before JUnit serialization
pyproject.toml, requirements.txt, pytest.ini, README.md
artifacts/RUN_ID/               generated only at runtime; never source delivery
```

The original manifest schema remains `autoqa.framework.v1`; V0.5 extends it with
`privacy=summary_only` and exact API row counts. The blueprint is version 0.5 for
API exports, while UI-only blueprints retain 0.4. The package and new exports are
0.5.0rc1. Old frozen archives and released exports are not rewritten.

Independent validation checks required runtime files, parameter counts, API case
identity, receipts and protected capture settings. Source-backed run-framework
also checks current source receipts. Delivery snapshots cannot observe later
source revocation. All integrity records are unsigned, requiring trusted writers.

## Network and application authentication

The HTTP client uses Python's standard-library http.client, without a new
dependency. Each scenario reviews exact origin, literal path, HTTP method and
mutation statement. All DNS answers must be public, or loopback with explicit
allow_localhost. The chosen validated address is used for the socket connection;
HTTPS retains the original hostname for certificate verification/SNI. No proxy,
redirect following, wildcard, retry, private LAN or cloud-metadata permission is
added. Body size is capped at 1 MiB; socket/read timeouts and the runner's overall
subprocess deadline are bounded. DNS resolution itself uses the OS resolver and
is bounded by the parent runner deadline, not a separate DNS cancellation API.
No hosted HTTPS/browser certification is implied by local HTTP acceptance.

Bearer/Basic/cookie strategies resolve only explicitly referenced
AUTOQA_SECRET_* variables. Missing/invalid references fail, never skip. The runner
passes only declared credential variables plus minimal runtime environment.
AUTOQA_ENVIRONMENT selects a named reviewed API environment; API ignores the
legacy UI base-URL override. A reviewed legitimate browser cookie can be supplied
through auth_reference= cookie:ENV:NAME. Authenticated UI stays on its exact
origin and requires HTTPS except explicitly allowed loopback. It does not obtain
sessions, bypass login or implement AutoQA user identity.

## Evidence, runner and compatibility

Each API parameter has a unique case/row identity and its own request/assertion
records. Actual HTTP status, duration, run/test/operation IDs, masked header names
and sensitivity labels remain available. Assertions fail with generic messages;
no raw request/response body or header value is persisted. For any API/authenticated
export, screenshots and traces are disabled, JUnit failure details are sanitized
before serialization and child console details are not written to disk. This is
conservative suppression, not pixel/trace redaction. Failed status is unchanged.
Summaries are retained until operator removal; age-based purging is not implemented.

The runner maps real parameterized JUnit records to row identities. Missing JUnit
still means NOT_EXECUTED and nonzero exit, not pass. Diagnostics do not invent
root causes. V0.4 unauthenticated UI-only capture remains unchanged, including its
documented privacy risks; legacy generated suites retain coarse scenario steps.

The trust model remains one local operator and trusted filesystem. There is no OS
sandbox, authenticated reviewer identity, multi-user concurrency guarantee or
universal PII scanner. Conventional sensitive keys are rejected during planning;
arbitrary sensitive strings under innocuous keys still require human review.

## Reproducible verification

`uv run python scripts/verify_release.py` runs checks and package stages; each
subprocess must succeed. The checks stage runs Ruff over src/tests/scripts, version
agreement, locked dependency consistency and non-browser regression excluding live
AI. Regression includes frozen archive/member hashes and independently installed
framework execution. The package stage builds wheel/sdist, checks their path
inventories, installs the wheel in a new environment, checks import/distribution/CLI,
exports an explicitly approved synthetic API contract, validates it, installs only
its standalone dependencies and collects with AutoQA absent.

CI retains pinned actions, Python 3.14 and read-only permissions. The same package
stage is added after regression. It uses public dependency registries and owned
loopback fixtures only. V0.5 CI was prepared locally; remote execution requires a
separate publication authorization. See the candidate audit for actual outcomes.
