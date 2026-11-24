# AutoQA V0.6.0 stable release gate

Review date: 2026-11-23 (America/Costa_Rica). Approved candidate:
`6669f3911723cbb73f494196e4312ccdae321980`, PR #4, branch `feat/v06-development`.
Retained main: `590832c229f9177c20eb4b928f78beac42488523` (V0.5.0).

## Baseline and change boundary

Fresh origin fetch confirmed the correct repository, clean working tree, approved
candidate ancestry and mergeable open PR #4. Exact candidate Actions
[45292041685](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45292041685)
completed successfully. Promotion requires fresh exact-promoted-HEAD CI; that earlier
result is baseline evidence only.

Package, import, root editable lock and version assertion change from 0.6.0rc1 to
0.6.0. Framework manifest and exported project metadata derive from `__version__`;
the installed-package acceptance verifies both. No dependency resolution, runtime
algorithm, approval schema or frozen compatibility fixture changes are authorized.
The [candidate audit](v06-release-candidate.md) and all earlier audits remain historical.

## Delivered scope and audit repairs

V0.6 delivers bounded read-only static framework analysis, independently reviewed
suite/pack membership, stable-ID single/pack/suite/tag/full execution and scope-aware
reports. See [architecture](v06-architecture.md), [analysis](v06-framework-analyzer.md)
and [management](v06-test-management.md).

H01 distinguishes ordinary application manifests from actual test declarations,
recognizes Cypress TypeScript configuration and applies default Pytest structure and
directory exclusions without executing inspected code. Static analysis remains
heuristic, partial for uncertain/custom tooling and never proves runtime coverage.
H02 reconciles the entire selected collection, including parameterized identities,
unsupported, missing, duplicate and foreign nodes. Incomplete collection is nonzero;
collection never fabricates operation evidence or PASSED results. Historical exports
require re-export to obtain corrected runtime files. The adjacent manual-case/API-only
export prerequisite fix remains covered by its original regression.

## Mandatory verification and publication

Run `uv sync --locked` then `uv run python scripts/verify_release.py --phase all`.
This enforces version alignment, Ruff lint/format, lock consistency, non-browser
regression excluding live AI, frozen archive/member compatibility, wheel/sdist
inventory, isolated installed import/CLI, approved independent export, AutoQA absence,
validation/collection and actual synthetic owned-loopback single/pack/full execution.
Compare parsed lock packages against the candidate: only the root version may change.
Review tracked/private artifact and conventional credential inventory. Do not weaken
assertions, convert failures to skips or substitute historical browser evidence for
new execution. Record actual local results below before committing.

Push the promoted branch, update existing PR #4 and verify every mandatory job on
its exact HEAD. Only then merge using a merge commit, fetch and verify integrated
main, run integrated-main gates, create annotated `v0.6.0` at that merge SHA, push and
verify both remote annotation and peeled target. Preserve branches and history.
Any mandatory failure stops release and prohibits migration. No GitHub Release entry.
Exact promoted/integrated SHAs and hosted results belong in the PR and permanent
project-state handoff, avoiding a self-referential commit identifier here.

## Reliability and security limits preserved

The historical V0.5 intermittent API/evidence/JUnit incident remains unroot-caused.
Deterministic persistence/reconciliation regressions establish their tested protections,
not that incident's cause. Duplicate/foreign/missing evidence fails conservatively;
real failures remain visible. Trusted filesystem, unsigned receipts, single writer,
no OS sandbox, limited Windows descendant cancellation and manual retention remain.
Independent snapshots cannot observe later source revocation. No universal PII/secret
redaction, arbitrary client certification or complete cross-platform/browser guarantee.
API/authenticated exports use restricted summary evidence; unauthenticated legacy UI
capture retains sensitivity limits. See [security](security.md) and the retained audits.
All current acceptance uses owned synthetic targets; no client data or credentials.

## Local promoted-tree results

The complete release script returned exit 0 on Windows/Python 3.14.3.
Non-browser regression: **305 passed / 18 deselected in 235.66s**; no skips
or unexpected failures. Ruff lint/format passed (67 files); lock consistency
passed (37 packages). Parsed lock data is identical to the approved candidate
after normalizing only the root version. Frozen fixtures and historical audits
are unchanged. Scoped inventory reviewed 129 files plus ZIP members with no
conventional credential/private-output findings.

Wheel/sdist built; installed site-packages import/distribution/CLI asserted 0.6.0.
Approved export metadata asserted 0.6.0. Standalone dependencies installed with
AutoQA absent. Validation and complete collection passed with zero unsupported,
missing, duplicate or unexpected nodes. Case/pack/all execution each returned 0
with one actual invocation and two operations. Disposable log: .test-work/v060-release.log;
package acceptance: .test-work/release-gate-1q18jtuf. No new browser benchmark
or live AI call is claimed. Exact-head hosted CI remains mandatory before merge.
