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

## Recovered independent service/security acceptance

The previous shared-boundary checkpoint above is retained as historical evidence.
After the original V0.8 QA session became unavailable, the Lead reassigned only its
unfinished review to an existing QA/security session. The same V0.8 worktree, original
dirty acceptance/security tests, prior commits and ignored failure logs were preserved.
No completed team or checkpoint was recreated. Current work remained confined to
`tests/test_v08_security.py`, `tests/test_v08_acceptance.py` and this review.
Lead-owned product fixes were cherry-picked only as test dependencies, not authored
or republished as specialist product changes.

### Reproduced integrity findings and corrections

- Existing actual API acceptance exposed missing failed-operation evidence being
  treated as complete, and stored inventory inspection ignored its recorded metadata
  binding. Original `.test-work/v08-backend-independent-first.log` remains:
  **2 failed / 8 passed / 13 deselected in 53.41s**.
- Independent contradictory-run fixtures demonstrated orphan operation identities,
  nonzero run exit with a passed invocation and failed assertions lacking any failed
  operation could retain unqualified health or complete evidence. Original
  `.test-work/v08-recorded-integrity-before.log` remains:
  **3 failed / 3 passed / 23 deselected in 2.71s**.
- Eight new fail-before probes proved linked ancestors must be rejected before any
  descendant metadata access, across symlink/junction checks and root/bytes/JSON/source
  revision interfaces. They failed before Lead fix
  `78298c8fe8e4b9e165b95f1a0e62fea97c0f1d17`, with log
  `.test-work/v08-ancestor-order-before.log`. They pass unchanged after that dependency.
- An actual owned Windows junction in a data-import path independently reproduced
  `candidate.exists()` probing its descendant before rejection. The target was an owned
  local temporary directory; no remote/network path was accessed. Its failing log is
  `.test-work/v08-data-ancestor-before.log`. The original native junction rejection test
  also executes on Windows without skipping. Lexically remote/device/ambiguous paths
  are challenged with filesystem entry points replaced by fatal probes.
- Lead fix `eae44d830762ab1af21f44780a82a8eb629ebd4b` checks data bindings and path
  ancestors before child lookup, rejects false healthy interpretation of incomplete
  run-level evidence and marks absent failed-operation evidence incomplete. The
  unchanged focused contradiction/inventory/junction regressions then passed:
  **8 passed / 22 deselected in 1.52s**,
  `.test-work/v08-data-diagnosis-integrity-after.log`.

These are reproduced defects with bounded tested corrections. They do not prove the
cause or resolution of the historical V0.5 intermittent API/evidence/JUnit incident,
which remains unroot-caused.

### Independent acceptance scope

QA's executable acceptance uses an owned loopback API, fresh synthetic projects and
an independently installed export that asserts AutoQA absent. It binds reusable data
as a pending case revision, proves old approval cannot authorize it, obtains explicit
scenario and separate membership review, and executes actual healthy and controlled
failed assertions. Diagnosis consumes the recorded run/snapshot/operations, with
suppressed values and no confirmed root cause. Tampered/absent/orphan evidence,
duplicate invocations and later current-case edits cannot rewrite that historical
interpretation. Missing credential execution fails before any HTTP hit.

Additional tests verify explicit potential impact and unaffected cases, equivalent
unordered inventory determinism, authorized unique data roots, changed file identity,
traversal/absolute/remote references, authorization before source reads, metadata
inventory tampering, separate review/apply intent and unchanged assertions/source.
Proposal project/case/evidence/source/locator/identity tampering, accepted-review drift
in source/case/evidence/root/data/membership, and substituted or rejected decision
receipts all fail without applying or silently repairing source. Static proposal and
reconciliation calls are deterministic/read-only with process execution prohibited.
Malicious conftest and changed/new Python remain inert and unsupported.

One new static-inspection test initially used a nonexistent DTO attribute
`baseline_revision`; it was corrected to the frozen `baseline`/`current` contract. The same new test also initially expected `UNCHANGED` instead of the frozen `UNCHANGED_MANAGED` state; only those test spellings changed.
That test-construction error did not require a production change or assertion weakening.
The initial **1 failed / 3 passed / 30 deselected** log remains at
`.test-work/v08-review-deeper-first.log`.

Combined owned acceptance/security execution: **116 passed / 1 failed in 133.30s**. The sole failure was the new static test's state spelling described above, not a product failure; the actual API healthy/defect/missing-credential acceptance and every reproduced product-integrity regression passed. After correcting only that test to the frozen enum, the affected test passed **1 passed / 33 deselected in 6.21s**, with log `.test-work/v08-static-readonly-verified.log`. The combined run is preserved at `.test-work/v08-independent-acceptance-final.log`; it is not relabeled as an all-green run. The unchanged shared security suite separately passed **83 tests in 3.79s**, `.test-work/v08-security-ancestor-verified.log`. Lead must run the corrected integrated complete suite for the final candidate gate.
Ruff lint/format and scoped diff checks are recorded with the verified commit handoff.
The complete integrated regression, package/installed V0.8 commands, frozen/H01-H03,
security inventory and final exact-head hosted CI remain Lead verification obligations.

### Independently reviewed browser evidence

The Lead executed the recovered Framework Chromium harness, reported **23 passed in
184.31s**, and supplied its actual sanitized run summary. QA inspected the test/source
change in `6544172693ff6af2f2fb05340acdcab9107678b4`: it reads the newly created
`results.json` after each integer-returning FrameworkService.run call and checks that
its exit code matches. This corrects test API handling; no product runtime was changed
for that harness correction. Source observers actually check both locator counts as 1.

| Actual owned Chromium phase | Exit | Recorded outcome |
| --- | ---: | --- |
| Healthy original approved locator | 0 | 1 PASSED |
| Controlled locator change, original export | 1 | 1 FAILED |
| Separately applied/reapproved fresh trusted repair | 0 | 1 PASSED |
| Genuine application defect, same repaired assertions | 1 | 1 FAILED |

The supplied record confirms `manual_source_unchanged=true` and
`assertions_preserved=true`. This is independent source/result review of Lead-executed
browser acceptance; QA did not rerun or claim to have executed those browsers. It
supports the bounded locator/manual reconciliation workflow only, not arbitrary
manual Pytest trust, automatic self-healing or general platform/client correctness.
No imported runtime claim becomes authenticated evidence merely by being valid JSON.
Trusted local/single-writer/unsigned records, no OS sandbox or universal redaction,
manual retention and limited platform guarantees remain explicit.
