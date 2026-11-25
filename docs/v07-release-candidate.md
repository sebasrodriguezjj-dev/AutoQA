# V0.7 release candidate evidence

Candidate preparation follows owner-authorized V0.7 development from main
`baa776d2253831f08dc7d630cf0e67d0a22d4b8f`. Stable release/tag v0.6.0 is preserved.
This is a supervised local QA Engineering tool, not SaaS or universal client certification.
Final candidate readiness depends on all gates and exact-head CI recorded below/PR.

## Architecture and product scope

D02 committed first (`d03c74d`) separates enduring instructions from dated state;
[ADR 0002](decisions/0002-enduring-instructions-and-dated-state.md) records the reason.
New strict schema 0.7 DTOs, pure requirements/planning engine, bounded local service and
four additive CLI commands implement [the operator guide](v07-intelligent-planning.md).
[ADR 0003](decisions/0003-additive-requirement-planning.md) records conservative evidence
and separate planning disposition. Existing domain 0.3 / API 0.5 / management 0.6 and scenario/
suite approvals, case signatures, framework runtime and legacy readers are retained.

Explicit supplied requirements and mappings yield confirmed/proposed/missing/unsupported/
insufficient/stale/excluded findings; no title matching, executed coverage or percentages.
Proposals are manual, risk is an explained heuristic and unknown outcomes stay unknown.
Analysis/coverage is read-only; only explicit import/review writes new sidecars. Planning
acceptance never grants scenario/suite approval or execution authority.

## Actual delegation and integration

Shared interface/context commit: `45188e38226b2da884ab83f8b3f0fd91227ff3d4`.
One Lead and three actual native specialists used isolated worktrees under
C:/Users/sebas/Desktop/AutoQA-worktrees/v07-backend, v07-framework and v07-qa.
Original foundation worktrees remained untouched. Backend owned pure planner/tests;
Framework owned local service/application/CLI/integration tests; independent QA owned
adversarial tests. Only Lead integrates and publishes. Contract-only amendments retained
exact source tag labels; actual V0.6 suite/pack ID restrictions remain unchanged.

Native tools were used, with four active slots. Automatic TOML profile discovery was
not observable; all specialists read assigned profiles and the same explicit briefing.
A third new spawn hit the environment thread limit; the already available backend_product
session was explicitly reassigned the independent QA role and correct new isolated
worktree. This is three specialists/four actual agents for V0.7, not an extra orchestrator.
CLI 0.114.0 still reports multi_agent=false; no global setting or external dependency changed.

| Specialist original commit | Lead integration | Actual evidence |
| --- | --- | --- |
| 0865d1c5b27bfb822f0832b67dda604f58951ba7 | 0338095 | 46 focused tests; 91 domain/frozen/H01-H02 tests; Ruff/format |
| 054ec1804b988bd57bd1de44e1a0dc4452b83f9e | d45a800 | 12 integration tests; Ruff/format; original legacy CLI command allowlist needed additive update |
| 0afa31031bf5eefbc5511ff85810913c0de50282 | 001e5d3 | 81 independent tests passed; combined 172; frozen legacy subset 18 |

No overlapping writes or integration conflicts. Shared-contract clarifications were
centralized and committed; dependency commits were integrated only within specialists'
own worktrees. Tests were not removed/weakened. Initial Framework fixture assumptions
about suite/pack whitespace IDs and normalized size were corrected against actual
contracts. Independent QA corrected order assumptions and separated allowed evidence-ID
deduplication from rejected duplicate workflow identities; final assertions retain the
preservation/atomicity guarantees. These were test-fixture assumptions, not hidden passes.

The existing exact-command-set characterization requires the four new approved commands;
Lead expanded only its additive allowlist, retaining all legacy signatures/options/help/
exit/fixture assertions. Framework's separate unchanged-copy run recorded 128 passes and
9 failures at that same allowlist assertion. Lead integrated focused run then passed
**140 tests in 39.29s** across V0.7, frozen compatibility and H01/H02. No runtime failure
was converted to a skip or an ignored prerequisite.

## Real synthetic example

`uv run python examples/validate_v07.py` passed without browser/API/client-code execution.
Fresh owned project has reviewed UI heading, reviewed API contract and manual case.
Five explicit requirements produced: 4 reviewed requirements, **2 confirmed mappings**
(UI and API), **2 missing mappings**, **1 unsupported**, **1 uncertain**, and **25 manual
proposals** with positive/negative/boundary/regression/error-handling intent.
Execution coverage is **NOT_ASSESSED**, no coverage percentage. One planning acceptance
left every original project file byte-identical; repeating analysis returned the same
snapshot. Actual JSON is in ignored .test-work/v07-planning-example-ginusuav/plan.json.
The example is declarative fixture evidence, not proof of arbitrary client behavior.

## Interrupted recovery and reproduced provenance defect

Recovered Lead HEAD 538f20f with 13 modified tracked files and 5 untracked candidate records;
all preserved in checkpoint 0d8d6e6. Existing specialist branches/worktrees were inspected,
not recreated. Backend fix c23de59 was recovered as 9dcc88d. Missing QA ambiguity repro
8a1fd2d was recovered as ef97669. Framework adapter/test and QA fixture changes remained
uncommitted in their original worktrees; exact patches were retained and integrated as
**dd12809** after inspection and focused verification. Original working copies remain
untouched. All initial specialist patches occur exactly once in the integration history.

Initial pre-correction full regression passed **444 passed / 18 deselected in 210.88s**, and its
package/installed planning/independent execution gates completed. That result did not
cover the later corrections and was not accepted as final candidate certification.

Lead review found actual provenance erasure: known SOURCE/INFERRED references could
receive observed-functionality risk and confirm explicitly observed support; provenance
drift could preserve accepted planning disposition. Independent QA reproduced **7 failed /
81 deselected in 4.89s** on the Lead tree (.test-work/v07-provenance-before.log), plus a
separate failing ambiguous-category regression. Backend independently reproduced 11 new
failures before its bounded pure-planner repair. No failing assertion was removed.

The correction preserves workflow.status/evidence.category in typed context, requires
OBSERVED for declared observation support, treats missing provenance as unknown, rejects
conflicting evidence categories and includes all provenance in the plan digest. Positive
fixtures now explicitly declare OBSERVED support; negative SOURCE/INFERRED/UNKNOWN/
VERIFIED_REQUIREMENT/missing cases remain independent regressions. Same-category evidence
repetitions deduplicate; provenance drift makes old review stale and rejects stale writes.

Recovered focused provenance gate: **39 passed / 141 deselected in 5.54s**. Complete V0.7
planning/integration/adversarial slice: **180 passed in 13.29s**. No product-runtime
change followed that verified correction; the final complete gate below certifies it.

## Final corrected-candidate release-quality gates

The complete reusable release script returned **exit 0**, Windows/Python 3.14.3,
on the corrected candidate runtime. Log: `.test-work/v07-final-release.log`;
fresh package/standalone evidence: `.test-work/release-gate-o299otnx`.

| Gate | Actual result |
| --- | --- |
| Focused provenance regressions | 39 passed / 141 deselected in 5.54s |
| Complete V0.7 unit/integration/adversarial slice | 180 passed in 13.29s |
| Full non-browser regression, live AI excluded | **485 passed / 18 deselected in 215.74s**, no Windows skip or unexpected failure |
| Ruff lint and format | Passed, 73 src/tests/scripts files; new example checked separately |
| Lock consistency and comparison | 37 packages; only root version changes from 0.6.0 to 0.7.0rc1 |
| Frozen compatibility and V0.6 H01/H02 | Passed in complete regression; archives/member hashes and historical schemas unchanged |
| Wheel/sdist, package/import/installed version | Built and asserted **0.7.0rc1**; private/disposable paths excluded |
| Installed four-command V0.7 workflow | Genuine JSON analysis/coverage, read-only checks, import, accepted planning disposition and nonzero stale-review refusal passed |
| Standalone framework | AutoQA absent; approved validation and COMPLETE collection; no missing/unsupported/duplicate/unexpected nodes |
| Genuine independent case/pack/full execution | Each exit 0, one passed invocation and two actual operations |
| Retained UI/API behavior | UI export/independent collection and actual owned API healthy/defect/restored acceptance remain in full regression |
| Documentation/roles/history | Relative destinations resolve, all four role TOML parse, D02 rules and historical architecture/state suffixes preserved |
| Scoped credential/artifact inventory | 160 tracked files plus frozen ZIP members; no conventional credential/private-output findings |

The corrected synthetic example was rerun: `.test-work/v07-planning-example-ginusuav/plan.json`,
plan `PLAN-65a905f7bec66860d09908e35c9f7713a10ae0fcd77f90f7478478323146a620`,
with the same 5-requirement/2-confirmed/2-missing/1-unsupported/1-uncertain/25-proposal
semantics recorded above and executed coverage NOT_ASSESSED. No browser logic changed;
new browser benchmarks, client targets and live AI were not run. Existing historical
Windows/Chromium evidence is retained, not claimed as new platform certification.

Final exact-HEAD hosted CI and inspected logs are post-commit delivery checks. Their
actual run/job IDs, tested synthetic merge and final HEAD belong in the development PR
and final handoff after verification; local success alone does not satisfy that gate.
Leave that PR unmerged for independent audit. No stable release/tag or V0.8.

## Newly approved future vision

The owner-approved future local application/workspace, Repository Management, manual/
AI-assisted professional IDE workflows, Test Data Manager, five dashboards and three
VS Code Agent Skills are documented in [product vision](product-vision.md),
[roadmap](roadmap.md) and [ADR 0004](decisions/0004-owner-approved-professional-workflow-vision.md).
Approximate allocation is V0.8 foundations, V0.9 interfaces/managers/skills/dashboards,
V1.0 integrated validation. No corresponding future runtime functionality is added to
V0.7; exact later scope and provider-specific skill compatibility need separate review.

## Limits and deferred scope

No unrestricted document/NLP ingestion, inferred semantic requirement matching, full
application/code coverage, automatic executable scenario generation, client source
modification, planning-to-execution approval bypass, provider requirement or V0.8 repair.
Operators supply bounded source provenance, expectations, signatures/mappings and review.
Declared reviewed state is not authenticated identity. Feasibility reflects case metadata,
not independent compiler/runtime certification. Existing unsigned/trusted-filesystem/
single-writer/sandbox/privacy/retention/platform limits remain. Historical V0.5 intermittent
API/evidence/JUnit incident remains unroot-caused. Scoped credential scans are not
universal PII/secret detection or a forensic audit of history. Stable 0.7 promotion,
merge/tag and V0.8 are not authorized. Stop at one verified development PR for audit.


## H03 evidence identity drift remediation

This section supersedes earlier candidate verification for H03. The owner requested
remediation of the static finding against audited HEAD
8b6f71eea1c726607159e5e77ff7d1e0a9923e0e; existing accepted D02/provenance/compatibility/
ADR 0004 work was preserved. PR #7 remains the only development PR and stays unmerged.

Before production edits, corrected synthetic reproductions recorded **6 failed /
1 passed in 6.41s**: workflow/page reassociation and required/min/max changes kept an
accepted plan CURRENT, and conflicting same-ID observations did not fail. The passing
case exercised the legacy element generator and proved ID reuse across validation
changes. The first fixture lacked a locator stub; its failure is not counted as a
product defect. Actual local logs are preserved:
`.test-work/v07-h03-before.log` and
`.test-work/v07-h03-before-corrected-fixture.log`.

[ADR 0005](decisions/0005-reviewed-semantic-observation-bindings.md) specifies the
versioned semantic hash projection and explicit reviewed requirement bindings.
Same-ID drift now changes the plan digest, resets prior disposition and refuses
outdated review writes. Conflicting observations fail generically; equivalent evidence
and reordered collections deduplicate/canonicalize. Timestamps and disposable artifact
paths do not cause drift. Hash-only context avoids exposing raw discovery content.
Actual OBSERVED provenance remains mandatory. Accepting a current plan cannot refresh
stale requirement bindings; explicit independent relationship review is required.
No historical discovery ID/schema/signature/receipt/runtime/frozen fixture changed.

| H03 corrected-candidate gate | Actual result |
| --- | --- |
| Focused H03 plus all affected V0.7 tests | **201 passed in 17.27s**; 21 additional regressions, existing assertions preserved |
| Full Windows/Python 3.14.3 release script | **Exit 0**; `.test-work/v07-h03-final-release.log` |
| Full non-browser regression, live AI excluded | **506 passed / 18 deselected in 218.17s**; no skips/failures |
| Ruff lint/format | Passed, 75 src/tests/scripts files |
| Lock, version and frozen compatibility | Passed, root 0.7.0rc1 only; historical hashes/contracts and V0.6 H01/H02 preserved |
| Build/install/archive inventory | Wheel/sdist built; isolated installed import/distribution/CLI 0.7.0rc1 passed; private output excluded |
| Installed planning CLI workflow | All four commands, read-only analysis, import, planning disposition and stale refusal passed |
| Independent framework | AutoQA absent; approved validation and COMPLETE collection; zero unsupported/missing/duplicate/unexpected |
| Actual independent case/pack/full | All exit 0, one passed invocation and two actual operations each |
| Docs/roles/history/inventory | Local Markdown links resolve, four TOML roles parse, complete historical suffixes/protected legacy files preserved; 163 files plus frozen ZIP members scanned without conventional credential/private-output findings |

Fresh package evidence is `.test-work/release-gate-xhi70uf3`. The final handoff changes
only documentation after the complete runtime gates; exact final published HEAD must
also pass hosted CI. Run/job, inspected logs and tested synthetic merge/tree equality
are recorded in the live PR after post-commit verification, avoiding a self-referential
commit SHA. Historical earlier counts are not substituted for H03 results.

Residual limits: conservative projections cover recorded meaning, not complete behavior
or authenticated identity; hashes are not encryption or universal secret protection.
ID-only declared observation links require explicit bindings for confirmation. Existing
trusted-local/unsigned/single-writer/privacy/retention/platform limitations and the
unroot-caused historical V0.5 incident remain. No browser logic changed; no new browser,
client or live-AI benchmark is claimed. No stable tag/promotion, merge or future scope.
Stop after verified PR publication for another independent owner audit.
