# V0.8 durable engineering checkpoint

Date: 2026-11-25, America/Costa_Rica. Branch: feat/v08-development.
Stable baseline main: 2243611658accb05afc39593ff6d21fd1e4ba369.
Stable tag object/target/tree verified; no open GitHub PR at preflight; Lead clean and
all six historical specialist worktrees preserved. See ignored `.test-work/v08-preflight.json`.

Batch A: shared strict DTOs, bounded IO, maintain intent, architecture/interface and
ADR 0006 frozen for specialist implementation. No V0.8 candidate claim yet. Package
metadata remains stable until supported acceptance is satisfied. No runtime features
are claimed from a design contract. Native delegation available; profiles explicitly
read because automatic loading is not demonstrable.

Assignments: Backend v08_diagnosis/v08_impact/v08_data plus its backend tests;
Framework v08_maintenance/v08_reconciliation plus framework tests;
QA independent acceptance/security tests and independent-review record. Each has a
new isolated V0.8 worktree from the same committed briefing; original worktrees untouched.
Lead owns contracts/IO/auth/CLI/ApplicationEngine/gates/version/permanent documentation.

Integrated commits: initial shared briefing only. Remaining commits: all specialist work.
Current defects: no completed implementation verified yet. Pending: all A-J acceptance,
full gates, affected owned browser acceptance, installed V0.8 commands and exact-head CI.
Last verified tree: stable 3b48f64a2f9a66b6f1b04269935f5cb91c635c88.
Exact next action: dispatch the three assigned specialists on the committed common
briefing, implement Lead adapters, review returned commits once, integrate and verify.
Owner boundary: one candidate PR, no merge/tag/stable V0.8/V0.9/unrelated product work.


## Batch B/C checkpoint after shared boundary review

Lead HEAD before this checkpoint: b922be7. Shared briefing947bc39; amendments09c96ab
(safe run snapshot/data bounds),41ed7d1 (strict conservative flags),c6dc572 (reject
remote/device/ADS paths). Lead adapters550884b; QA source-only0e97613 integrated once
as b922be7. Source/private byte inventories and legacy V0.7 semantic protections remain.

Active isolated worktrees: v08-backend/codex/v08-backend; v08-framework/codex/v08-framework;
v08-qa/codex/v08-qa under C:/Users/sebas/Desktop/AutoQA-worktrees. Backend and Framework
source commits still pending, QA service acceptance draft waiting for those dependencies.
Do not cherry-pick duplicate shared/CLI dependency commits from specialist branches.
Only integrate each specialist's owned source/test diff once.

Verified Lead checks: 39 shared independent security and CLI tests passed in7.08s;
log .test-work/v08-shared-integrated.log. QA preserved failing shared-boundary repro
logs in its own ignored .test-work directory; details in independent-review.md.
Current known implementation gaps: complete service/real A-J acceptance not integrated;
installed V0.8 gate and final candidate metadata remain pending. No candidate-ready claim.
Exact next action: inspect/integrate verified Backend/Framework owned commits; supply
SHAs to QA for independent service acceptance; extend installed gate and run actual
owned browser workflow; only then prepare0.8.0rc1 and complete final gates/publication.
