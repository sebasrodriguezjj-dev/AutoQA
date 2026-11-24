# Repository engineering roles

Common instructions: read [AGENTS.md](../../AGENTS.md) and all linked permanent context;
verify the Lead's shared briefing, worktree, baseline, exclusive ownership, acceptance,
approved targets and limits. Current stable release is V0.6.0; no V0.7 implementation
is authorized by foundation setup. Never modify another checkout or publish as a specialist.

The project-scoped TOML profiles in [.codex/agents](../../.codex/agents) are reusable
instructions following the current documented custom-agent schema. Model and permissions
inherit from the caller. Their automatic discovery has not been tested in installed CLI
0.114.0; use explicit role briefs when unavailable. The actual pilot used native task
messages. These roles are repository governance, not authenticated security identities.

| Profile | Responsibility | Return |
| --- | --- | --- |
| lead_engineering | Alignment, briefing, decisions, integration, gates and publication | Verified GitHub PR/HEAD/CI, residual risks and maintained state |
| backend | Contracts, core services, persistence and rules in assigned paths | Local commit, tests, compatibility and data risks |
| framework | Playwright/Pytest, UI/API generation, exporter/runtime/CLI in assigned paths | Local commit, export/independence evidence and limitations |
| qa_security | Independent test/review, adversarial cases, evidence/security/compatibility | Findings/reproductions, local test commit if assigned, residual risks |

Coding tasks require an isolated worktree and real regression tests. Documentation-only
reviews validate facts and destinations without inventing product behavior or test results.
Specialists receive all shared context even when their files cover only one concern.
