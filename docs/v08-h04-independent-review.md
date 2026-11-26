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

## Post-correction independent verification — 2026-11-25

This dated section supersedes the pending-correction status above without replacing
the fail-before evidence. Source audit AUTOQA-AUDIT-20261125-02 and handoff
AUD-DEV-20261125-02 remain the authority; external re-audit is still pending.

QA executor: the narrowly resumed QA & Security specialist, native Windows/Python3.14.3.
Recovered QA worktree remained at90c7dbe until Lead supplied the production commits.
H04 Lead6625430994d14176ab1bc9521285443a4da157bc was applied locally asa239fba;
H05 specialist49e5f9aa4a232d486e13a1aeb79fb5e0ccdd190a asd2491d7. Only the
checkpoint document conflicted; it had no QA edits and was resolved to the exact Lead
snapshot. Production files were not edited by QA. Lead independently reviews these
source/test/log results and owns final integration, comprehensive gates and publication.

Read-only source review identified two H04 gaps before the final supplied correction:
the accepted disposition was not revalidated, and a missing typed case reference could
disable revision checking. Lead added accepted-decision checks and an independent active
revision index. The private baseline/manual-path retention and conservative whole-context
limits are now explicit in ADR0007; paths never enter exported snapshots or diagnosis.

QA added fourteen controlled post-apply mutations: removed/null reference, missing/changed
active index, missing/changed revision ledger, missing/rejected decision, changed baseline,
persisted config drift with the same cached Project, changed data, missing/ambiguous
locators and contradictory same-ID elements. Each mutation uses one fixture and checks
all seven boundaries (scenario review, membership review, direct compilation, fresh
build, legacy generation, legacy execution and source-backed framework execution).
All98 rejection checks preserve project/source bytes and mtimes after each call, create
no output and cannot reach the fatal subprocess probe. Another test verifies accepted
manual source remains unchanged through apply/export and later manual drift is rejected.

Actual combined command `uv run pytest tests/test_v08_h04.py tests/test_v08_h05.py -q -s`
completed **50 passed in221.95s**, exit0. Log and exit record:
`.test-work/h04-h05-independent-after.log` and `.exit` in this QA worktree.
No test was skipped, deselected or weakened in that command.

Genuine owned Chromium H04 execution produced healthy0/PASSED1, locator-change1/FAILED1,
exact reviewed repair0/PASSED1, and genuine application assertion defect1/FAILED1.
Three locators were actually observed with count1; amount-other was rejected before
scenario approval. The repaired Page Object contains amount-new, never amount-other;
original assertions/expectations, manually inspected source and historical export remain
unchanged. This is measured Windows Chromium evidence, not Linux/browser certification.

The same combined run independently exercised H05's actual AutoQA-absent three-row API
execution and controlled missing-first/middle/final, duplicate/unexpected/mixed identity,
operation, plan, aggregate/accounting/schema, malformed scope and legacy-uncertainty
cases. Actual captured API assertion failures retain symptoms and hypotheses without
claiming root cause. Historical diagnosis remains deterministic after current project/
data changes. An actual AutoQA-absent nonparameterized Chromium execution retains exact
case identity/None cardinality/three operations and healthy diagnosis; legacy copies
remain explicitly uncertain. Source review found no new blocking gap in these corrected
boundaries; records remain unsigned and cannot authenticate arbitrary imported claims.

Native security confirmation `uv run pytest tests/test_v08_security.py -q` completed
**83 passed in4.63s**, exit0, including actual Windows linked-ancestor/junction checks
and lexical prohibited-path rejection before access. No unauthorized remote share was
contacted. Evidence: `.test-work/h04-h05-independent-security.log` and `.exit`.

QG07/QG08 have focused independent pass-after evidence; QG09 still requires the Lead's
complete final integrated release gate and hosted exact-HEAD checks. QG10 executor scope
is recorded above; Lead log review is separate. QG11 external independent re-audit and
QG12 owner promotion authorization remain pending. QA did not push, merge, tag or approve
stable promotion. Historical V0.5 incident remains unroot-caused; trusted local operator/
filesystem, single writer, no OS sandbox and manual evidence privacy/retention remain.
