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
