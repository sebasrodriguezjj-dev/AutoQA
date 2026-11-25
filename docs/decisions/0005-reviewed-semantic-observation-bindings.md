# ADR 0005: Reviewed semantic observation bindings (H03)

Status: implemented in V0.7 RC1, pending independent audit.
Date: 2026-11-24, America/Costa_Rica.
Authorization: owner-requested H03 remediation on existing PR #7; no merge, stable
release, roadmap change or future milestone implementation.

## Evidence and alternatives

At audited HEAD 8b6f71eea1c726607159e5e77ff7d1e0a9923e0e, six synthetic regressions
failed: workflow/page association changes and required/min/max drift preserved accepted
planning snapshots, while conflicting same-ID observations were accepted. A seventh
test confirmed that the legacy element ID excludes validation changes. An initial
fixture needed a missing locator stub; the corrected reproduction isolates six actual
defects. Both logs remain locally in `.test-work/v07-h03-before*.log`. Production
edits began only after the corrected reproduction.

Changing legacy IDs would affect historical artifacts. Hashing all discovery JSON
would invalidate review on timestamps and paths. Changing only the plan digest would
still allow a reused ID to confirm a different requirement relationship. These
alternatives do not meet the required integrity boundary.

## Decision

The bounded adapter hashes semantic projections using SHA-256 and domain separator
`autoqa-planning-identity-v1`. Only ID-to-hash maps enter planning output:
`context.workflow_fingerprints` (up to 2000) and `context.evidence_fingerprints` (5000).
The existing 5 MB source limit, typed discovery parsing and inventory bounds remain.

| Object | Semantic projection |
| --- | --- |
| Element | Page URL and typed element fields except discovered_at/evidence paths: ID, kind, name, href, input_type, required, role, all attributes including validation limits, locators, options, form and components. |
| Page | URL, title, status, headings and unique element hashes. |
| Evidence record | ID, category, description, page association; corresponding page hash when available and same-ID element hash when present. |
| Workflow | All typed fields except evidence paths; current page hash and linked element hashes. Workflow step sequence remains meaningful. |

Dictionary keys and unordered collections are canonicalized. Element/record timestamps,
screenshot/artifact/evidence paths, discovery timestamp, page depth, readiness and
dynamic telemetry are excluded. Attributes/components remain conservatively semantic;
incidental recorded changes there may require review. Text inside descriptions remains
semantic even if it describes paths or time. Unrecorded behavior is outside this model.

Conflicting same-ID record content, element content/page association or same-URL page
content fails generically. Equivalent record repetitions and element observations
deduplicate. Record/element overlap joins both records, requiring OBSERVED and matching
page association (or an unspecified record page). Duplicate workflow IDs still fail.

Requirements may declare `workflow_bindings` and `evidence_bindings`, maps of declared
reference IDs to independently reviewed current hashes, each limited to 20 entries.
Declared observations support confirmation/risk only with actual OBSERVED provenance
and matching explicit bindings. Missing bindings are insufficient; changed/missing
bound observations make active mappings stale. Requirements without declared observed
references retain their existing explicit case-review semantics.

The operator inspects actual local evidence and the requirement relationship before
copying hashes into reviewed requirements. Import and plan acceptance never create or
refresh bindings. A CURRENT planning disposition can coexist with a stale requirement
relationship. A deliberate reviewed requirements revision restores that relationship
and changes the plan digest.

## Compatibility, security and verification

Existing V0.7 input remains parseable; ID-only observation relationships now need
explicit bindings for confirmation. New context fields intentionally stale older plan
reviews. Legacy IDs, schemas, signatures, receipts, runtime and frozen fixtures stay
unchanged. Planning stays read-only and separate from executable approval, with
SUPPLIED_REQUIREMENTS_ONLY and NOT_ASSESSED execution coverage.

Hashes avoid emitting raw discovery content but are not encryption, authenticated
identity, semantic equivalence proof or universal privacy protection. Low-entropy
content can be guessed. Operator-supplied requirements still contain text. Trusted
local filesystem/operator and single-writer assumptions remain. See
[tests](../../tests/test_v07_evidence_identity.py),
[projection](../../src/autoqa/planning_identity.py) and
[candidate evidence](../v07-release-candidate.md) for actual verification.
