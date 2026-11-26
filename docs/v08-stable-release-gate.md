# AutoQA V0.8.0 stable release gate

Date: 2026-11-25, America/Costa_Rica.
Owner explicitly authorizes metadata promotion, full release gates, merge commit of
existing PR #8 and annotated v0.8.0 at verified official main; no V0.9/Factory/UI work.
Audit AUTOQA-AUDIT-20261125-05 / AUD-DEV-20261125-05: TECHNICAL PASS.
QG01–11 favorable; QG12 satisfied by explicit owner authorization.

## Baseline and scope

Approved RC1 commit11ccaf85883ab7c1546e1c5c98ea89e887cb7e32, tree
340ffe52d5b0489005bedb59dda1c37e24ad2513. Stable main2243611658accb05afc39593ff6d21fd1e4ba369;
v0.7.0 annotated object4395f8a1b9ab2c8bf870bd17052337b730e08328. Preflight verified
clean Lead, exact open/mergeable PR8 head/base, no pending operations, no v0.8.0 tag,
all existing worktrees and dirty historical copies preserved.

Only pyproject.toml, src/autoqa/__init__.py, uv.lock root package version and the
corresponding tests/test_framework.py version assertion change to0.8.0. Parsed lock
data is identical after normalizing only root version. No runtime algorithm, security,
interface, signature, schema, dependency, timeout, skip or frozen artifact changes.
Historical candidate evidence remains unchanged. Current release/context docs are additive.

## Verification

Fresh Windows/Python3.14 verification: uv sync --locked;
uv run python scripts/verify_release.py --phase all; git diff --check.
Fresh full stable gate PASS, exit0:729passed/21browser deselected575.61s, no skips/failures,
native Windows/Python3.14.3. Ruff92files, locked37packages, frozen/H01-H05/native sharing/
security, wheel/sdist, isolated site-packages/import/distribution/CLI0.8.0, installed
V0.7/V0.8, AutoQA-absent COMPLETE collection and real case/pack/all plus three-row alias
requests/assertions passed. Log .test-work/v080-stable-release.log/.exit0; package root
release-gate-fv8jddh8. No timeout/skip/assertion changes. Links203, roles4, inventory192
files/16ZIPmembers passed, no conventional credential/private-output findings (not DLP).
Parsed dependency lock unchanged except root version; historical/protected files intact.
Final documentation recording follows verified runtime; new exact-HEAD CI remains required.

Log .test-work/v080-stable-release.log and corresponding .exit preserve actual completion.
Required scope: Ruff, full non-browser/frozen/H01-H05/native Windows sharing/security,
lock/build/archive inventory, isolated installed stable package/CLI, V0.7/V0.8 workflows,
AutoQA-absent COMPLETE collection and genuine case/pack/all and three-row alias execution.

Reused accepted candidate evidence only for unchanged implementation/tests: internal QA
50passed, native security83passed and actual Chromium healthyPASS/locatorFAIL/exactrepairPASS/
genuine-defectFAIL. External auditor accepted this under audit05. Evidence bundle
DEV-AUD-QG10-BUNDLE-20261125-01, AutoQA-V08-QG10-Evidence.zip SHA256
b44898a80d83a0cb2276768d3fc0bd1dc4df05189f9ac4290101b48e902f1a1b remains outside Git.
This is historical accepted browser evidence, not a new stable browser execution.
See [candidate record](v08-release-candidate.md), [remediation handoff](v08-remediation-handoff.md)
and [independent evidence](v08-h04-independent-review.md).

## Publication record

Authoritative final promotion HEAD, exact-HEAD hosted run/job/logs/actual checkout and
parents/tree, official merge and annotated tag object/target are recorded after actual
verification in [PR8](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/8) and the
[v0.8.0 tag](https://github.com/sebasrodriguezjj-dev/AutoQA/tree/v0.8.0).
This avoids self-referential commit hashes or an unnecessary follow-up PR.
No separate main/tag CI is claimed. Merge/tag require successful new exact-HEAD CI,
unchanged expected base/head and official integrated/tested-tree equality.

Trusted local filesystem/operator, unsigned records, single writer, no OS sandbox or
universal secret/PII detection, manual retention, conservative maintenance context and
limited platforms remain. Baseline/manual directories must stay available; exported
historical snapshots cannot observe later revocation. V0.5 incident remains unroot-caused.
No GitHub Release/PyPI publication or new development milestone is authorized.
Stop after stable publication for final independent release audit.
