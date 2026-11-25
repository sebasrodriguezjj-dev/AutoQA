# V0.7 shared contract and specialist briefing

Owner explicitly authorized V0.7 and D02 on 2026-11-24. Verified starting main:
`baa776d2253831f08dc7d630cf0e67d0a22d4b8f`; stable product remains annotated v0.6.0.
D02 was committed first as `d03c74d`. No open PR at startup; clean checkout and
original three pilot worktrees preserved. Integration branch feat/v07-development.

## Common context and authorization

Read AGENTS.md and permanent vision/state/architecture/roadmap/gates/security/decisions,
V0.6 architecture, management, approvals, API/functional contracts and impacted tests.
AutoQA is a supervised local QA Engineering tool, not SaaS. V0.7 adds reviewable
requirements planning, not autonomous client code modification. Historical domain 0.3,
API 0.5, management 0.6, legacy CLI/import/receipts/signatures/readers/frozen fixtures
must remain unchanged. No execution/install of inspected client code, no new network
permission, AI approval or arbitrary executable generation. Synthetic fixtures only.
The historical V0.5 intermittent evidence incident remains unroot-caused. Trusted local
single writer, unsigned review/receipts, no sandbox/universal redaction remain limits.
Current task ends at one verified unmerged development PR, 0.7.0rc1 only after acceptance.
No merge/tag/stable release/V0.8. Owner controls roadmap changes and publication gates.

Native spawn tools are available (Lead plus three specialists). Automatic TOML role
loading is not observable in this session/tool schema; read assigned role explicitly
and use this briefing. CLI 0.114.0 has multi_agent=false. Do not claim automatic loading.
Each specialist must explicitly set its assigned absolute workdir for every shell call,
acknowledge common context/role/ownership, commit locally and never push or edit another
checkout. No extra agents. Deliver SHA, tests/evidence, findings and limitations.

## Frozen shared DTO/API agreement

Lead owns `src/autoqa/planning_contracts.py`; read the actual model fields and validators.
All V0.7 models forbid extra fields, use strict scalar validation, bounded IDs/text/lists,
schema 0.7, serializable outputs and no random/time identity. No changes to core/domain
or existing planning/APIScenario/management schemas. Request contract changes from Lead.

Input `RequirementsDocument`: explicit sources/reference/provenance, supplied evidence,
requirements with review/priority/impact/criticality, optional related/workflow/observed
references, declared expectations/design hints, and explicit requirement/case mappings.
Mapping approved requires case signature. Supplied relationships validate or fail before
writes; absent/stale case relationships become conservative findings, never successes.
Unknown observed workflow/evidence references stay insufficient, never inferred facts.

Backend public functions in `autoqa.qa_planning`:
- `parse_requirements(payload: bytes) -> RequirementsDocument`: max 256000 bytes; UTF-8
  (BOM may be accepted), JSON object only; duplicate JSON keys/NaN/infinity/invalid UTF-8,
  recursion/resource/validation errors fail as generic ValueError without echoing input.
- `build_plan(document: RequirementsDocument, context: PlanningContext) -> PlanningSnapshot`:
  pure, deterministic, no IO/network/import/eval/provider call. Canonicalize semantically
  unordered source/evidence/requirement/mapping/case/ref/hint/pack/tag lists before digest.
  Same logical validated input/state gives identical snapshot and stable proposal IDs.
  PLAN- + SHA256 canonical input; PROP- + first20 SHA256 of requirement+kind+hint content.
  Hash includes project, current cases/signatures/review/receipt validity, observed IDs,
  suite state/digest/enabled/packs/tags; excludes proposal review sidecar and wall clock.

Coverage is only SUPPLIED_REQUIREMENTS_ONLY; execution_coverage always NOT_ASSESSED.
Never read run results to invent execution coverage or output percentages. Findings
include explicit confirmed/proposed/missing/unsupported/insufficient/stale/excluded.
Confirmed requires approved requirement with known expectation, valid declared observed
refs, approved mapping whose exact signature matches current approved case with valid
existing receipt. No fuzzy matching or inference from titles/controls/static collection.
Pending requirement/mapping/case gives proposed mapping, never confirmed. Missing case,
signature drift, rejected case or invalid approved receipt gives stale mapping. Unsupported
mapped cases are explicit; no unsupported automation is counted as confirmed automation.
Rejected requirements are excluded with no proposals. Rows may have several states.
Counts label reviewed/mapped/missing/unsupported/uncertain/stale/excluded requirements;
they describe reviewed mappings, not executed coverage or complete application coverage.
Suite CURRENT adapters expose actual pack/tag/enabled metadata. STALE suite is disclosed,
never used to claim reviewed membership; source-case mapping and suite review are separate.

Risk factors exactly: business_criticality = value*4 (max20); user_impact=value*4(max20);
priority Critical15/High12/Medium8/Low4; coverage_gap=15 if no confirmed mapping else0;
observed_functionality=10 if declared nonempty observed refs are all valid else0;
execution_feasibility=10 if a mapped case is supported else0; uncertainty=10 if requirement
pending/expectation absent/unknown observed refs or stale mapping else0. Sum<=100;
High>=70, Medium>=40 elseLow. Reasons expose factors/limitations, not invented measurements.

Proposal kinds positive/negative/boundary/regression/error_handling. Use explicit design
hints where supplied, otherwise one bounded manual review prompt per kind. Only positive
may reuse requirement expected_behavior by default; other outcomes remain unknown unless
explicitly supplied in that kind's hint. Conditions/defaults are review questions, never
invented endpoints/selectors/limits/statuses/auth/business rules. Every proposal stays
MANUAL_REVIEW, with evidence IDs, assumptions and pending status. Stable IDs change when
requirement/hint content changes. Accepted proposals remain recommendations, not test cases.

Framework public service in `autoqa.intelligent_planning_service`:
`IntelligentPlanningService(project, authorization=None)` with
- `analyze(requirements: Path|None=None) -> PlanningSnapshot` read-only: supplied file or
  stored test-cases/requirements-v07.json. Absent inventory fails; no automatic import.
- `import_requirements(path: Path) -> RequirementsDocument`: requires project-bound plan
  authorization before IO/writes; validate all input before writing only the new sidecar.
- `review(plan_id: str, proposal_ids: list[str], decision: accepted|rejected) -> PlanningSnapshot`:
  requires review authorization, uses stored requirements, recomputes current plan and
  rejects unknown/duplicate/empty IDs, bad decisions or stale expected plan ID before writes.
  Stores only `test-cases/planning-review-v07.json` using PlanningReview. Merge decisions
  only within same current plan. Overlay CURRENT review on matching snapshot; stale record
  never carries approvals forward and is disclosed as STALE with proposals pending.
Review uses existing AuthorizationContext review intent; never calls planning.approve,
changes cases/receipts/suite/config/discovery, renders executable code or grants execution.
No second scenario approval system: accepted/rejected is planning disposition only.

Adapter reads bounded, path/link-safe project data through existing storage paths; rejects
oversized/malformed/duplicate current inventories. Bounds: 1000 cases, 2000 workflows,
5000 observed evidence IDs; source JSON max5MB per file, suite/review max1MB; fail explicitly.
External requirements is regular bounded file, reject symlink/junction components; enforce
bound on actual bytes read. Catch malformed input without echoing client text in errors.
Existing cases: signature via planning.case_signature; approved receipt checked via existing
verify_approval_binding; invalid receipt represented false without fabricating a replacement.
Missing discovery/matrix allowed as empty; malformed present data fails. Deduplicate actual
observed IDs; suite validity uses existing validated export_inventory and digest with no writes.

ApplicationEngine additive methods: intelligent_plan(requirements=None),
import_requirements(path), review_plan(plan_id, proposal_ids, decision),
coverage_report(requirements=None). Route through focused service; old methods untouched.
CLI: requirements-import FILE --project P (explicit write); intelligent-plan
[--requirements FILE] --project P (read-only JSON); coverage-report same input options
(read-only JSON scope/summary/findings/context); plan-review PLAN_ID --accept PROP-ID
(repeatable) OR --reject PROP-ID --project P. Reject combined/empty decision modes.
Use print JSON, not Rich markup for untrusted payloads; JSON reports parse as UTF-8.
No new AI request or client code/network execution. Old plan/API/suite/generation/run
interfaces unchanged. New commands use existing handled nonzero error semantics.

## Ownership / acceptance

Lead: shared contracts, D02, docs/examples/version/lock, any shared test/gate adjustments,
integration/full gates, publication, final state. Do not edit specialist-owned paths.
Backend: src/autoqa/qa_planning.py, tests/test_v07_planning.py only.
Framework: src/autoqa/intelligent_planning_service.py, application.py, cli.py,
tests/test_v07_integration.py only.
QA/security: tests/test_v07_adversarial.py only (independent adversarial/reproducibility/
read-only/receipt/mapping/review/size/authorization/compatibility tests from this contract).

A-H acceptance: reviewed UI/API mapping without executed claims; missing requirements;
unsupported/unknown; positive/negative/boundary proposals with sources/assumptions/risk;
review drift never reapproves old cases; invalid/oversized/adversarial inputs fail safely;
V0.6 compatibility and H01/H02 retained; identical inputs give identical logical plans.
Specialists run focused checks when dependencies available and report unavailable checks
honestly. QA may integrate dependency commits into its own worktree after Lead supplies
SHAs, then commit only its assigned test diff. Lead runs full non-browser/frozen/H01/H02,
Ruff/lock/build/install/UI-API standalone gates, links/security inventory and exact-head CI.
Browser acceptance only if actual browser logic changes. Never weaken existing tests.

Contract clarification: existing V0.6 tags may contain spaces and are preserved exactly with bounded Label fields. Source V0.6 suite/pack IDs still obey their original validated syntax; the context DTO does not relax source validation. Source labels are data and remain unmodified.

Provenance correction after integration review: PlanningContext now retains workflow_provenance and evidence_provenance maps for known IDs. Only OBSERVED supports explicitly observed/workflow references and the observed_functionality risk factor. SOURCE/INFERRED/UNKNOWN/VERIFIED_REQUIREMENT remain known references but cannot become observed support; missing provenance is unknown. All provenance participates in plan digest, so drift invalidates planning decisions. Adapter records actual workflow.status/evidence.category; page element IDs are OBSERVED. Conflicting provenance for one evidence ID fails safely; identical repeated evidence IDs may deduplicate. Positive fixtures must explicitly supply real OBSERVED test provenance; independent negative tests retain SOURCE/INFERRED cases.


## H03 semantic binding amendment

PlanningContext adds bounded workflow_fingerprints/evidence_fingerprints maps (2000/
5000 lowercase SHA-256 values). Requirement adds workflow_bindings/evidence_bindings
maps (20 each), with keys restricted to declared workflow_ids/observed_evidence_ids.
Missing bindings preserve parsing but cannot confirm declared observation support.
Current OBSERVED provenance plus exact reviewed semantic bindings are required.
Drifted bindings make active mappings stale; accepting a proposal never updates a
requirement relationship. Fingerprints enter the plan digest and stale prior decisions.
Only hashes are output, with deterministic unordered collections and meaningful workflow
step sequence. Conflicting evidence identities fail; equivalent evidence deduplicates.
[ADR 0005](decisions/0005-reviewed-semantic-observation-bindings.md) specifies the
projection, excluded volatile metadata and unchanged compatibility/trust boundaries.
