# AutoQA V0.7.0 stable release gate

Release date: 2026-11-25, America/Costa_Rica. Owner authorization explicitly covers
stable metadata promotion, mandatory verification, updating/merging existing PR #7
with a merge commit and annotated v0.7.0 publication at verified official main.
It does not authorize new functionality, V0.8 or the AI Software Factory.

## Approved baseline and promotion boundary

Independent audit approved candidate b3a709cd944779a83beda69e7ec3ca0d94140893,
tree fce7b9133629d68f52fcf4f2f48e7519bca7bfdd, against main
baa776d2253831f08dc7d630cf0e67d0a22d4b8f. RC1 Actions
[45528140141](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45528140141),
job 138916481893, tested synthetic merge 0ea5cd70e622d9c127cb62de19872e9554935fbb,
with that same tree: 505 passed, one expected native-Windows skip, 18 deselected.
The corresponding Windows candidate gate recorded 506 passed / 18 deselected.
These are historical RC1 results, not substitutes for stable verification.

Fresh preflight verified clean Lead feat/v07-development, matching remote candidate/
main and open mergeable [PR #7](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/7).
No pending Git operation; all six specialist worktrees and original dirty copies
preserved. Annotated v0.6.0 object bea83dc984687dcde97416a8fa57bd2849f8aa0f targets
bbd54ad0821cb6962c09d8a1149a0f40b936764b. Earlier tags remain untouched; v0.7.0 was absent.

Only package/import/root-lock metadata and the corresponding framework version
assertion change from 0.7.0rc1 to 0.7.0. Other changes are release/context documentation.
Parsed lock data must be identical after normalizing only the root package version.
No runtime algorithm, schema, signature, receipt, standalone contract, dependency or
frozen compatibility artifact changes. Historical candidate records retain original
versions, results and commit references.

## Delivered functionality and accepted audit corrections

Bounded explicit requirements/source/evidence/mapping JSON, deterministic read-only
planning and supplied-inventory coverage findings, explained risk and manual positive/
negative/boundary/regression/error-handling proposals. Four CLI commands provide
requirements-import, intelligent-plan, coverage-report and plan-review. Only explicit
import/disposition writes new planning sidecars. Acceptance cannot approve executable
scenarios/suites or grant execution authority. No fabricated coverage percentages:
SUPPLIED_REQUIREMENTS_ONLY and execution coverage NOT_ASSESSED.

The independent audit accepted D02's enduring-instructions/dated-state separation,
the original provenance correction (only actual OBSERVED supports declared observations)
and H03's [semantic identity/binding correction](decisions/0005-reviewed-semantic-observation-bindings.md).
Changed meaning cannot inherit review through reused IDs; conflicting observations fail.
Planning disposition never refreshes independent requirement-to-evidence bindings.
Domain 0.3, API 0.5, management 0.6, historical approvals and independent exports remain.
See [guide](v07-intelligent-planning.md), [candidate history](v07-release-candidate.md)
and [architecture](architecture.md). ADR 0004/future professional vision is preserved.

## Mandatory stable verification

Run `uv sync --locked`, `uv run python scripts/verify_release.py --phase all` and
`git diff --check` with failure propagation. Verify stable version, Ruff, full
non-browser regression excluding live AI, frozen compatibility, H01/H02, provenance,
H03, lock, archive inventory, isolated wheel/import/CLI and all four planning commands.
Validate independent framework/COMPLETE collection and genuine case/pack/full execution
with AutoQA absent. Check documentation links, four role TOMLs, credential/artifact
inventory, historical preservation and exact candidate-to-promotion diff scope.

Actual outcomes are recorded below before publication. Any failed/incomplete mandatory
gate blocks merge/tag; previous RC1 success does not certify stable metadata.

### Actual stable promotion results

Complete local release script: **exit 0**, native Windows/Python 3.14.3.
Full non-browser regression: **506 passed / 18 deselected in 197.42s**, no skips or
failures. This includes frozen archive/member hashes, H01/H02, original provenance,
H03 semantic identity and unchanged legacy contracts. Ruff lint and format passed
(75 files). Stable package/import/editable-lock version is 0.7.0.

Parsed dependency data is identical to the audited candidate except root version.
The exact source diff is only __version__; the sole test change is its corresponding
framework-version assertion. Current release/context docs are the remaining changes.
Historical candidate records, frozen fixtures, runtime and prior schemas are untouched.

Wheel/sdist built and passed archive inventory. Isolated site-packages import,
distribution/CLI and export metadata asserted 0.7.0. All four installed planning
commands passed, including read-only analysis, import, snapshot-bound disposition and
stale-review refusal. Independent approved validation and COMPLETE collection passed
with AutoQA absent and zero unsupported/missing/duplicate/unexpected identities.
Genuine case/pack/full executions each exited 0 with one passing invocation and two
actual operation records. Log: `.test-work/v070-stable-release.log`; fresh package
evidence: `.test-work/release-gate-g_ry3h68`.

Documentation destinations, all four role TOMLs, enduring D02 instructions, historical
architecture/state suffixes and protected files pass. Scoped inventory: 164 files plus
frozen ZIP members, no conventional credential/private-output findings; not universal
DLP. Final documentation-only result recording follows runtime verification, with
links/inventory/diff rechecked and fresh exact-final-HEAD CI required before merge.
Actual hosted run/job/checkout and official merge/tag evidence belong in the canonical
PR publication handoff below. Full-gate reuse after merge requires exact tree equality
and integrated version/context/compatibility verification, not an assumed equivalent tree.

## Publication and permanent evidence

Commit and push the verified stable promotion on the existing development branch;
update PR #7. Inspect the exact new HEAD's mandatory hosted job and actual logs,
recording run/job, real checkout and synthetic merge parents/tree. Refresh immediately
before merge and refuse unexpected HEAD/base drift. Merge by merge commit, fetch main,
verify parents/ancestry/tree/version and required integrated-tree checks. Only then
create/push the absent annotated v0.7.0 tag at official main and verify object/type/
peeled target remotely. Preserve all previous tags and branches. No GitHub Release entry.

The authoritative post-publication handoff is [PR #7](https://github.com/sebasrodriguezjj-dev/AutoQA/pull/7)
and the immutable [v0.7.0 tag](https://github.com/sebasrodriguezjj-dev/AutoQA/tree/v0.7.0):
promotion SHA/CI, official merge SHA/tree, tag object and peeled target are recorded
there after verification, avoiding self-referential commit hashes or a follow-up PR.
The actual PR checkout is distinguished from official main; no separate main/tag CI
is claimed unless observed. [Project state](project-state.md) records the release
authorization, delivered scope and this canonical evidence lookup.

## Residual risks and deferred features

Trusted-local operator/filesystem, single writer, unsigned approval/review records,
no OS sandbox/universal secrets or PII redaction, manual retention and limited platform/
browser validation remain. The historical V0.5 intermittent evidence incident remains
unroot-caused; automatic Codex agent profile loading remains unverified. Semantic
hashes cover recorded meaning, not authenticated identity or complete application
behavior, and are not encryption. No new browser/client/live-AI acceptance is claimed.

V0.8 Maintenance, Diagnosis and Reliability is next proposed, subject to separate
owner authorization. Future local UI/repository management/test-data managers/IDE skills/
dashboards retain their approved deferred allocation; none is implemented here.
Stop after verified stable publication for owner-requested final audit ("Audita").
