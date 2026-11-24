# Bounded multi-agent foundation pilot

Date: 2026-11-23, America/Costa_Rica. Scope: independent documentation and engineering
review after verified V0.6.0 release. No V0.7 feature implementation. Common committed
brief: [713b6f8](multiagent-pilot-brief.md), full SHA
`713b6f808bae3156ee7759b16c7a3f24f9631865`, based on stable main
`bbd54ad0821cb6962c09d8a1149a0f40b936764b`.

## Actual delegation and isolation

**Four actual agents**: one Lead and three native subagents, dispatched through this
desktop session's spawn_agent tool. The specialists were independently active with
the same context revision and disjoint assignments. No external orchestration service,
extra user-owned chat or CLI model run was used. Specialists inherited conversation
context but were explicitly directed to read the common committed brief and historical
evidence. Future independent sessions must use written handoffs; shared chat memory is
not assumed. All shell work was assigned an explicit absolute workdir.

| Agent/task | Branch and isolated directory | Exclusive deliverables |
| --- | --- | --- |
| Lead | chore/multiagent-foundation; C:/Users/sebas/Desktop/AutoQA | AGENTS, handoff/workflow/decisions/role definitions, shared briefing, integration, checks, official GitHub delivery |
| Backend/product | codex/pilot-product; C:/Users/sebas/Desktop/AutoQA-worktrees/product | product-vision, roadmap, [product review](pilot/product-review.md) |
| Framework/architecture | codex/pilot-architecture; C:/Users/sebas/Desktop/AutoQA-worktrees/architecture | architecture, [architecture review](pilot/architecture-review.md) |
| QA/security | codex/pilot-qa-security; C:/Users/sebas/Desktop/AutoQA-worktrees/qa-security | release-gates, [QA/security review](pilot/qa-security-review.md) |

Each specialist acknowledged its assigned checkout/context. Git worktree list confirmed
separate branch/HEAD/directory entries. Git objects/refs remain shared and this is not
an OS security sandbox; isolation relies on explicit ownership and workdir discipline.
No specialist wrote the Lead checkout or pushed official refs. Worktrees/branches are
retained for audit; no cleanup removes history or uncommitted work.

## Review, integration and coordination

Specialists read historical V0.1–V0.6 release/architecture/security/roadmap documents
before current summaries and inspected impacted source/test/workflow definitions.
They distinguished Lead-verified release observations from their independent source
reviews. No specialist independently claimed to rerun product tests or live GitHub CI.

| Original specialist commit | Lead integration | Outcome |
| --- | --- | --- |
| 93c39450b3dbdcf440601d439c5de71b7ee2b9fb | d3b21e6 | Three owned product/roadmap/review docs inspected and cherry-picked; no conflict. |
| 3b40a21f44d36830e3a366f4622f991c92dbe386 | a67a375 | Two owned gates/review docs inspected and cherry-picked; no conflict. |
| 95128888257fae682d8b4501a039e75ce0a0a24e | 7d71810 | Two owned architecture/review docs inspected and cherry-picked; original historical suffix preserved; no conflict. |

Lead commits establish instructions and current release handoff centrally; specialists
never edit shared context. All three independently found stale current README text
calling V0.6 an unmerged candidate. They reported it without violating ownership;
Lead corrected README and the current CLI-reference heading. Historical candidate
files remain unchanged. QA identified that exact-head PR workflow association must be
distinguished from synthetic merge checkout; permanent gates/state record both.

The product specialist's isolated link scan reported two references to project-state.md
not present in its base. These were integration dependencies explicitly resolved by the
Lead's new state file, not fabricated specialist success. This demonstrates why the
integrated link gate is required. Source review also distinguishes existing bounded
resource rules from broader deferred SPA permissions.

## Measurements and limits

- Actual agents: 4 total, 3 specialists; all dispatched concurrently at the same base.
- Independent tasks: 3 completed independently; commit and integration evidence above.
- Overlapping file ownership: 0. Checkout write conflicts: 0 observed. Cherry-pick
  conflicts: 0 across all three integrations.
- Specialist checks: owned-path/whitespace/source review and local Markdown destinations.
  Product checked 35 destinations, with two known integration dependencies; QA checked 13.
- Lead integration checks: full regression, frozen compatibility, Ruff/lock, package/
  independent export, links, role TOML and scoped inventory; final outcomes recorded in
  [project state](project-state.md) and the setup PR, not substituted from release checks.
- Coordination problems: stale current wording and cross-task document dependencies;
  handled through messages and Lead-only shared-file edits. The architecture reviewer initially needed to create the untracked empty pilot directory in its own worktree; resolved locally. No blocked/deadlocked task.

Native delegation availability is proven by these tasks, not inferred from documentation.
Installed CLI 0.114.0 reports multi_agent=false; separate CLI delegation remains disabled.
The four repository TOML role definitions parse and follow current documented schema,
but automatic profile discovery/reload was not exercised. Independent CLI sessions and
repository-local native skill loading were not exercised; no external dependency was
added to emulate them. See [workflow](multiagent-workflow.md) for fallback and limits.
This pilot validates bounded engineering collaboration, not autonomous product behavior,
hostile-agent isolation or performance superiority. No timing/speedup claim is made.

Foundation success additionally requires a real setup PR and successful CI associated
with its exact final HEAD. That PR remains unmerged for owner-triggered independent audit.

## Recovery verification (2026-11-24)

After the usage-limit interruption, Lead recovered the completed architecture
integration at 7d71810 and preserved this report. Exact diff and owned-file blob
comparisons confirmed all three specialist tasks were integrated once, without
repeating assignments or cherry-picks. All three specialist worktrees remained clean.
The recovered full non-browser run passed 305 tests (18 deselected) in 216.13s;
its executable tree is unchanged. Fresh package/install/independent validation,
collection and actual case/pack/full execution returned exit 0. Documentation/role/
history/inventory checks also passed; see [project state](project-state.md).
No new specialist run, cleanup, stable release operation or V0.7 work was performed.
