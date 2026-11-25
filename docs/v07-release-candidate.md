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
and separate planning disposition. Existing domain0.3/API0.5/management0.6 and scenario/
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
| 0afa31031bf5eefbc5511ff85810913c0de50282 | 001e5d3 | 81 independent tests passed; combined172; frozen legacy subset18 |

No overlapping writes or integration conflicts. Shared-contract clarifications were
centralized and committed; dependency commits were integrated only within specialists'
own worktrees. Tests were not removed/weakened. Initial Framework fixture assumptions
about suite/pack whitespace IDs and normalized size were corrected against actual
contracts. Independent QA corrected order assumptions and separated allowed evidence-ID
deduplication from rejected duplicate workflow identities; final assertions retain the
preservation/atomicity guarantees. These were test-fixture assumptions, not hidden passes.

The existing exact-command-set characterization requires the four new approved commands;
Lead expanded only its additive allowlist, retaining all legacy signatures/options/help/
exit/fixture assertions. Framework's separate unchanged-copy run recorded128 passes and
9 failures at that same allowlist assertion. Lead integrated focused run then passed
**140 tests in39.29s** across V0.7, frozen compatibility and H01/H02. No runtime failure
was converted to a skip or an ignored prerequisite.

## Real synthetic example

`uv run python examples/validate_v07.py` passed without browser/API/client-code execution.
Fresh owned project has reviewed UI heading, reviewed API contract and manual case.
Five explicit requirements produced: 4 reviewed requirements, **2 confirmed mappings**
(UI and API), **2 missing mappings**, **1 unsupported**, **1 uncertain**, and **25 manual
proposals** with positive/negative/boundary/regression/error-handling intent.
Execution coverage is **NOT_ASSESSED**, no coverage percentage. One planning acceptance
left every original project file byte-identical; repeating analysis returned the same
snapshot. Actual JSON is in ignored .test-work/v07-planning-example-2lxci1yg/plan.json.
The example is declarative fixture evidence, not proof of arbitrary client behavior.

## Final release-quality gates

Full gates, package/install/independent framework acceptance, documentation/inventory
checks and exact final-head CI must complete before recommending candidate audit.
Actual results will be recorded before final delivery; pending checks are not success.

## Limits and deferred scope

No unrestricted document/NLP ingestion, inferred semantic requirement matching, full
application/code coverage, automatic executable scenario generation, client source
modification, planning-to-execution approval bypass, provider requirement or V0.8 repair.
Operators supply bounded source provenance, expectations, signatures/mappings and review.
Declared reviewed state is not authenticated identity. Feasibility reflects case metadata,
not independent compiler/runtime certification. Existing unsigned/trusted-filesystem/
single-writer/sandbox/privacy/retention/platform limits remain. Historical V0.5 intermittent
API/evidence/JUnit incident remains unroot-caused. Scoped credential scans are not
universal PII/secret detection or a forensic audit of history. Stable0.7 promotion,
merge/tag and V0.8 are not authorized. Stop at one verified development PR for audit.
