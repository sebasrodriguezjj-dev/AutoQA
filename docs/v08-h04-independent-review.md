# Independent H04 maintenance binding review

Date: 2026-11-25 (America/Costa_Rica). Audited baseline:
`a265ebfbd32ea2f4cebc9fde784e7ca324a8012e` (tree
`3d694e3a12f6d9c799e079c1caedea753e27dffd`). Assigned existing QA/security
session resumed only H04 audit remediation in isolated worktree
`C:/Users/sebas/Desktop/AutoQA-worktrees/v08-h04-qa`, branch `codex/v08-h04-qa`.
The QA role TOML, AGENTS, permanent context, V0.8 interface/ADR 0006 and the owner's
H04/H05 instruction were read. Only this review and
[test_v08_h04.py](../tests/test_v08_h04.py) belong to this specialist. Lead owns
production design/integration/publication; H05 has separate independent acceptance.
No earlier worktree, historical evidence, package version or release ref was changed.

## Mandatory fail-before experiment

On the unchanged audited product source, the existing test_v08_framework.prepare/drift
fixture built an approved original framework whose actual Page Object contains
`amount-old`. The maintenance proposal reviewed `amount-new`; explicit application
created the pending revision, preserving the complete original contract/expected value.
Only the observed locator then changed to `amount-other`, retaining the same element
identity and functional behavior. The independent test attempted the normal scenario,
independent suite and fresh compiler paths at each boundary:

- After maintenance apply, before renewed scenario approval.
- After renewed scenario approval, before suite review.
- After renewed suite review, before fresh standalone export.
- Before retained legacy managed generation.
- Before retained legacy managed execution, with subprocess entry replaced by a fatal
  probe so stale execution could not contact any application.

Actual Page Object and `blueprint.json` output contained `amount-other` for all three
standalone boundaries. Actual legacy `automation/test_observed.py` also contained
`amount-other`. The accepted `amount-new` transformation was therefore not preserved
by subsequent approval/compiler boundaries. The original `amount-old` export stayed
byte/mtime-identical. This confirms H04 through generated executable representations;
checking a description or receipt alone would not establish that defect.

The pre-fix evidence log is ignored local
`.test-work/v08-h04-mandatory-before.log`. The mandatory pre-fix run finished **5 failed in 58.54s**. The separate pass-after
results will be appended after their actual execution; no pending check is called green.
The controlled legacy execution probe is a fail-closed boundary test, not actual browser
acceptance. The separately authorized owned Chromium repair/defect acceptance remains
required after the production correction.

## Scope and limitations

This is a synthetic owned fixture with explicit local review/generation/maintenance
intent. No client code, untrusted source or remote application is executed. Existing
assertions, signatures, schemas and frozen fixtures remain intact. Receipts and future
maintenance bindings remain unsigned trusted-local records; no sandbox, identity or
universal redaction claim is made. Independent historical exports cannot observe later
source revocation and remain immutable. The historical V0.5 incident remains unroot-caused.

## Additional audited-source boundary evidence

The shared/unrelated operation experiment produced **3 failed / 1 passed / 5 deselected
in 74.88s**, `.test-work/v08-h04-unrelated-before.log`. The passing control repairs one
case with a disjoint control while both cases share a Page Object. The failures show:

1. A single reviewed repair silently changes another approved case sharing its observed
   element, demonstrated by expanded per-case blueprint operation comparison.
2. Unrelated assertion-locator drift in the same case enters the newly compiled output.
3. Unrelated control-locator drift in another case enters the newly compiled output.

A further managed-boundary run produced **2 failed / 10 deselected in 18.15s**,
`.test-work/v08-h04-managed-bypasses-before.log`. Direct blueprint compilation accepts
`amount-other`, and source-backed FrameworkService.run reaches its subprocess despite
post-approval discovery drift. Both source-backed and legacy execution checks stop with
fatal probes before an application is contacted. These are distinct bypass checks,
not claims of new browser execution. No prior assertion was removed or relaxed.

The owned Chromium H04 test has been drafted to observe all three actual unique locators,
record healthy/controlled locator failure/exact repaired pass/genuine application defect,
and reject the third locator before scenario approval. It will run only after the
Lead supplies the production fix and the static boundary regressions pass. Current
pre-fix failures remain release blockers; no H04 resolution is claimed by this checkpoint.
