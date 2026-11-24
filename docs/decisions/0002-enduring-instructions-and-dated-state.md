# ADR 0002: enduring instructions and dated engineering state (D02)

Status: adopted for the owner-authorized V0.7 development; 2026-11-24.

## Evidence and decision

Foundation PR #5 and reconciliation PR #6 were correctly left unmerged at delivery,
then independently approved and explicitly merged. Permanent instructions repeated
temporary merge prohibitions, causing stale context after each merge. Original
[foundation evidence](../multiagent-pilot.md) and Git history remain intact.

Keep AGENTS.md and role/workflow/release-gate instructions enduring. Product vision
holds product purpose; roadmap holds owner-approved direction. Dated project-state
holds release/branch/PR/CI observations and current explicit authorization. Live GitHub
is authoritative for current refs, PRs and checks. Always verify it; source text is not
live state. Temporary task restrictions belong in dated state and the owner request.

## Alternatives and consequences

Continuing post-merge instruction rewrites causes recurring correction cycles. Removing
handoffs loses audit evidence. The chosen split preserves original dated records and
requires a fresh handoff per task without hardcoding transient rules in every profile.
Explicit owner authorization still controls roadmap changes, sensitive actions, merges
and releases. No product/runtime/security/compatibility contract changes follow from D02.

Verify by checking enduring rules for current PR/version-specific prohibitions and
preserving historical record content. V0.7 requires its own real acceptance and CI;
this structural decision is not evidence of implemented planning functionality.
