# ADR 0001: supervised local product and isolated engineering

Status: adopted for foundation setup review; 2026-11-23, America/Costa_Rica.
Authorization: owner's V0.6 stable release and permanent multi-agent migration request.
This is a new governance decision, not a claim about undocumented historical intent.

## Context and alternatives

AutoQA's existing [V0.3 design](../architecture-v03-plan.md),
[V0.4 exporter](../v04-architecture.md), [V0.5 API boundary](../v05-architecture.md)
and [V0.6 management](../v06-architecture.md) retain a synchronous local tool,
reviewed templates, independent exports and backward readers. The owner explicitly
rejects a SaaS direction and requires stable release before governance migration.
Alternatives considered here: shared writable checkout, isolated worktrees, or an
external orchestrator. Shared writes obscure ownership; an external orchestrator adds
an unnecessary dependency. Existing Git and native delegation are sufficient.

## Decision

Retain the local supervised product. One Lead integrates and publishes; up to three
specialists use isolated worktrees, common context and non-overlapping ownership.
Native delegation is used when exposed by the active environment. Independent Codex
sessions with worktrees are the fallback. No automatic shared-memory assumption.
Future roadmap changes require explicit owner approval. QA review remains independent
from implementation, and application mutation authority is never implied by repository
editing authority. No V0.7 implementation is part of this foundation.

## Consequences and verification

Repository-local instructions and role definitions travel with source; they are not
an OS access-control boundary. The Lead reviews specialist commits and runs integrated
checks. Context handoffs need active maintenance and fresh remote verification.
The [pilot brief](../multiagent-pilot-brief.md) fixes the common baseline; the
[pilot report](../multiagent-pilot.md) records actual isolation, integration and limits.
Existing trust/security/compatibility constraints are unchanged. Revisit only through
a separately authorized ADR; no new service or orchestration dependency is introduced.
