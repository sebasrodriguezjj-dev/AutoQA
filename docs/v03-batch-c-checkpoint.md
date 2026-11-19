# AutoQA V0.3 Batch C checkpoint

## Stage 6.0 — approval integrity hardening

Completed on `feat/v03-batch-c` from the verified Batch B HEAD `e55b824`.

- New approvals persist independently in `test-cases/approval-receipts.json`.
- Each receipt binds the case ID, current scenario signature and reviewed case revision,
  with approval time, source and status fields.
- Generation and new-suite execution verify the receipt before proceeding. Changed,
  missing, malformed or mismatched receipts require explicit reapproval.
- New manifests identify `approval_binding: required`; historical V0.1/V0.2 manifests
  remain readable and executable under their existing manifest checks.
- Legacy approved cases without receipts are not silently trusted for new generation;
  the compatibility policy is explicit reapproval before first generation.
- Receipts are local integrity records, not tamper resistance against an attacker with
  write access to both case and receipt files. Authentication and cloud identity remain
  out of scope.

Verification: 69 focused non-browser tests passed, 4 browser cases deselected; Ruff
check and format verification passed.

## Next

Stage 6.1 will extract generation, validation, collection, execution, JUnit ingestion,
diagnostics and run persistence behind reusable services while preserving the existing
CLI and generated-suite formats.

## Stage 6.1/6.2 — execution and evidence

Reusable `GenerationService`, `ExecutionService` and `JUnitIngestionService` now sit
below the CLI and planning service. The existing `testing` functions remain compatible
facades and retain manifest, collection, subprocess and JUnit semantics.

New generated runs support headless/headed configuration, bounded slow motion, trace
capture and `every_step`, `failures_only` or `disabled` screenshot policies. The generated
fixture records structured step metadata and separates evidence-capture errors from the
scenario assertion outcome. Legacy run snapshots remain unchanged and expose no invented
step history.

Verification: the complete non-browser regression passed with 173 tests and 13 browser
cases deselected. Owned real Chromium headless vertical and failure/report slices passed
with step-result assertions. Ruff check and format verification passed.

## Stage 7 — shared application engine

`ApplicationEngine` and `InProcessAdapter` expose project context, discovery,
planning/review, generation, execution, diagnostics and reporting without importing CLI
presentation code. CLI generation, execution, diagnosis and reporting now delegate to
the same application services. Authorization, approval receipts, manifest checks and
scope validation remain below the interface boundary.

Verification: 175 non-browser tests passed and 13 browser cases were deselected; Ruff
check, format verification and diff checks passed.
