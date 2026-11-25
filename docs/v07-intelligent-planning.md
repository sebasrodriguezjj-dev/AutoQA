# V0.7 Intelligent QA Planning and Coverage Gap Analysis

The V0.7 candidate adds bounded deterministic planning over explicitly supplied JSON
requirements and current local QA inventory. It does not ingest arbitrary documents,
execute inspected code, modify client applications or create executable tests from
proposals. See [contract/interface agreement](v07-interface-agreement.md) and
[current dated handoff](project-state.md) for implementation/verification status.

## Input and provenance

Use [synthetic JSON example](../examples/v07_requirements.json), not real client data
in the public repository. The root schema is 0.7, separate from historical domain 0.3,
API 0.5 and management 0.6. Sources are declared references; they are not fetched or
independently authenticated. Requirements include stable REQ-* IDs, description,
source_id, review_status, kind, optional expected_behavior, priority, business_criticality
and user_impact (1..5). Evidence references point to supplied source records. Optional
related_ids reference declared requirements. Workflow/observed-evidence IDs refer only
to the actual current discovery inventory. Context preserves workflow_provenance and
evidence_provenance; only OBSERVED supports these explicitly observed references.
SOURCE, INFERRED, UNKNOWN, VERIFIED_REQUIREMENT and missing provenance remain
insufficient for observation-based confirmation/risk even when the ID is known.

Mappings explicitly bind requirement_id to an existing TC-* case, its case_signature,
a review_status and rationale. Copy exact current signatures from intelligent-plan's
context.cases after reviewing the requirement-to-case relationship. No title matching
or observation-based automatic coverage claim occurs. Review requirements/mappings by
editing the bounded JSON, then explicitly import the reviewed revision. A declared
approved requirement is operator-supplied review state, not an authenticated identity.

Limits: 256000 input bytes, 100 requirements, 100 sources, 1000 supplied evidence
records, 2000 mapping pairs, 20 reference IDs of each kind per requirement and 10
explicit design hints. IDs/text/collections and current context are bounded. Extra
Explicit import applies the same byte bound to normalized stored JSON; a raw document
near the limit may need to be reduced before import even when read-only analysis accepts it.
fields, malformed/future schemas, duplicate JSON keys/IDs, invalid declared references,
nonfinite numbers, unsafe control characters and conventional credential material fail.
Do not place secrets/PII in descriptions or tags; this is not universal redaction.

## CLI and review workflow

```powershell
# Read-only proposal/coverage; supplied inventory is not saved automatically.
uv run autoqa intelligent-plan --requirements examples/v07_requirements.json --project projects/owned
uv run autoqa coverage-report --requirements examples/v07_requirements.json --project projects/owned
# Explicitly import reviewed declarative data. Existing cases/receipts/suite stay intact.
uv run autoqa requirements-import examples/v07_requirements.json --project projects/owned
uv run autoqa intelligent-plan --project projects/owned
# Use actual PLAN-* and PROP-* IDs from the current JSON output.
uv run autoqa plan-review PLAN_ID --accept PROP_ID --project projects/owned
uv run autoqa plan-review PLAN_ID --reject PROP_ID --project projects/owned
```

All new output is JSON. Only requirements-import and plan-review write new V0.7
sidecars; analysis/coverage do not write project files or audit events. Review commands
reuse project-bound plan/review authorization. They never invoke existing scenario
approval, mutate scenario content/signatures/receipts, approve suite membership, generate
code or execute tests. Accepted means the operator accepts a planning recommendation;
it remains MANUAL_REVIEW. Implement an executable scenario only through the existing
reviewed UI/API workflow, then explicitly approve it and review suite membership.

Review binds the exact deterministic PLAN-* input/context digest and stable PROP-* IDs.
Provenance maps participate in that digest: downgrading observation to source invalidates
prior planning acceptance. Conflicting categories for one evidence ID fail; identical
same-category repetitions may deduplicate.
Changed requirements, current cases/signatures/review/receipt validity, observed evidence or suite
context invalidate prior planning decisions. Stale reviews remain disclosed and cannot
silently carry acceptance forward. Unknown/empty/duplicate review IDs and stale plan
IDs fail before writes. This is trusted single-writer local integrity, not signed audit
identity or a concurrent multi-user transaction system.

## Coverage meaning

Each requirement row lists confirmed reviewed mappings, proposed mappings, missing
mappings, unsupported automation, insufficient evidence, stale relationships or rejected
requirements excluded from planning. Rows can have several findings. Confirmation
requires approved requirement/known expectation, valid declared observed references,
explicit approved exact-signature mapping and a current approved supported case with
an intact existing receipt. Pending cases/mappings never count as confirmed. Missing,
changed, rejected or invalid-receipt relationships remain conservative. Unsupported
cases remain visible; they do not disappear into a successful automation numerator.

Counts describe this supplied inventory and reviewed test mappings only. There are no
coverage percentages, no full-application coverage claim and no computed executed
coverage: execution_coverage is always NOT_ASSESSED. Observed controls, static candidates,
Pytest collection and selected-scope passes are not requirements coverage evidence.
Automation feasibility reflects recorded case feasibility and manual kind, not a new
compiler validation or proof of exportability. Suite/pack/tag/enabled context reflects
reviewed current metadata; stale suite metadata
is disclosed separately and does not become a valid membership claim.

## Explainable proposals and risk

Each nonrejected requirement receives bounded positive, negative, boundary, regression
and error-handling review prompts, using explicit design hints when provided. Supplied
expectations remain attributed to their source. Generic nonpositive expectations stay
unknown; no endpoints, selectors, HTTP responses, input limits, auth rules or validation
messages are invented. Assumptions ask the owner to confirm applicability and outcomes.
All proposals retain source/evidence links, requirement identity, risk and review state.

Risk is a transparent prioritization heuristic, not a measured failure probability:
criticality*4 + impact*4 + priority (Critical15/High12/Medium8/Low4) + coverage gap15 +
observed functionality10 + feasible mapped execution10 + uncertainty10, each applicable
only under the documented rules. Score 0..100; High>=70, Medium>=40, otherwise Low.
Reasons expose the seven contributions. Requirement priority and uncertainty can elevate
manual review work without suggesting it is executable.

The same validated logical inventory/context yields the same plan and proposal IDs;
list order, runtime timestamps and random identity do not manufacture new plans.
Planning review disposition is excluded from the plan input digest. Model output remains
suitable for later adapters; no web server, frontend, provider credential or AI call is
required. Existing optional AI recommendations remain a separate review-only capability.

## Boundaries and validation

V0.7 planning does not prove application behavior, discover all requirements, perform
semantic NLP matching, ingest arbitrary documents, auto-compile proposals, run/repair
client code, replace approval receipts or add multi-user identity/isolation. Current
network, privacy, trusted-local and legacy compatibility boundaries remain. The
historical V0.5 intermittent evidence incident is still unroot-caused.

A-H acceptance, independent tests, exact candidate/CLI behavior, actual verification
counts and residual limitations belong in [candidate evidence](v07-release-candidate.md).
Existing V0.6 execution/framework gates remain mandatory. Browser acceptance is added
only when browser logic changes; new planning itself performs no browser/API requests.
