# Permanent engineering and release gates

These are the project gates adopted for the multi-agent foundation on 2026-11-23
(America/Costa_Rica). They apply to future authorized work; they do not authorize a
new milestone, client execution, merge or release. Read the permanent context and
[security boundaries](security.md) first. The [V0.6 stable gate](v06-stable-release-gate.md)
is the release-specific evidence record, not a replacement for fresh checks.

## Before modifying anything

The Lead verifies the current repository, origin, local status, branch/worktree map,
remote main, active PR base/head and latest stable annotated tag. Fetch fresh remote
state before trusting any historical handoff. Record the baseline SHA, intended
version, authorized objective, acceptance criteria and non-overlapping ownership.
Do not discard user edits, rewrite history, force-push or delete release branches.
Use one isolated worktree per coding specialist; only the Lead publishes the official
integration branch. Inspect impacted source, tests and compatibility contracts before
planning changes. Sensitive, mutating or uncertain client actions require human review.

## Required local gates

Run from the assigned checkout with Python 3.14 and uv. Stop immediately on a nonzero
exit; later commands must not turn an earlier failure into an overall success.

```powershell
uv sync --locked
uv run python scripts/verify_release.py --phase all
git diff --check
```

The reusable [script](../scripts/verify_release.py) runs these checks with failure
propagation, bounded subprocess timeouts and fresh ignored output directories:

| Gate | What must actually pass |
| --- | --- |
| Version metadata | Root pyproject, Python import, root lock entry and installed editable distribution agree. |
| Ruff | `ruff check src tests scripts` and `ruff format --check src tests scripts`. |
| Lock | `uv lock --check`; unapproved dependency changes are forbidden. |
| Non-browser regression | `python -m pytest tests -m "not browser" --ignore=tests/test_live_ai.py -q`; no failing or unexpectedly skipped test. |
| Frozen compatibility | Regression verifies original V0.1/V0.2 archive and member hashes, signatures, non-mutating reads, CLI/selection/artifact/report contracts. |
| Distribution build | One wheel and one sdist; archive inventory excludes projects, .test-work, .venv, .env and artifacts path components. |
| Isolated installed package | Install built wheel and locked runtime requirements in a new environment; assert site-packages import, matching distribution/import version and CLI help. |
| Approved export | Import synthetic API requirements as pending, explicitly approve scenario and suite membership, export and validate; manifest and exported project versions match package. |
| Standalone independence | Install declared export dependencies; assert AutoQA absent; validate and reconcile real collection. |
| Actual independent execution | Owned-loopback single/pack/all runs each return zero with one passed invocation, two operation records and matching logical-case accounting. |

`--phase checks` and `--phase package` allow the same bounded stages separately.
Both must succeed for release or integration delivery. Run focused regression first
when behavior changes; preserve a failing reproduction before repairing a defect.
Add meaningful negative/adversarial coverage for affected boundaries. Do not weaken
assertions, hide failures, remove security checks or relabel a missing prerequisite
as a pass. Reuse completed gates only when the verified tree is unchanged; document
that equality and any focused integrated-tree checks. Changes after verification
require the affected gates again, and every final published HEAD requires fresh CI.

### Platform and execution scope

The native Windows handle test in
[test_release_reliability.py](../tests/test_release_reliability.py) must execute on
Windows; it intentionally skips on Linux because Windows sharing semantics are
unavailable. That one documented platform skip is expected in Linux CI. Investigate
new/unexpected skips. Do not introduce a skip for an intermittent failure.

Non-browser gates execute synthetic owned-loopback API scenarios, including actual
healthy/defect/restored and missing-auth outcomes. They are not collection-only and
do not require client secrets. Dependency/tool installation may contact registries;
standalone dependencies resolve their own lock from pinned direct declarations.
Cached root wheels do not guarantee offline standalone resolution.

For changed browser behavior, add/run the affected owned Chromium acceptance and
record actual outcomes, capture settings and platform. The historical V0.4 independent
9 PASS / 7 PASS + 2 FAIL / 9 PASS and V0.5/V0.6 authenticated combined acceptance
remain historical evidence unless freshly rerun. Metadata/documentation-only work
need not repeat unrelated browser benchmarks; explicitly state that exclusion.
Linux non-browser success never certifies Linux browser or arbitrary client behavior.
Live AI is excluded from mandatory gates; any authorized opt-in provider check uses
synthetic data and reports its actual outcome separately.

## Compatibility and result integrity review

Preserve the frozen [baseline](../tests/fixtures/compatibility/baseline.json) and
[compatibility record](v03-compatibility-baseline.md). Do not regenerate fixtures to
make a change pass. Preserve public imports/CLI options, entry point, approval
signatures, legacy artifact paths, original schema versions and historical report
fallbacks. Domain 0.3, API 0.5 and management 0.6 contracts coexist. A package version
promotion does not rewrite them or patch already delivered standalone runtimes.

Compare frozen files against the approved baseline with Git as well as hash tests.
For a metadata-only promotion, parse candidate/promoted lock data and verify only
the root package version changes; preserve every dependency source/version/hash.
Keep candidate release audits and original acceptance records intact. Update current
release documentation while labeling historical evidence accurately.

Review [H01/H02 regression coverage](../tests/test_v06_audit_remediation.py),
[management](../tests/test_v06_management.py) and
[accounting](../tests/test_v06_accounting.py) for impacted changes. Static candidates
are not actual collection or coverage. Collection must reconcile the entire selected
inventory, including unsupported, missing, duplicate, foreign and parameter-row
identities, and cannot create passing execution evidence. Reports must distinguish
selected scope from full regression, logical cases from parameter invocations, and
PASSED from failed/error/skipped/not-executed/unsupported outcomes. Missing/foreign/
duplicate/inconsistent or incomplete current-run operation evidence cannot support
success. Preserve real failures even when operation evidence is unavailable.

## Security, artifact and documentation review

These additional checks are Lead obligations; the release script does not perform a
complete tracked-file secret scan, documentation-link audit or GitHub verification.

- Review tracked/new files, the staged diff and actual wheel/sdist contents. Exclude
  private workspaces, real credentials, browser state, generated client frameworks,
  screenshots/traces, fresh run evidence, environments and disposable output.
- Scan tracked text and decompressed intentional fixture members for conventional
  private-key, GitHub/OpenAI-token and AWS-key patterns. Review matches without
  printing credential values. Record scope and findings; this is neither universal
  PII/secret detection nor a forensic audit of all Git history.
- Keep synthetic examples and frozen archives explicitly identified. Historical XML
  or fixture workstation/path provenance is not new client execution evidence.
- Validate new/changed Markdown local destinations. Preserve historical references
  to ignored evidence as historical references; disclose unavailable artifacts rather
  than fabricating them or force-adding private evidence. Check external release/CI
  links against observed GitHub metadata and actual logs.
- Preserve project-bound intent and independent approval receipts, exact API
  origins/methods/paths and mutation review, DNS classification/pinning, redirect
  refusal, HTTPS/owned-loopback limits and environment-only declared credential
  references. Missing credentials fail; no arbitrary client source is executed.
- Keep API/authenticated export summary-only capture and disabled screenshots/traces.
  This is suppression, not universal redaction. Review legacy/unauthenticated UI
  evidence, tags, descriptions and fixtures before any authorized sharing.

Trust assumptions remain explicit: local operator/filesystem, unsigned receipts,
single-writer projects, no OS sandbox or authenticated multi-user identity, limited
Windows descendant-process cleanup and manual retention. Independent exports cannot
observe later source revocation. The historical V0.5 intermittent API/evidence/JUnit
incident remains unroot-caused; deterministic persistence/reconciliation repairs prove
their tested protections, not that historical cause. Record these residual risks at
handoff; do not silently declare them solved after a green run.

## Exact-HEAD GitHub gate

Lead commits verified work, pushes the official branch and creates/updates one PR.
Read current PR head/base and the workflow runs associated with that exact head.
Require the mandatory `AutoQA code verification` job and every required step to
complete successfully, inspect logs for actual regression/package outcomes and
record run/job URLs and SHAs. Pending, cancelled, failed, earlier-head or unrelated
checks do not satisfy the gate. Recheck PR HEAD immediately before any authorized
merge; if HEAD/base changes, verify the resulting tree and relevant fresh checks.

The [current PR workflow](../.github/workflows/autoqa-pr-verification.yml) triggers on
`pull_request`, and checkout has no explicit `ref`. GitHub's PR run therefore checks
out the synthetic PR merge ref. A run associated with exact PR head H is not proof
that checkout SHA equals H. Record the association and checkout SHA separately;
inspect merge parents/tree when claiming integration coverage. The V0.6 promotion
run associated with `530e436777c149164cb14be8fc9c34178ce09d5f` checked out synthetic
merge `f091d87d86afa8aa40543225639de53adbd7a6ed`; the official merge subsequently
became `bbd54ad0821cb6962c09d8a1149a0f40b936764b`. See
[release CI](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45296528515).
No push-to-main or tag-triggered code-verification run exists in this workflow;
do not claim one from the PR result.

Pinned action revisions, read-only contents permissions and checkout without
persisted credentials are retained. No `pull_request_target`, client secrets or
private workspaces belong in PR verification. The separate
[manual demo workflow](../.github/workflows/autoqa-demo-project.yml) requires a
privately provisioned approved project and authorized target; it is not a substitute
for PR code checks and remains unverified for client/hosted execution. Do not dispatch
it or broaden targets merely to obtain green CI.

## Authorized stable publication and fail-stop rule

Stable release authorization must explicitly cover version promotion, merge and tag.
After local gates and exact-head hosted gates pass, the Lead merges with a merge
commit, preserves the complete release history and existing branch, fetches main,
checks expected parents/ancestry/tree/version and performs required integrated-tree
verification. Create an annotated version tag at that verified official main SHA.
Push only the intended tag and verify both remote tag-object SHA/type and peeled
commit target. Never move an existing release tag. Record the official release SHA,
tag object/target, PR and exact verification links in the permanent project handoff.
A GitHub Release entry is separate and was not required for V0.6.0.

Any mandatory failed/incomplete gate blocks release promotion. Preserve evidence and
report the exact blocker; do not begin dependent migrations. A safe verified partial
delivery may be published as one draft PR if technically possible and authorized.
Follow the active owner's delivery boundary recorded in dated project-state and the
current request. Leave review PRs unmerged unless explicitly authorized after their
required audit and exact-head checks. Historical foundation/reconciliation restrictions
are dated evidence, not permanent prohibitions on already authorized merges. Roadmap
changes and releases require explicit owner authorization; stop at each task's boundary.
