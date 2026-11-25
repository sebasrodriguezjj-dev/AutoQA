# CLI reference

Use `uv run autoqa COMMAND --help` for exact options. All project commands accept `--project PATH`. Run from a project directory or use the registry's active project when invoking from the QA repository root.

| Command | Notes |
| --- | --- |
| `init NAME --parent DIRECTORY` | Default parent: projects; no overwrites; Windows-safe project names |
| `demo --host 127.0.0.1 --port 8000` | Blocks until Ctrl+C; local server intended only for testing |
| `demo --variant independent --port 8001` | Independent owned Supply Lab fixture |
| `explore --url URL --authorized` | Explicit authorization required; strict initial origin scope |
| `explore --url URL --authorized --allow-localhost` | Enables loopback only; does not permit private LAN/metadata addresses |
| `explore --repo PATH --authorized` | Existing local path only; no scripts or dependency installation |
| `explore --repo PATH --url URL --authorized` | Hybrid UI/source inspection and inferred path matches |
| `plan` | Rebuild matrix from latest discovery; preserve identical approvals |
| `plan --approve TC-001 --approve TC-003` | Persist selected approvals; all IDs validated before changes |
| `plan --requirements FILE` | Import a reviewed JSON behavior-contract array; proposals remain pending |
| `plan --reject ID` | Persist rejection without deleting the scenario |
| `plan --ai` | Send reduced workflow evidence to configured cloud provider; saves review-only suggestions |
| `generate --approved` | Legacy UI-only generator; API cases require build-framework |
| `run` | Exit 0 only when Pytest succeeds; retain per-run JUnit and JSON |
| `diagnose` | Analyze latest run; no automatic repairs |
| `report --format html` | Client-facing HTML with escaped application text |
| `report --format json` | Structured project/run summary |
| `integrate --provider github` | Generate workflow from QA repository root; refuses overwrite |
| `plan-api REQUIREMENTS --project PATH` | Import 1?100 validated API contracts as pending cases without network requests; preserve identical approvals |
| `build-framework DESTINATION --approved --project PATH` | Export supported approved UI/API scenarios, Page Objects and API services into a new standalone directory |
| `validate-framework DESTINATION` | Check file hashes, Python syntax and exported approval snapshot; no execution |
| `run-framework DESTINATION --project PATH` | Recheck current source approvals, collect and run; propagate failure exit status |

Order: init → explore → plan → review → approve → generate → run → diagnose → report. `maintain` and `auth configure` are intentionally absent until implemented. There are no commands that print placeholder success.

Repository-only discovery cannot generate executable UI cases. AI suggestions cannot be approved through test IDs: they require independent review and implementation. AutoQA never executes AI output as Python. V0.2 behavior contracts are documented in v0.2-functional-testing.md. Reports can also be generated before execution; they explicitly state NOT_EXECUTED and contain no fabricated test records.

## Standalone framework workflow (V0.4)

Use the existing project selection and review commands first. `build-framework` requires
`--approved` and valid independent receipts. UI scenarios also require browser evidence;
API scenarios require the complete reviewed declarative contract.
Its destination parent must exist; the destination itself must be absent and outside the
source project, without traversal or link/junction components. It never overwrites an
existing export. Unsupported approved scenarios are listed explicitly; no test is emitted
for them. At least one supported approved scenario is required.

After export, install the dependencies in its own environment using `uv sync`, install
Chromium with `uv run playwright install chromium` when UI scenarios are included, then use:

```powershell
uv run python -m qa_runtime.runner validate
uv run python -m qa_runtime.runner collect
uv run python -m qa_runtime.runner run
```

These commands run from the exported directory without AutoQA installed. The application
must be running separately. Browser/environment settings are reviewed snapshots; update
the source config and export to a new directory when they change. `AUTOQA_BASE_URL` is
the optional authorized target override, still constrained by exported network policy.

`run-framework` uses AutoQA's interpreter and additionally checks current project approval
state before calling the export runner. Direct standalone execution validates only the
exported snapshot; it cannot observe later source revocation. Unique run directories
contain real JUnit, JSON outcomes, per-operation evidence, diagnosis.json and report.html.
Ruff is needed in the builder environment, but not in the standalone runtime.

Failures return nonzero; collection failure/timeout cannot become passing records.
See the [stable release gate](v04-stable-release-gate.md) for current verification and operating limits. The [0.4.0rc1 candidate audit](v04-release-candidate.md) remains historical evidence; commands are unchanged by the 0.4.0 version promotion.


## V0.5 API and authentication workflow

1. Initialize/select an authorized project. For UI cases, explore/plan first as before.
2. Prepare a JSON array of versioned API contracts (see `examples/api_contracts.json`).
3. `uv run autoqa plan-api FILE --project PATH` adds pending API cases without requests.
4. Review **test-cases/test-matrix.json**, not just its human summary: method, exact
   origin/path, query, headers, body, all environments, expectations, mutation review,
   auth references, fixture rows and evidence policy must be intentional.
5. `uv run autoqa plan --approve TC-API-ID --project PATH` creates the existing receipt.
6. Build/validate/run the same standalone framework commands. Unsupported approved
   cases are reported; pending/rejected cases never become tests. UI replanning retains
   API cases and their receipts. Changed imported API contracts return to pending.

Contracts support GET/POST/PUT/PATCH/DELETE, query parameters, static nonsecret headers,
JSON body, exact status/header/value checks and dotted JSON field/index type checks.
A non-GET request requires `mutation_review` of at least ten characters describing
reviewed scope and expected effect. This does not authenticate the reviewer.
`json_types` is basic shape checking, not full JSON Schema/OpenAPI validation.

An environment contains a unique name, exact HTTP(S) origin, explicit localhost flag
and nonsecret values. `AUTOQA_ENVIRONMENT` selects only one of those reviewed names;
unknown names fail. API ignores `AUTOQA_BASE_URL`; UI retains its existing scoped
base override. Remote API origins require HTTPS, public DNS addresses and direct
validated/pinned connections. Redirects and private LAN/metadata addresses are denied.
No proxy, wildcard scope, endpoint discovery or automatic retries are used.

Authentication is `none`, `bearer` with `token_env`, `basic` with `username_env` and
`password_env`, or `cookie` with `token_env` and `cookie_name`. References must match
`AUTOQA_SECRET_[A-Z0-9_]+`. Set their real values only in the invoking environment;
never place them in JSON, Python source, Git or reports. Missing/invalid values fail.
Reviewed browser cookies use source config `auth_reference`:
`cookie:AUTOQA_SECRET_SESSION:session`. Supply a legitimate application session yourself.
Login forms, OAuth refresh, browser storage-state import and AutoQA user login are absent.
Authenticated UI resources remain on the exact reviewed UI origin.

Named data fixtures contain a seed and 1?30 isolated JSON rows. A `${field}` whole-value
reference resolves from the row or environment values in query/body/JSON expectations.
`synthetic_id` is seeded deterministically; each parameter row gets a unique operation
identity. Credentials cannot be fixture data. Arbitrary client PII detection is not
implemented. No remote setup/teardown automation is implied; the operator owns test
state reset. Local fixtures and owned acceptance servers clean up their own lifetimes.

API or authenticated exports use `summary_only`: all HTTP header values and payloads
are omitted; marked header names appear masked. JUnit failure messages/log details,
screenshots and traces are suppressed before persistent capture. Pass/fail/error and
step associations remain intact. Summaries remain until explicit operator removal;
there is no automatic age-based deletion. Unauthenticated UI-only exports retain V0.4
capture and its documented privacy limits. Screenshots/traces are not claimed redacted.

For current 0.5.0 evidence see the [stable release gate](v05-stable-release-gate.md).
The [0.5.0rc1 candidate audit](v05-release-candidate.md) remains unchanged historical
evidence, as do V0.4 documents. No arbitrary client/platform certification is claimed.


## V0.6.0 commands

- `autoqa analyze-framework PATH`: JSON static audit and create/improve decision;
  ANALYSIS_BLOCKED exits 1. No execution, installation or source modification.
- `autoqa suite-propose --project PATH`: pending JSON inventory to stdout; nothing
  persisted. Assign/review packs, tags and enabled state in a UTF-8 JSON file.
- `autoqa suite-approve FILE --project PATH`: validate current scenario identity and
  approvals, persist reviewed membership/digest/event history. Re-export afterwards.
- `autoqa run-framework DEST --project PATH [--case ID | --pack ID | --suite ID |
  --tag TAG | --all]`: one mode; repeat case/pack/tag to form a deduplicated union.
  No flags retains approved-enabled regression. Invalid/empty/disabled/unapproved
  selections fail, with no full-suite fallback. Unsupported/incomplete scope fails.

Standalone: `python -m qa_runtime.runner run` and `collect` accept equivalent options;
AutoQA need not be installed. Arbitrary Pytest expressions/node IDs are not accepted.
See [management semantics/examples](v06-test-management.md), [analyzer limits](v06-framework-analyzer.md)
and [historical candidate evidence](v06-release-candidate.md) and [stable gate](v06-stable-release-gate.md). V0.5 examples remain valid.

## V0.7 intelligent planning

- `requirements-import FILE --project PATH`: explicit bounded JSON import into a new
  V0.7 sidecar; never scenario or suite approval.
- `intelligent-plan [--requirements FILE] --project PATH`: read-only full planning JSON,
  or the explicitly stored inventory when FILE is omitted.
- `coverage-report [--requirements FILE] --project PATH`: read-only supplied-inventory
  scope, counts/findings and current context; executed coverage is NOT_ASSESSED.
- `plan-review PLAN_ID --accept PROP_ID --project PATH` or `--reject PROP_ID`: repeat
  IDs within exactly one decision mode; bind planning disposition to the current plan.

Missing inventory, invalid/stale IDs, invalid input and unauthorized writes fail nonzero.
Accepted proposals remain MANUAL_REVIEW and cannot bypass existing plan/suite approval.
Read the [full operator guide](v07-intelligent-planning.md) for JSON bounds, signatures,
review workflow, coverage semantics and known limits. Old command interfaces remain.
