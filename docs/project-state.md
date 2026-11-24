# Permanent project state and engineering handoff

Last verification: **2026-11-23, America/Costa_Rica**. This is a dated handoff, not live
GitHub state. Before work the Lead must fetch and inspect actual repository, branch,
PR/head/base and associated exact-head check state. Update this file at every development
and release handoff. Source-controlled implementation facts and remote observations
are separated below. Do not treat historical authorization statements as new permission.

## Verified stable release (GitHub and Git observations)

- Repository: [sebasrodriguezjj-dev/AutoQA](https://github.com/sebasrodriguezjj-dev/AutoQA).
- Latest verified stable: **V0.6.0**. Official main/release SHA:
  [`bbd54ad0821cb6962c09d8a1149a0f40b936764b`](https://github.com/sebasrodriguezjj-dev/AutoQA/commit/bbd54ad0821cb6962c09d8a1149a0f40b936764b).
- [PR #4](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/4) merged using a merge
  commit with parents V0.5 main `590832c229f9177c20eb4b928f78beac42488523` and promoted
  feature HEAD `530e436777c149164cb14be8fc9c34178ce09d5f`. All feature history remains.
- Approved candidate `6669f3911723cbb73f494196e4312ccdae321980` remains an ancestor.
- Annotated [v0.6.0 tag](https://github.com/sebasrodriguezjj-dev/AutoQA/tree/v0.6.0):
  tag object `bea83dc984687dcde97416a8fa57bd2849f8aa0f`; remote peeled target equals
  official main above. Verified through git ls-remote and local tag type/target.
- [Release-head CI run 45296528515](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45296528515)
  completed success, verify job 138118224986, all steps successful. Run is associated
  with exact promoted PR head; checkout was synthetic merge `f091d87d86afa8aa40543225639de53adbd7a6ed`.
  Linux/Python 3.14.4: 304 passed / 1 expected native-Windows skip / 18 deselected in
  41.93s, plus package/install/export/independent collection and case/pack/full execution.
- Integrated main has exactly the verified promoted tree `c5b09d92111b0f3b7ce0ec60c66a15e45afa4c6f`,
  expected parents, version 0.6.0 and clean checkout. Fresh integrated compatibility,
  reliability and H01/H02 regression: **92 passed in 37.91s**.
- Existing workflow runs on pull_request, not main/tag pushes. No separate hosted
  main/tag run is claimed. No GitHub Release entry was requested or created.

## Branches, active PRs and authorized objective

Release branches feat/v04-development, feat/v05-development and feat/v06-development
are preserved. feat/v06-development remains at promoted 530e436; it is merged, not an
active candidate. Historical feat/v03-batch-* local refs remain untouched. main is the
verified release SHA above at this observation.

Current integration branch: **chore/multiagent-foundation**, based on that stable main.
The setup PR URL, final branch HEAD and associated exact-head hosted verification are
recorded in the setup delivery section below and in that PR. The final commit is reported
outside itself to avoid a self-referential SHA. Local pilot branches codex/pilot-product,
codex/pilot-architecture and codex/pilot-qa-security are isolated review branches, not
extra official PRs. Verify fresh remote active PR inventory at the next handoff.

Active milestone: **permanent engineering foundation on V0.6.0**. This task authorizes
context/governance/review and its unmerged setup PR only. Next authorized objective
is the owner's independent audit trigger **"Audita al dev"**. V0.7 Intelligent QA
Planning and coverage-gap analysis is the next proposed product milestone, not currently
authorized development. Do not implement it or alter the owner roadmap without explicit
authorization. See [roadmap](roadmap.md) and [workflow](multiagent-workflow.md).

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

## Verification evidence and setup delivery

[Stable release gate](v06-stable-release-gate.md) records local full checks:
305 passed / 18 deselected in 235.66s; Ruff 67 files; 37-package lock with root-version-only
change; frozen archive/member hashes; wheel/sdist inventory; installed 0.6.0 import/CLI;
reviewed export metadata; AutoQA-absent independent validation/collection and actual
case/pack/full execution (one invocation/two operations each). Scoped inventory: 129
files plus ZIP members, no conventional credential/private-output findings. No new
browser or live AI benchmark. Local logs/evidence are disposable ignored output.

Foundation integrated gates and exact-head hosted result are pending until recorded by
the Lead below. [Pilot evidence](multiagent-pilot.md) records actual agents, ownership,
worktrees, commits, checks, coordination and limits. Native desktop delegation is exposed;
installed CLI 0.114.0 separately reports multi_agent disabled. Profiles are reusable
instructions, not a claim of automatic CLI loading or access-control isolation.

Setup PR must remain **open and unmerged**. Final delivery stops there. Do not begin V0.7.
