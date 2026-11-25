# Permanent project state and engineering handoff

Last verification: **2026-11-24, America/Costa_Rica**. This is a dated handoff, not live
GitHub. Verify current refs/PRs/checks before trusting it; enduring rules are in AGENTS.

## Current authorized objective and release state

The owner authorized V0.7 Intelligent QA Planning and Coverage Gap Analysis plus D02,
then authorized resuming interrupted work and recording expanded future product vision.
Development branch: **feat/v07-development**. Candidate: **0.7.0rc1**, with completed
local acceptance below. Deliver one verified development PR and stop for independent
audit ("Audita al dev"). No merge, stable V0.7 tag, V0.8 or unrelated product work.
Starting/current verified main: **baa776d2253831f08dc7d630cf0e67d0a22d4b8f** (PR #6
merged after approved foundation PR #5). Fresh recovery query found no open PR or
published V0.7 branch before this task's publication. Final branch HEAD/PR/CI are
recorded in its live GitHub review and external handoff, without self-referential SHA.

The single [V0.7 development PR #7](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/7)
targets main from feat/v07-development and must remain **open and unmerged** for audit.
Its [checks view](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/7/checks) is the
canonical final-head verification link. Final run/job IDs and the inspected synthetic
merge checkout are recorded in the PR after post-commit CI completes. Do not substitute
its initial publication commit or an earlier/pending check for the current PR HEAD.

Stable product remains **v0.6.0**, target bbd54ad0821cb6962c09d8a1149a0f40b936764b,
annotated tag object bea83dc984687dcde97416a8fa57bd2849f8aa0f. No tag/main/history
rewrite, visibility change or worktree deletion. Domain 0.3, API 0.5, management 0.6,
legacy signatures/receipts/readers and standalone runtime remain compatible.

## Delivered V0.7 behavior and boundaries

Strict additive schema 0.7 DTOs; bounded explicit JSON source/requirement/evidence/mapping
input; deterministic snapshots/proposals; explained seven-factor risk; confirmed,
proposed, missing, unsupported, insufficient, stale and rejected/excluded mapping states.
Read-only intelligent-plan/coverage-report; explicit requirements-import and plan-review
write only new V0.7 sidecars under existing project-bound plan/review intent. Accepted
planning proposals remain MANUAL_REVIEW and cannot approve cases or suites, change
receipts/signatures, generate executable code or authorize execution. Coverage is only
the supplied partial inventory; no percentages and execution_coverage=NOT_ASSESSED.

Actual workflow/evidence provenance is retained. Only OBSERVED supports declared
observation references/risk; source/inferred/unknown/missing provenance cannot be inflated.
Conflicting categories fail; provenance drift changes plan ID and makes review stale.
See [operator guide](v07-intelligent-planning.md), [contract](v07-interface-agreement.md),
[candidate evidence](v07-release-candidate.md) and [ADR 0003](decisions/0003-additive-requirement-planning.md).

## Recovery and integration evidence

Recovered initial HEAD **538f20fe35a23657949db60b97ce6149a2698ca9**, with 13 modified
tracked files and five untracked candidate/docs/example files. All preserved in checkpoint
0d8d6e6; no active cherry-pick or verification process required restart/cleanup. No new
team was spawned. Exact binary diff checks prove each original patch integrated once:

| Original specialist/repro commit | Lead integration |
| --- | --- |
| Backend 0865d1c5b27bfb822f0832b67dda604f58951ba7 | 0338095 |
| Framework 054ec1804b988bd57bd1de44e1a0dc4452b83f9e | d45a800 |
| QA 0afa31031bf5eefbc5511ff85810913c0de50282 | 001e5d3 |
| Provenance repro d6133f4ee906e71afbcb69a9cd8491d233db4268 | 538f20f |
| Ambiguity repro 8a1fd2d8445dd08ca7e165b8d0273bf1e93a63d3 | ef97669 |
| Backend correction c23de59d8978415d34a23e414dd017986757ad6c | 9dcc88d |

Recovered Framework adapter/test and QA fixture/provenance changes were uncommitted in
specialist worktrees. Exact saved patches were reviewed, applied and tested, then committed
as **dd128091a13534c0b6fb9f6dd431032453f90e00**. Final owned files match preserved
specialist commits/working copies; none lost. Original three foundation worktrees and
three V0.7 worktrees remain. Framework retains its two original uncommitted files;
QA retains its original uncommitted test edits. They were not discarded or rewritten.
Lead working changes after the corrected runtime commit were documentation only.

D02 was the first commit, d03c74d: enduring instructions in AGENTS/roles/workflow/gates,
product purpose in vision, owner direction in roadmap, dated facts here and authoritative
live state in GitHub. [ADR 0002](decisions/0002-enduring-instructions-and-dated-state.md).
One Lead/three real specialists used explicit common context from 45188e3. Native tools
were exercised; automatic TOML role loading is unverified, profiles read explicitly.
CLI 0.114.0 has multi_agent=false. A thread-limit issue was handled by reassigning an
existing session to QA, not adding orchestration or claiming new automatic discovery.

## Actual final local verification

Corrected runtime complete gate **exit 0**, Windows/Python 3.14.3:
**485 passed / 18 deselected in 215.74s**, no unexpected failures or skips. Ruff
lint/format 73 files, lock 37 packages with root-version-only change, frozen archive/member/
CLI/import/approval compatibility and V0.6 H01/H02 passed. Wheel/sdist and isolated
installed import/distribution/CLI assert 0.7.0rc1. All four new installed commands pass
read-only/import/review/stale-refusal checks. Standalone framework has AutoQA absent,
validates and reconciles complete collection; genuine owned-loopback single/pack/full
each pass with one invocation/two operations. UI independent export/collection and API
healthy/defect/restored execution remain in regression. No browser logic changed;
no new browser/client/live-AI benchmark is claimed.

Focused provenance: 39 passed / 141 deselected in 5.54s. Complete V0.7 slice: 180 passed
in 13.29s. Initial gate 444 passed / 18 deselected in 210.88s and its package results are
**pre-correction history**, not final certification. Independent 7-failure provenance
and separate ambiguity repros remain, with before/after logs. All evidence lives in
ignored `.test-work`: v07-provenance-before.log, v07-provenance-after.log,
v07-provenance-recovered.log, v07-full-release.log (initial), v07-final-release.log
(corrected complete gate), v07-example-final.log; exact recovery patches are retained.
Fresh package directory: release-gate-o299otnx. Corrected synthetic plan artifact:
v07-planning-example-ginusuav/plan.json (5 requirements, 2 confirmed UI/API mappings,
2 missing, 1 unsupported, 1 uncertain, 25 manual proposals; executed coverage NOT_ASSESSED).

Documentation links/roles/D02/history checks and scoped inventory passed: all current
relative destinations, four TOML profiles and exact historical architecture/state
suffixes; 160 tracked files plus frozen ZIP members had no conventional credential or
private-output findings. This is not universal PII/secret detection or history forensics.
The final exact-HEAD hosted result and inspected logs are required post-commit before
delivery; run/job IDs, tested checkout and final HEAD are recorded in the PR/handoff.
No earlier/pending check substitutes for it. Root is committed before publication.

## Future owner-approved requirements and residual risks

Expanded private/local-first/code-first/supervised/evidence-driven V1.0 requirements are
recorded in [product vision](product-vision.md), [roadmap](roadmap.md) and
[ADR 0004](decisions/0004-owner-approved-professional-workflow-vision.md): local Application
Setup/guided projects/Developer Mode, separate application/automation repositories,
manual/AI-assisted IDE development and safe reviewed reconciliation, Test Data Manager,
five truthful dashboards and three provider-verified VS Code Agent Skills. Documentation
only: approximate V0.8 foundations, V0.9 interfaces/managers/skills/dashboards, V1.0
integrated validation. Exact future scope needs separate authorization; V0.7 is unchanged.

No current reproduced local mandatory blocker remains after the provenance repair.
Planning is not unrestricted document/NLP ingestion, semantic correctness certification,
automatic executable case compilation or complete application coverage. Declared review
and mappings remain human assertions; feasibility is recorded case metadata, not a new
compiler certification. Trusted-local/single-writer/unsigned-record, sandbox, privacy,
manual retention and platform limits remain. Historical V0.5 intermittent API/evidence/
JUnit incident is still unroot-caused. Provider-specific skill compatibility is deferred
and unverified. No V0.8 code, manager/UI/skills runtime or stable release is implemented.

## Historical foundation and reconciliation handoff

The following original dated handoff is retained intact as historical evidence.
Its temporary PR/authorization descriptions are superseded by the active section above.

---

# Permanent project state and engineering handoff

Last verification: **2026-11-24, America/Costa_Rica**. This is a dated handoff, not live
GitHub state. Before work the Lead must fetch and inspect actual repository, branch,
PR/head/base and associated exact-head check state. Update this file at every development
and release handoff. Source-controlled implementation facts and remote observations
are separated below. Do not treat historical authorization statements as new permission.

## Verified stable release (GitHub and Git observations)

- Repository: [sebasrodriguezjj-dev/AutoQA](https://github.com/sebasrodriguezjj-dev/AutoQA).
- Latest verified stable: **V0.6.0**. Stable product release/tag target:
  [`bbd54ad0821cb6962c09d8a1149a0f40b936764b`](https://github.com/sebasrodriguezjj-dev/AutoQA/commit/bbd54ad0821cb6962c09d8a1149a0f40b936764b).
- [PR #4](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/4) merged using a merge
  commit with parents V0.5 main `590832c229f9177c20eb4b928f78beac42488523` and promoted
  feature HEAD `530e436777c149164cb14be8fc9c34178ce09d5f`. All feature history remains.
- Approved candidate `6669f3911723cbb73f494196e4312ccdae321980` remains an ancestor.
- Annotated [v0.6.0 tag](https://github.com/sebasrodriguezjj-dev/AutoQA/tree/v0.6.0):
  tag object `bea83dc984687dcde97416a8fa57bd2849f8aa0f`; remote peeled target equals
  stable release SHA above. Verified through git ls-remote and local tag type/target.
- [Release-head CI run 45296528515](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45296528515)
  completed success, verify job 138118224986, all steps successful. Run is associated
  with exact promoted PR head; checkout was synthetic merge `f091d87d86afa8aa40543225639de53adbd7a6ed`.
  Linux/Python 3.14.4: 304 passed / 1 expected native-Windows skip / 18 deselected in
  41.93s, plus package/install/export/independent collection and case/pack/full execution.
- At V0.6.0 release integration, main had the verified promoted tree `c5b09d92111b0f3b7ce0ec60c66a15e45afa4c6f`,
  expected parents, version 0.6.0 and clean checkout. Fresh integrated compatibility,
  reliability and H01/H02 regression: **92 passed in 37.91s**.
- Existing workflow runs on pull_request, not main/tag pushes. No separate hosted
  main/tag run is claimed. No GitHub Release entry was requested or created.

## Branches, active PRs and authorized objective

Release branches feat/v04-development, feat/v05-development and feat/v06-development
are preserved. feat/v06-development remains at promoted 530e436; it is merged, not an
active candidate. Historical feat/v03-batch-* local refs remain untouched.

Current verified main: **`57a133626cc9c1b09ddf3039c6521e65ac5fdcc7`**, the approved
foundation merge. [PR #5](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/5) is
**merged/closed**, with parents stable V0.6.0 `bbd54ad0821cb6962c09d8a1149a0f40b936764b`
and audited foundation HEAD `3ca20958420f4f76daf2dff77439170d7c4adeab`. Its integrated
tree `e56b8327aa78ac464477dc39ffdd458148b27b27` equals the audited/CI-tested tree.
The [exact foundation-head CI run 45398766348](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45398766348)
and [verify job 138461518035](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45398766348/job/138461518035)
passed all steps: Linux/Python 3.14.4, 304 passed / 1 expected native-Windows skip /
18 deselected in 32.42s, plus package/install/independent export and execution.
The tested synthetic merge was `dce49090ad2442b95146843b4432a4fdbaff6b52`; no new
push-main CI is inferred. The owner approved the independent audit and explicitly
authorized the subsequent merge. The stable V0.6.0 tag remains at its release SHA.

Current documentation branch: **codex/docs-post-merge-context**, based on verified main.
Fresh GitHub inspection found no open PR before this reconciliation's publication.
The focused [documentation PR #6](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/6)
targets main and must remain unmerged for independent audit. Its final
HEAD, verification results and CI links are recorded in that PR and the external handoff;
this document cannot embed its own eventual commit SHA. Verify fresh GitHub state at
the next handoff. The original `chore/multiagent-foundation` branch is preserved at the
audited HEAD. Local pilot branches codex/pilot-product, codex/pilot-architecture and
codex/pilot-qa-security and all three clean specialist worktrees are preserved.

Active work: **post-merge engineering-context reconciliation**, documentation only.
The foundation is integrated; its original delivery and recovery records below are
historical. Next action is independent audit of this reconciliation ("Audita al dev").
V0.7 Intelligent QA Planning and coverage-gap analysis remains the next planned product
milestone, **not implemented** and not authorized by this task. The owner must explicitly
initiate its development. Roadmap changes, releases and PR merges also require explicit
owner authorization. See [roadmap](roadmap.md) and [workflow](multiagent-workflow.md).

## Implemented source-controlled facts

Python 3.14/uv; Typer/Rich CLI; Pydantic contracts; Playwright/Pytest; Page Object
exports; SQLite project registry and local JSON; real JUnit/JSON/HTML evidence;
optional advisory AI; pinned GitHub Actions code checks. See factual
[module map](architecture.md) and [product vision](product-vision.md).

V0.3 delivers domain/readers/storage, project-bound review/approvals, execution,
reporting and coarse legacy evidence. V0.4 delivers independently runnable reviewed
Page Object frameworks with operation evidence. V0.5 adds reviewed API contracts,
application credential references, deterministic fixtures and protected evidence.
V0.6 adds bounded static analysis, reviewed management, case/pack/suite/tag/full
selection and conservative scope-aware reporting. H01/H02 classification and complete
collection reconciliation repairs remain covered by 25 retained regressions. Collection
is not execution evidence; selected-scope success is not a full regression pass.

## Known defects, residual risks and deferred capabilities

No reproducible mandatory release blocker remains in the verified scope. The historical
V0.5 intermittent API/evidence/JUnit discrepancy remains **unroot-caused**. Separate
bounded persistence/reconciliation regressions do not establish that historical cause.
Static framework understanding is heuristic, custom collectors/configuration partial,
and historical exports need re-export for new runtime fixes. One managed suite per project.

Trusted single local writer/filesystem, unsigned receipts, caller-intent authorization,
no OS sandbox, limited Windows descendant cleanup and no authenticated multi-user
boundary remain. Independent delivery cannot observe later source revocation. API/auth
summary-only evidence suppresses payloads and browser capture, not universal redaction;
legacy/unauthed UI evidence may expose sensitive data. Retention is manual. No complete
platform/browser/client certification, owned hosted HTTPS acceptance or live AI success
is inferred from Linux non-browser CI. External functional generalization remains limited
by the retained authorized-scope evidence. See [security](security.md) and historical audits.

Deferred: autonomous repair, intelligent coverage planning, QA operations dashboard,
central history/CI operations, multi-suite expansion, strong approval identity/signatures,
concurrent writers, OS isolation, universal redaction/automatic purge, arbitrary client
code execution, session acquisition/refresh and remote setup/teardown. Roadmap outcomes
remain proposed; some historical opportunities were superseded by later delivered scope,
so read the latest implementation map rather than assuming every old proposal shipped.

## Current reconciliation verification (2026-11-24)

The complete reusable release gate returned **exit 0** on the documentation branch:
**305 passed / 18 deselected in 193.72s**, Ruff lint/format (67 files), 37-package lock,
frozen compatibility, wheel/sdist inventory, installed 0.6.0 import/distribution/CLI,
approved export metadata and independent dependencies with AutoQA absent. Standalone
validation and complete collection passed; case/pack/all each executed successfully
with one passed invocation and two actual operations. Log:
`.test-work/context-reconciliation-gates.log`; disposable package acceptance:
`.test-work/release-gate-d_nxhu7y`. No browser, client or live-AI benchmark was repeated.

Consistency checks passed for 201 relative Markdown destinations and four role TOML
definitions. Exact comparisons preserve the owner-defined future roadmap, ten-stage
product workflow, mandatory gate commands, historical architecture and original
recovery/publication evidence. Only seven current context/instruction files change;
product code, dependencies, tests, workflows, specialist roles, pilot records and
compatibility fixtures are unchanged. Scoped inventory reviewed 146 tracked files
plus frozen ZIP members, with no conventional credential/private-output findings;
this does not establish universal secret detection or a forensic history audit.

The [PR #6 checks view](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/6/checks)
tracks the final published HEAD. Exact-HEAD CI and inspected job logs remain a post-commit
delivery requirement, recorded in that PR and the handoff after execution. The PR
must remain unmerged for independent audit; these local checks do not authorize merge.

## Historical foundation verification and setup delivery

The remaining sections preserve the original release/foundation delivery and recovery
observations as dated historical evidence. Their pre-audit instructions to leave PR #5
unmerged, and the then-current branch/main descriptions, were superseded by the approved
merge recorded above. They do not revoke that merge or authorize future development.
The [original audited handoff](https://github.com/sebasrodriguezjj-dev/AutoQA/blob/3ca20958420f4f76daf2dff77439170d7c4adeab/docs/project-state.md)
retains the complete pre-merge record at its immutable commit.

[Stable release gate](v06-stable-release-gate.md) records local full checks:
305 passed / 18 deselected in 235.66s; Ruff 67 files; 37-package lock with root-version-only
change; frozen archive/member hashes; wheel/sdist inventory; installed 0.6.0 import/CLI;
reviewed export metadata; AutoQA-absent independent validation/collection and actual
case/pack/full execution (one invocation/two operations each). Scoped inventory: 129
files plus ZIP members, no conventional credential/private-output findings. No new
browser or live AI benchmark. Local logs/evidence are disposable ignored output.

Foundation recovery and publication evidence is recorded below. [Pilot evidence](multiagent-pilot.md) records actual agents, ownership,
worktrees, commits, checks, coordination and limits. Native desktop delegation is exposed;
installed CLI 0.114.0 separately reports multi_agent disabled. Profiles are reusable
instructions, not a claim of automatic CLI loading or access-control isolation.

Original pre-audit delivery boundary: setup PR must remain **open and unmerged**.
That historical boundary was satisfied before the owner's subsequent merge authorization.
V0.7 remains outside this reconciliation's scope.

## Interrupted-session recovery (2026-11-24)

Recovered branch `chore/multiagent-foundation` at
`7d7181050165375459796619c8650dc226a5adcf`. No staged or unstaged changes and no
pending cherry-pick were present. The completed untracked `multiagent-pilot.md`
was preserved for inclusion. All three specialist worktrees were clean and retained.
Exact binary diff comparison across the five foundation commits proved each specialist
patch was integrated once; all seven owned file blobs still matched the original
specialist commits. No recreation, reset, cleanup, history rewrite or release action
was needed. See the [pilot integration table](multiagent-pilot.md).

The recovered `.test-work/foundation-checks.log` ends with **305 passed / 18 deselected
in 216.13s**, following successful Ruff lint/format and 37-package lock checks.
Product source, tests, scripts, workflows, package metadata, dependency lock and frozen
fixtures are unchanged from stable V0.6.0. The later architecture integration changed
documentation only; this full regression therefore covers the final executable tree.
Fresh resumed Ruff lint/format (67 files) and lock checks also passed.

Integrated documentation checks resolved **200 relative destinations**, parsed all four
role TOML definitions, verified the original architecture text remains an exact suffix,
and confirmed unchanged product/tests/lock/workflows and historical audits. Scoped
inventory reviewed **146 tracked/new files plus frozen ZIP members**, with no conventional
credential-pattern or private-output-path findings. This is not universal secret/PII
detection or a forensic audit of Git history.

The resumed package phase returned **exit 0**: wheel/sdist build and inventory,
isolated installed 0.6.0 import/distribution/CLI, reviewed export metadata, standalone
dependency installation with AutoQA absent, validation and complete collection all
passed. Independent case/pack/all each returned 0 with one passed invocation and two
actual operations. Log: `.test-work/foundation-package.log`; acceptance directory:
`.test-work/release-gate-51v6wlf3`. No new browser, client or live-AI execution.

Fresh fetch and remote ref inspection confirmed main and the annotated stable tag
unchanged at the recorded release, no setup branch and no active PR before publication.
Publication details are recorded in the setup PR; final PR HEAD is recorded there and
in the external handoff rather than embedding this document's own commit SHA.

## Setup publication handoff (historical, before approved merge)

The single setup [PR #5](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/5) targets
main from `chore/multiagent-foundation` and remains **open and unmerged**. Fresh remote
inspection before publication found no other active PR. Its initial published recovery
commit was `f40cdd978d2620b4f6d87b82539a8df463e58ec0`; this final link/count handoff
is a subsequent documentation-only commit. Resolve the final branch SHA from the PR
head, not the initial commit or this self-contained document.

The [PR checks view](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/5/checks)
is the canonical current hosted verification link. The Lead must verify success for
the final published HEAD and inspect its actual job logs before reporting completion;
the inspected run/job IDs, checkout SHA, regression/package results and exact final
HEAD are recorded in the PR body and delivery handoff after that post-commit check.
An earlier-head or pending result is insufficient. This source record describes the
publication sequence without claiming future CI success from inside its own commit.

All three specialist worktrees remain available and clean. Stable main and the
annotated `v0.6.0` object/target were verified unchanged during recovery. No release
merge/tag was repeated, no V0.7 work began, and no foundation merge is authorized.
There is no local mandatory-gate blocker; a final mandatory CI failure blocks delivery
until corrected or explicitly reported. Next action after verified publication is
the owner's independent audit trigger: **"Audita al dev"**.
