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
The new focused documentation PR must remain unmerged for independent audit. Its final
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

The focused PR's final exact-HEAD CI and inspected job logs remain a post-commit
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
