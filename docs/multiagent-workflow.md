# Permanent multi-agent workflow

Read [AGENTS.md](../AGENTS.md), [vision](product-vision.md), [state](project-state.md),
[architecture](architecture.md), [roadmap](roadmap.md), [gates](release-gates.md),
[security](security.md) and [decisions](decisions/README.md) before work. These describe
engineering agents working on AutoQA; they do not claim autonomous product workers.

## Installed capability observations

Observed 2026-11-23, America/Costa_Rica:

| Capability | Actual observation and boundary |
| --- | --- |
| Native subagents | This desktop chat exposes spawn_agent/send_message/followup_task/list_agents/wait_agent and supports one Lead plus three specialists (four active slots). The pilot uses these actual tools. |
| Concurrent execution | Three specialist tasks dispatched concurrently, each receiving the same briefing commit; see [pilot](multiagent-pilot.md) for completion evidence. |
| Git worktrees | git worktree add/list works; three distinct pilot checkouts created. Git objects/refs are shared, working directories/indexes are separate. |
| Independent sessions | Installed codex-cli 0.114.0 exposes exec/resume/fork and --cd. Separate sessions are available as a workflow; no independent CLI model run or cross-session shared state is certified by this pilot. |
| Agent instructions | Native tasks accept explicit role/common-context briefs; AGENTS.md supplies repository rules. Committed role TOML files follow current official custom-agent schema; automatic discovery/reload is not exercised in this existing chat. |
| Repository-local skills | Current official documentation supports .agents/skills; existing skills/*.md are AutoQA QA reference documents, not native SKILL.md packages. No new skill or orchestration dependency is needed for this pilot. |
| CLI delegation difference | codex features list reports multi_agent experimental=false and child_agents_md=false in installed CLI 0.114.0. Do not claim CLI native delegation is enabled merely because this desktop chat supports it. Global CLI settings were not changed. |

Current [official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
describes project .codex/agents TOML files and [agents] concurrency settings. The
[official repository guidance](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)
describes AGENTS.md and maintained context. Actual environment/tool observations outrank
general availability claims. Validate profile loading before relying on it in a new client.
This repository stores profiles without changing global settings or adding an untested
CLI feature override. Lead enforces the observed four-slot limit through task dispatch.

## Organization and briefing

| Role | Ownership and responsibility |
| --- | --- |
| Lead Engineering Agent | Purpose/roadmap alignment, common briefing, acceptance, decisions, integration checkout/branch, conflict resolution, quality gates, all official GitHub pushes/PRs, final state/handoff. |
| Backend Agent | Assigned domain contracts, pure rules, application services, data/persistence. |
| Framework Agent | Assigned Playwright/Pytest, UI/API compiler/exporter, standalone runtime and CLI integration. |
| QA & Security Agent | Independent test design, negative/adversarial review, compatibility, genuine evidence and security boundaries. |

Start with a briefing containing origin and verified base/context SHA; product purpose;
current stable release and active authorized version goal; relevant source/design links;
architecture/compatibility invariants; approved targets and security limitations;
exclusive file ownership; focused/full test expectations; acceptance and definition of
done; prohibited work; and a return format (commit SHA, changed paths, tests, findings,
limitations/blockers). Every specialist acknowledges its worktree, branch and baseline.
For the initial context-construction pilot use the [fixed brief](multiagent-pilot-brief.md).
For future work use current permanent context, not that dated snapshot.

## Isolation, integration and publication

1. Lead fetches origin/tags, verifies GitHub PR/head/base/checks and local changes, reads
   the active milestone and confirms owner authorization. Record a dated state snapshot.
2. Lead owns one integration branch. Create each specialist branch/worktree from the same
   committed context revision. Choose unique directories; never reuse a dirty checkout.
3. Assign disjoint files before dispatch. Specialists explicitly set absolute workdir on
   every shell call; inherited parent cwd is not isolation. No two writers in one checkout.
   Move shared-file work to the Lead; revise ownership before any new assignment.
4. Specialists use their checkout only, run approved focused verification, commit only
   owned files and return the full SHA/evidence/limits. They never push the official branch,
   merge main, create tags or publish separate PRs. They must not mutate shared refs/other
   worktrees, invoke hooks that write elsewhere or assume the Lead has their tool memory.
5. Lead inspects each commit diff and tests, then cherry-picks verified commits sequentially
   into integration. Resolve conflicts centrally after consulting owners, rerun affected
   checks and record resolutions. Do not silently discard review findings.
6. Run the integrated mandatory gates, package/export behavior, link and inventory review.
   Update state and decisions, commit and push the official branch without force. Create
   or update one PR; verify mandatory jobs associated with its exact current HEAD and
   inspect executed checkout/logs. A new commit invalidates previous-head CI evidence.
7. Deliver actual results/residual risks and the next authorized action. Keep worktrees
   until handoff/audit; removal is deliberate and must not discard uncommitted work.

Example future setup (branch names/placeholders need task-specific values):

```powershell
git fetch origin --tags
git switch -c codex/integration-TASK origin/main
git worktree add -b codex/backend-TASK ../AutoQA-worktrees/backend-TASK HEAD
git worktree add -b codex/framework-TASK ../AutoQA-worktrees/framework-TASK HEAD
git worktree add -b codex/qa-TASK ../AutoQA-worktrees/qa-TASK HEAD
# Lead inspects returned SHA before: git cherry-pick SPECIALIST_SHA
```

When native tools are absent, use independently opened Codex sessions with explicit
`codex --cd ABSOLUTE_WORKTREE` and the same briefing. Independent sessions do not share
chat memory automatically; commits and written handoffs are the integration mechanism.
Do not add external orchestrators to simulate native delegation.

## Definition of done and startup boundary

Implementation must match authorization/acceptance, retain invariants and real regression
coverage, pass focused plus full gates, preserve security/evidence limits and include
updated context and residual risks. Delivery requires a real verified GitHub PR or a
clearly identified blocker/draft. Only separately authorized release work can merge/tag.
The foundation was independently approved and [PR #5](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/5)
merged at `57a133626cc9c1b09ddf3039c6521e65ac5fdcc7`. Its original delivery and pilot
records retain their pre-merge instructions as historical evidence; they do not describe
the current PR state. V0.6.0 remains the stable release. Current authorization covers
post-merge context reconciliation and its independent audit; this documentation PR
must remain unmerged until separately authorized. Roadmap changes and releases require
explicit owner authorization. V0.7 is planned, not implemented or authorized by the
foundation merge. After explicit V0.7 authorization, Lead refreshes GitHub/context,
defines a bounded planning/coverage-gap design and acceptance criteria,
then delegates disjoint backend/framework/QA work. Do not infer permission to implement
V0.7 from the roadmap or from the existence of these role profiles.
