# V0.8 architecture, interfaces and common specialist briefing

Frozen initial contract: 2026-11-25. Baseline main/tag target
2243611658accb05afc39593ff6d21fd1e4ba369, stable tree
3b48f64a2f9a66b6f1b04269935f5cb91c635c88, annotated v0.7.0 object
4395f8a1b9ab2c8bf870bd17052337b730e08328. Owner authorized one V0.8 candidate PR,
not merge, stable tag, V0.9 or unrelated products. AutoQA remains private/local/code-first/
human-supervised/evidence-driven, not SaaS. All work uses synthetic owned targets.

## Architecture and shared contracts

Lead owns v08_contracts.py/v08_io.py, authorization.py, ApplicationEngine, CLI, release
script/version surfaces and permanent docs. Existing schemas/signatures/receipts/
framework integrity, network/privacy restrictions and frozen evidence are unchanged.
Strict additive schema 0.8 DTOs define diagnostic evidence/hypotheses/reports, source
revisions, maintenance proposal/decision, reconciliation, application inventory/impact,
test-data inventory and validation results. See source for exact field names/bounds.
One JSON input is at most 1 MB; source inventory at most 1000 files / 5 MB, each file
at most 1 MB; structured CLI output is limited to 2 MB. Duplicate keys/nonfinite values,
links/junctions/traversal and conflicting identities fail with payload-free errors.
No changes to older schemas. No dependencies added.

Canonical JSON sorts dictionary keys, not meaningful operation/row/step sequence.
Services sort explicitly unordered collections (IDs, source paths, reference sets),
exclude timestamps/artifact paths where semantically irrelevant and domain-separate
digests. Revision binds the exact supplied root identity plus file paths/content hashes;
changing roots cannot substitute a different repository. Root paths are hash-only.
V0.7 semantic projections and OBSERVED-only reviewed bindings remain intact.

## Frozen service surface and narrow supported scope

Backend owns only v08_diagnosis.py, v08_impact.py, v08_data.py and tests/test_v08_backend.py.

- DiagnosisService(project).analyze(run_path): deterministic DiagnosticReport over
  bounded recorded legacy or standalone run data. Use historical snapshots, selected
  case/invocation identity and ordered operation evidence. Missing/inconsistent evidence
  is not an application failure. Raw errors/secrets/suppressed artifacts never echo.
- ImpactService(project).compare(before, after): compare explicitly supplied typed
  ApplicationInventory snapshots; changes in routes/controls/components/API/validation/
  workflow objects yield only potential impact and explicit unknown scope. Relationships
  are supplied, not guessed by names; actual V0.7 mappings can enrich known IDs safely.
- TestDataService(project, authorization=None).inspect(input_path=None),
  import_inventory(path, authorized_roots=()), validate_alias(alias, environment),
  bind_case(alias, case_id, environment): reusable synthetic API row/value materialization
  through a pending case and existing approval/export workflow. Import needs plan intent;
  bind needs maintain+review, never grants approval. Credential aliases store only an
  environment-variable NAME, never resolve values during analysis. Safe file references
  bind explicitly authorized roots and bounded regular-file hashes. No remote downloads.
  Return typed inventory/validation results or a pending TestCase as appropriate.

Framework owns only v08_maintenance.py, v08_reconciliation.py and
tests/test_v08_framework.py; add one owned acceptance script if useful.

- MaintenanceService(project, authorization=None).propose(source, case_id, element_id,
  locator, manual_source=None) -> MaintenanceProposal. Supported repair is an observed,
  unique declarative functional locator replacement. Synchronization/unsupported kinds
  remain explicitly manual; no arbitrary wait/patch/Python acceptance. Source is an
  existing validated managed export. Bind current case signature, source revision,
  evidence semantic digest, optional data identity and optional inspected manual revision.
- review(source, proposal, decision, manual_source=None) -> MaintenanceDecision needs
  review intent, saves only exact proposal-digest disposition in a V0.8 sidecar.
- apply(source, proposal, manual_source=None) -> pending TestCase needs separate maintain
  AND review intent, exact accepted decision and all current bindings. Preserve assertions,
  expected results, actions, endpoints/auth/scope/enabled state; mark revised case pending
  and change its reviewed revision metadata so old receipts cannot authorize new output.
  Existing scenario reapproval and independent suite approval are still required before
  trusted compiler export to a fresh destination. Never overwrite automation source.
- ReconciliationService(project).inspect(baseline, current) -> ReconciliationReport:
  read-only bounded static comparison against a validated baseline managed export.
  Recognize changed/removed/new/moved candidates only with explicit stable evidence,
  assertion/dependency/data changes and unsupported/integrity states. Narrow reconciliation
  subset: a Page Object locator literal change whose entire remaining AST is identical,
  with exact method/case mapping and independently observed unique replacement. It can
  supply manual_source to the maintenance flow; it never trusts edited Python or updates
  manifest hashes. Unknown or ambiguous edits stay manual and unexecutable as managed code.

QA owns only tests/test_v08_acceptance.py, tests/test_v08_security.py and
docs/v08-independent-review.md, independently exercising frozen interfaces. No product
source edits. After dependency integration Lead provides exact commit/tree for tests.

Shared contract amendments require Lead changes and a written message to all specialists.
Each coding specialist explicitly reads its assigned TOML and this briefing, works only
in its isolated worktree, commits locally, returns SHA/tests/findings/limitations. Only
Lead integrates exactly once and publishes. No worktree deletion or dirty-copy cleanup.
Native delegation is available; automatic profile loading is not demonstrated, so role
instructions are explicitly supplied/read. No invented performance measurements.

## Frozen CLI and ApplicationEngine adapters (Lead-owned)

All output JSON, generic errors exit 1, read-only commands do not write/audit.
Existing commands/options/exit codes remain unchanged.

| Command | Signature |
| --- | --- |
| diagnose-run | RUN_FILE --project PATH |
| impact-review | BEFORE_FILE AFTER_FILE --project PATH |
| test-data inspect | --input FILE (optional) --project PATH |
| test-data import | FILE --root DIRECTORY (repeatable explicit authorization) --project PATH |
| test-data validate | ALIAS --environment NAME --project PATH |
| test-data bind | ALIAS CASE_ID --environment NAME --authorized --project PATH |
| maintenance propose | SOURCE CASE_ID ELEMENT_ID LOCATOR_JSON --manual-source DIRECTORY (optional) --project PATH |
| maintenance review | SOURCE PROPOSAL_JSON --decision accepted/rejected --manual-source DIRECTORY (optional) --project PATH |
| maintenance apply | SOURCE PROPOSAL_JSON --authorized --manual-source DIRECTORY (optional) --project PATH |
| reconcile-source | BASELINE CURRENT --project PATH |

CLI constructs existing project-bound plan/review intent for explicit import/review,
and new maintain intent only with --authorized for apply/bind; never execute intent.
ApplicationEngine delegates to the same services with supplied AuthorizationContext.
No model provider, untrusted collection/import/dependency installation or shell execution.

## Acceptance and definition of done

Owner A-J: actual healthy/defect run diagnosis with snapshots; observed locator proposal,
acceptance without source mutation, separately authorized pending revision/reapproval/
fresh export and actual owned Chromium execution; preserved genuine defect/assertions;
manual Page Object detection plus narrow reconciliation and arbitrary-code rejection;
stale case/evidence/source/data/decision rejection; controlled inventory impact with
unrelated/unknown scope; reusable synthetic data alias consumed by approved API workflow;
missing credentials/unauthorized paths safe; malformed/duplicate/oversized/link/traversal/
malicious input tests; historical compatibility; deterministic equivalent inputs.

Prepare 0.8.0rc1 only after supported acceptance passes. Full non-browser/affected browser,
Ruff/lock/frozen/H01-H03/build/installed V0.8/independent execution/docs/inventory and
exact-final-HEAD hosted CI are mandatory. Incomplete results are not passes. Keep durable
batch/branch/assignments/integration/defects/tests/logs/next-action checkpoints. Publish one
verified PR (draft with explicit blockers if necessary), stop for "Audita al dev".
