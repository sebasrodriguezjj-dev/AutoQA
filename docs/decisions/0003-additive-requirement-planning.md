# ADR 0003: additive requirement planning and conservative mapping evidence

Status: adopted for owner-authorized V0.7 candidate development; 2026-11-24.

## Context and alternatives

V0.6 already has receipt-bound reviewed UI/API cases and independently reviewed suite
membership. Historical domain 0.3, API 0.5 and management 0.6 are compatibility contracts.
The owner requests traceable planning over bounded supplied requirements, without
invented execution coverage or bypassing existing review. Automatic text matching,
executable proposal conversion and a replacement scenario-approval model would exceed
those evidence/approval boundaries. Arbitrary document ingestion adds unbounded parsing
and ambiguous provenance. They are excluded from this first planning version.

## Decision

Add independent strict schema 0.7 DTOs, a pure deterministic planner and a focused local
service. Explicit source/requirement/evidence/mapping data is the reviewed inventory;
missing, uncertain, unsupported and stale relationships stay visible. Confirmation
requires explicit exact-signature mapping and the existing case receipt, never inferred
semantic equivalence. Retain actual observation provenance: known SOURCE/INFERRED/
UNKNOWN facts are not OBSERVED support. Reject conflicting categories and bind review
to provenance-sensitive snapshots. Outputs cover supplied requirements only, show counts without
percentages and always state executed coverage NOT_ASSESSED.

Read-only analysis uses current cases/receipts/discovery/suite state without persistence.
Only explicit import/review writes new sidecars through existing confined storage and
project-bound plan/review intent. Accepted/rejected planning disposition binds a current
snapshot; it cannot grant scenario or suite approval, mutate prior signatures, generate
code or execute anything. Existing scenario approvals remain the only scenario approval
system. Unknown outcome proposals are manual review prompts with attributed assumptions.

Canonical digests and stable content-derived IDs make equivalent inputs reproducible.
Risk factors are explainable heuristics, not measured failure probabilities. Current
reviewed suite labels are retained exactly rather than rewritten into new identifier
syntax. No dependency, service backend, AI provider or client-code execution is required.

## Consequences and verification

Review remains explicit and bounded; the first version requires operators to supply
mapping signatures and expected behavior. It does not prove semantic correctness of a
human mapping, authenticate the reviewer or quantify full application/code coverage.
Planning records are unsigned trusted-local data with single-writer assumptions.
Changed current context invalidates planning acceptance; source receipt semantics stay.

Verify A-H through synthetic UI/API inventories, strict/adversarial input tests, unknown/
unsupported/stale coverage, read-only byte preservation, snapshot-bound review, deterministic
reordering and unchanged historical compatibility/framework execution gates. Future
NLP, automatic scenario compilation, broader ingestion and provider assistance require
separate reviewed scope. V0.8 maintenance is not implemented here.
