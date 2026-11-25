# V0.8 independent QA and security review

Date: 2026-11-25 (America/Costa_Rica). Assigned QA worktree:
`C:/Users/sebas/Desktop/AutoQA-worktrees/v08-qa`, branch `codex/v08-qa`.
Common briefing: 947bc3922d7452e5e824309f136f869f261495a6.
Stable baseline: 2243611658accb05afc39593ff6d21fd1e4ba369 (annotated v0.7.0).
The QA agent explicitly read `.codex/agents/qa_security.toml`; native delegation was
available, while automatic role loading was not demonstrated. No product-source changes,
push, merge or tag were performed by QA.

## Verified shared-boundary checkpoint

Independent tests initially reproduced **6 failures / 20 passes**:

- An unreadable source subtree was silently omitted by default os.walk error handling.
- Strict locator cardinality accepted boolean True as integer one.
- Credential definitions accepted inline values, missing/remote references and an
  incompatible SYNTHETIC classification.

The Lead corrected those boundaries in 09c96ab45739cc2b0252ba6aefd8d17838bf1c38;
QA cherry-picked that dependency locally and observed all 26 regressions pass.
A further strict-contract check reproduced numeric zero accepted as a Literal False
claim: **2 failures / 2 passes**. This could not produce a true root-cause claim, but
contradicted the strict contract. Lead correction
41ed7d1c258cfb8b26ea65a938f8ced30e9a79d6 rejects non-boolean false flags.

The expanded complete shared-boundary suite now passes **35 tests in 4.58s**. It
includes actual native Windows junction refusal (no skip), input/ancestor confinement,
root substitution, casefold/identity conflicts, duplicate/nonfinite/invalid JSON,
real oversized/file-count bounds, synthetic sensitive-cell/nesting bounds, read-only
snapshots and inert malicious conftest/setup/test source. Timestamp/directory order
changes do not manufacture source revisions. Inspected source is hashed, never executed,
imported, collected or installed. Before/after logs are preserved locally under the QA
worktree's ignored `.test-work/v08-shared-security-*.log` and
`.test-work/v08-literal-flags-before.log`; disposable artifacts are not tracked.

## Pending service and runtime acceptance

Independent service acceptance is drafted in
[test_v08_acceptance.py](../tests/test_v08_acceptance.py), awaiting Backend/Framework
dependency commits. No A-J runtime completion claim is made at this checkpoint.
The tests exercise reusable synthetic data through pending revision, renewed scenario/
suite approval, a fresh AutoQA-absent export, genuine healthy/defect API execution and
historical diagnosis. They also challenge missing credentials, stale file identities,
tampered inventory/proposals, source/case/evidence/root drift, separate review/apply
intent, preserved assertions and inert arbitrary manual Python.

Actual owned Chromium maintenance/reconciliation acceptance is assigned to Framework;
QA will review its executed outcomes separately. Full release/hosted CI remains Lead
work. Synthetic input tests do not prove arbitrary client correctness or a sandbox.
Trusted-local/single-writer/unsigned-record, privacy, retention and platform limitations
remain; the historical V0.5 evidence incident remains unroot-caused.
