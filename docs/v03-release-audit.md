# AutoQA V0.3 release audit

Audit date: 2026-11-18. Audited repository: `sebasrodriguezjj-dev/AutoQA`.
Audited branch/HEAD: `feat/v03-batch-c` / `7d2d599`.

**Finalization update (2026-11-19):** the audit below records the original audited
state. The screenshot lookup finding is now fixed, package/import/lock metadata is
`0.3.0`, and release verification has been repeated. See
[release finalization](./v03-release-finalization.md) for current results and integration
instructions. The original 0.2.0 build and uncommitted-audit statements below are
historical audit observations, superseded by that finalization record.

## Decision

**Ready for local-engine integration, with the limitations below. No release-blocking
defect was found in the supported synchronous, trusted-local-operator workflow.**
Mandatory regression, compatibility, lint, formatting and package-build gates passed.
This is not approval to publish packages or Git artifacts. Proposed release: **0.3.0**.
Current package metadata and import version remain **0.2.0**; align them and the lockfile,
then repeat package verification before publishing a V0.3 release. No version was changed
by this audit. Remote main must be refreshed before any integration decision is executed.

Only this audit document is a deliverable change. No product code, assertions, fixtures,
dependencies or commits were modified. No PR, push, merge, tag or reset was performed.

## Git and delivery provenance

Initial working tree was clean. HEAD exactly matched the requested final commit.
Origin is `https://github.com/sebasrodriguezjj-dev/AutoQA.git`.
Local `main` and cached `origin/main` are `1853c35b5a666b1c1680d9dc0684014452f82430`.
The merge base is that same commit; `git rev-list --left-right --count main...HEAD`
returned `0 12`. No fetch was performed; cached remote refs do not establish current
GitHub state. Agent-host checkpoint refs visible under `--all` are not extra commits
in the twelve-commit main-to-HEAD integration range.

The following are in the linear ancestry, in order:

| Batch | Verified implementation/delivery commits |
| --- | --- |
| A | `b7566a6`, `5bcba16`, `545a245`, delivery `c5e71f4` |
| B | scaffold `eb57329`, `d6e2614`, `8e6dc67`, delivery `e55b824` |
| C | `4c9eace`, `bf70190`, `119dfad`, delivery `7d2d599` |

Read and checked [Batch A delivery](./v03-batch-a-delivery.md),
[Batch B delivery](./v03-batch-b-delivery.md), and
[Batch C final delivery](./v03-final-delivery.md), together with checkpoints and the
[compatibility baseline](./v03-compatibility-baseline.md).

## Architecture findings

- [Domain](../src/autoqa/domain.py) contains versioned Pydantic contracts, lexical artifact
  references, independent review/generation/execution states and relationship validation.
  It does not access filesystem/browser/provider adapters. These contracts are additive;
  production producers still use the compatible legacy models and artifact layout.
- [Legacy projections](../src/autoqa/legacy.py) copy historical payloads without migration
  or invented approval identity; missing historical steps remain `NOT_RECORDED`.
- [Storage](../src/autoqa/storage.py) confines project-relative paths, rejects symlink and
  junction components, atomically replaces serialized files and protects completed run
  directories through its adapter. Registration and selection retain existing precedence.
  This is not a filesystem sandbox: runner/discovery code and generic compatibility
  helpers still perform direct writes. Single-writer operation and trusted local files
  are required; path checks do not eliminate concurrent check/use races.
- [PlanningService](../src/autoqa/planning_service.py),
  [DiscoveryService](../src/autoqa/discovery_service.py), and
  [generation/execution services](../src/autoqa/engine.py) provide callable application
  boundaries. Much orchestration still delegates to existing modules; this is not a
  complete ports-and-adapters extraction. JUnit ingestion is a parser service, while
  execution still calls the underlying parser directly.
- [ApplicationEngine](../src/autoqa/application.py) composes the same services, diagnostics
  and reporting. `InProcessAdapter` forwards attributes; it is not a restricted API or
  authentication adapter. CLI generation/execution use the same services directly;
  diagnostics/reporting use the engine. The final delivery's shared-layer claim is valid,
  but should not be read as every CLI command going through `ApplicationEngine`.
- [Generation/execution](../src/autoqa/testing.py) retain trusted template rendering,
  AST/Ruff validation, managed-file digests, case signatures, collection-first subprocess
  execution, constrained environment, actual JUnit ingestion and `NOT_EXECUTED` for
  missing cases. The subprocess is not an OS security sandbox.

## Approval integrity and authorization

[Approval implementation](../src/autoqa/planning.py) writes receipts only from explicit
`approve`, after project-bound `review` authorization. Planning, generation and execution
do not repair or recreate receipts. Generation validates every selected case before
writing suite files; new manifests require approval binding and execution rechecks it.
The passing receipt regression deletes a receipt, checks generation refusal, corrupts
its signature, checks refusal, and succeeds only after explicit reapproval.

Therefore normal generation cannot silently refresh an approval to match changed cases.
Receipt schema, case identity, approved status, scenario signature and signature-based
revision must match. `approved_at` is only checked to be a string; source is informational,
not validated identity. Reapproval overwrites the prior record rather than preserving an
append-only signed approval history. Reject changes matrix status; it does not revoke or
delete the old receipt. Current case approval is independently checked before execution.

[AuthorizationContext](../src/autoqa/authorization.py) expresses project/operation intent.
Any Python caller can construct one; there is no authenticated actor, role management,
unforgeable capability, separation of duties or enforced proof of human review. CLI
approval is the operator's review action. AI recommendation paths cannot approve through
the provided workflow, but this is not isolation from arbitrary code in the process.
Diagnostics/reporting write files and audit events without an authorization context;
initialization/integration and low-level helpers are also outside this operation enum.

Receipts and manifests are unsigned local data. A writer controlling cases and receipts
can forge a matching binding; a writer controlling a manifest can remove its
`approval_binding` marker and enter legacy handling. These are explicit trusted-filesystem
limits, not authenticated tamper protection. Legacy generated suites retain their old
checks; approved legacy cases need reapproval for new generation. Approval persistence
across matrix/receipt/audit files is not a multi-file transaction. Remote/multi-user
exposure requires a stronger authorization and concurrency design first.

## Browser execution and evidence

Configuration supports headless (default), headed, slow motion 0–2000 ms, trace enablement
and `every_step`, `failures_only` (default), or `disabled` screenshots. Browser launch uses
these settings and existing scope/route controls. Both actual headed and headless tests
passed against owned localhost applications.

The generated fixture wraps the executed scenario in **one coarse step**, records its
test ID, step ID, sequence, outcome, duration and timestamp, and attaches capture filenames.
It takes screenshots/stops tracing during fixture teardown in that execution's unique
artifact directory. Capture errors are separate from assertion errors. Traces include
screenshots and DOM snapshots; disabling standalone screenshots does not disable trace
screenshots. Sensitive assertion details are reduced in step logs, but raw JUnit, pytest
logs, DOM snapshots and images can still contain sensitive content.

Fresh audit evidence was independently traversed: every emitted step test ID matched a
run record, every referenced file existed, and every trace ZIP contained a `.trace` member.

| Fresh execution | Scenario outcomes | Steps | Traces | Screenshots |
| --- | --- | ---: | ---: | ---: |
| Headless vertical slice | 4 passed | 4 | 4 | 0 |
| Failure/report | 1 failed (expected regression) | 1 | 1 | 1 |
| Headed | 1 passed | 1 | 1 | 0 |
| Independent healthy | 9 passed | 9 | 9 | 0 |
| Independent defect | 7 passed / 2 failed | 9 | 9 | 2 |
| Independent restored | 9 passed | 9 | 9 | 0 |

These are actual scenario-execution associations, not per-action measurements or domain
step-contract execution. Timestamp is recorded at teardown, not a start/end interval.
Step ingestion accepts dictionaries from current-run JSON without full domain validation;
it relies on trusted generated producers. Interrupted/setup failures can have no step.

Non-blocking findings for follow-up:

1. [Diagnostics](../src/autoqa/reporting.py) still looks for `<test>.png`; new screenshots
   are `<test>-step-1.png`. Step results reference the actual image and the general report
   artifact listing includes it, but diagnosis-specific evidence can omit that screenshot.
2. Fixture outcome mapping has only passed/failed branches: absent `rep_call` is treated
   as passed and a skipped call as failed. Supported generated templates do not emit skips,
   and JUnit remains authoritative, but richer future execution must preserve missing and
   skipped step semantics. This branch observation was not a browser skip-path test.
3. No focused runtime matrix for every screenshot policy, trace-disabled mode, capture
   failure or slow-motion bound was added here. Those options were inspected; the default
   capture paths and headed/headless execution were exercised.

## Fresh verification

Interpreter: existing `.venv/Scripts/python.exe`, Python 3.14.3. No live AI module was
imported/executed by test selection; no external website benchmark was run.

```powershell
.venv/Scripts/python.exe -m pytest tests --ignore=tests/test_live_ai.py -q -p no:cacheprovider --basetemp=.test-work/release-audit-elevated --junitxml=.test-work/release-audit-elevated.xml
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m ruff format --check src tests
uv build --out-dir .test-work/release-audit-dist
git diff --check
```

| Gate | Observed result |
| --- | --- |
| Complete offline/local regression | **189 passed in 173.82s**, no failed/skipped cases |
| Composition of selection | 175 non-browser + 14 browser cases; live AI module explicitly ignored |
| Independent acceptance | Healthy 9 / defect 7+2 / restored 9 sequence verified |
| Ruff lint / format | Passed / 43 files already formatted |
| Package build | sdist and wheel built; wheel built from sdist |
| Shared imports | `autoqa`, `autoqa.application`, `autoqa.engine` passed |
| Diff whitespace | Passed |
| Frozen fixtures | No diff from Batch A delivery; archive and member hash tests passed |

Initial sandboxed pytest attempts hit Windows temporary-directory `WinError 5`, including
cleanup errors; those are not passing evidence or product failures. Authorized elevated
rerun above passed. `python -m build` and `python -m hatchling` were unavailable in the
venv; `uv build` was used successfully after authorized access to its external cache.
Generated evidence/builds remain ignored under `.test-work/`, not release deliverables.

The reported final 175 non-browser plus focused 11 browser, 1 headed and 1 acceptance
results are consistent with this fresh broader 189-case run (which also includes the other
functional browser security test). Historical Batch A/B command counts were read as
historical claims, not relabeled as fresh executions. Tracked Stage 0 JUnit parses as
102 tests, zero failures/errors. No assertion was weakened.

Fixture SHA-256 values remain:

- V0.1: `7a5da45753e6776ea5105de75258b0532ada189bd14160ee3cdfdf1a03cd613d`
- V0.2: `ec14a2516a42c46bf05a69fd105ab7b1ac0e28a52074fe53a04c64d01b39d390`

## Compatibility and publication review

CLI/selection contracts, fourteen frozen approval signatures, read preservation,
snapshot/fallback reporting, manifest refusal and process exit semantics passed.
Direct callers of protected Python functions must now supply authorization contexts.
Legacy reads remain compatible; receipt-free new generation intentionally requires
reapproval. Python support is explicitly `>=3.14,<3.15`; this audit does not certify other
Python versions or operating systems. No dependency/lockfile change from main was found.

Reviewed tracked inventory, main-to-HEAD changes, ignore rules, fixture ZIP member contents
via scan, and actual wheel/sdist member inventories. No private credential or sensitive
client artifact was identified. Common private-key, GitHub-token, OpenAI-key and AWS-key
patterns returned no hits in tracked text or decompressed fixture contents. Test strings
such as `token=secret` are intentional synthetic rejection inputs. `.env.example` has
empty credential placeholders. This pattern scan is not proof against every possible
secret format or a complete forensic audit of all Git history.

No project directory is tracked. Projects, `.env`, auth state, local caches, build output
and new audit evidence are ignored. Wheel contains only the package/template and metadata.
Sdist additionally includes tracked docs, examples, tests and frozen fixture archives.
Those fixtures are intentional demo compatibility evidence, containing config/discovery,
matrices, suites, manifests, result JSON and JUnit, without screenshots or traces.
Existing historical XML includes workstation hostname and fixtures preserve local path
metadata; these are technical provenance, not credentials or identified client data.
Source publication will include that existing provenance. There is no automatic redaction.
Actual client browser evidence must be reviewed before any separate distribution.

## Proposed integration and release procedure — not executed

Preserve all twelve batch commits. Prefer a fast-forward if refreshed main is still the
verified ancestor; do not squash or cherry-pick only Batch C. First review and commit this
audit on the current branch, and require a clean tree. After explicit authorization:

```powershell
git fetch origin
git switch main
git merge --ff-only origin/main
git merge-base --is-ancestor main feat/v03-batch-c
git merge --ff-only feat/v03-batch-c
```

If either ancestry/fast-forward check fails, stop and assess the new main changes; do not
reset main or force integration. Prepare a reviewed merge on an integration branch and
rerun these gates against the combined tree before requesting integration approval.
Push/PR remain separately subject to explicit user authorization.

For the proposed **0.3.0** release, prepare a separate reviewed metadata commit aligning
`pyproject.toml`, `autoqa.__version__` and lockfile package metadata. Preserve historical
fixture versions and the legacy generated manifest wire format. Rebuild, inspect the
distribution contents and repeat regression on that exact final commit. Only after
explicit authorization publish or create a `v0.3.0` tag. The current successful 0.2.0
build is build evidence, not a correctly versioned V0.3 publication artifact.
