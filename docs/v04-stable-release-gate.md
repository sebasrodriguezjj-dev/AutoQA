# AutoQA V0.4.0 stable release gate

Promotion review date: 2026-11-23. Branch: `feat/v04-development`. Existing PR: #2.
Verified candidate: `6a0914f0e4df05e094e4107564bae4262e46b05c` / `0.4.0rc1`.
Retained main/v0.3.0 baseline: `d26f9088f12b369ea222da6ea3c02176f93b7474`.
Target package/import/export version: **0.4.0**.

## Release decision and scope

This gate prepares the existing verified V0.4 implementation for stable release review.
AutoQA remains an internal professional QA Automation Engineering tool supporting its
owner's consulting services. It is not a SaaS product or a certification service for
arbitrary client systems. No V0.5 implementation is part of the promotion.

The supported acceptance scope remains a trusted local operator, Python 3.14 and owned
Windows/Chromium browser applications. Linux PR CI verifies non-browser behavior only.
Complete multi-platform browser validation is not claimed.

Before changes, a fresh fetch confirmed the exact approved candidate HEAD locally and
remotely, a clean tree, the correct origin and no unexpected main divergence. PR #2 was
open, targeted main and was mergeable. Candidate CI run 45225591082 completed successfully
with 205 passed / 17 browser tests deselected. The candidate audit identified no unresolved
release-blocking issue inside its documented scope.

The [0.4.0rc1 candidate audit](v04-release-candidate.md) is preserved unchanged as
historical evidence. This document supersedes its current-version/readiness statements
for the stable promotion; it does not rewrite historical tests or exported artifacts.

## Final functionality

- Deterministic export of a complete standalone Playwright/Pytest project, including
  validated blueprints, per-page Page Objects, checked locator properties, reusable
  operation methods, fixtures, reviewed environment/browser configuration, pinned direct
  dependencies, pytest configuration and setup/execution documentation.
- Compilation of supported explicitly approved heading/navigation and reviewed functional
  scenarios. Unsupported approved cases are reported explicitly; pending/rejected cases
  never become tests. Independent approval receipts remain mandatory for new exports.
- Additive CLI commands: `build-framework DESTINATION --approved --project PATH`,
  `validate-framework DESTINATION` and `run-framework DESTINATION --project PATH`.
  Existing V0.3 commands and behavior are retained.
- Separate navigation/action/assertion records for entered operations, with run/test/step
  identity, status, UTC timestamp, duration, generic error and actual evidence references.
  Every-step/failures-only/disabled screenshots and separate trace controls are retained.
- Standalone integrity validation, collection-first bounded execution, actual JUnit/JSON
  outcomes, run-scoped diagnostics and escaped HTML reports, without AutoQA installed.
  Missing outcomes remain NOT_EXECUTED. A nominal zero subprocess exit with missing,
  failed or error JUnit outcomes returns 3 instead of false success.

For installation, exact CLI usage and export layout, see [README](../README.md),
[CLI reference](cli-reference.md) and [architecture](v04-architecture.md).

## Stable version alignment

Only release metadata, the version assertion and current release documentation change;
no application architecture, runtime algorithm or test expectation is weakened.

| Version surface | Alignment |
| --- | --- |
| pyproject.toml root project | 0.4.0 |
| autoqa.__version__ | 0.4.0 |
| uv.lock root editable project | 0.4.0 |
| Installed distribution metadata | Verified against 0.4.0 during installation smoke |
| Newly exported framework.json | Inherits autoqa.__version__, verified as 0.4.0 |
| Newly exported pyproject.toml | Inherits autoqa.__version__, verified as 0.4.0 |
| Current version-specific regression assertion | 0.4.0; all existing behavioral assertions retained |

A parsed comparison against the approved candidate lock confirms that changing the
root project version back to 0.4.0rc1 makes the lock data identical. All dependency
versions, sources and hashes remain unchanged (37 packages). Historical exports, domain
schema versions and legacy manifest wire versions are not rewritten.

## Validation evidence

Local verification used Python 3.14.3 on Windows. Disposable test/build/install output
uses new ignored `.test-work/v040-stable-*` directories. The exact promoted HEAD and
new hosted CI result are recorded in PR #2 and delivery.

| Check | Actual result |
| --- | --- |
| Non-browser regression, excluding live AI | 205 passed / 17 deselected in 164.87s |
| Focused export/integrity and standalone isolation tests | 2 passed in 51.79s |
| Ruff lint and format | Passed; 52 files already formatted |
| Locked dependency consistency | Passed; 37 packages, unchanged dependency resolutions |
| Wheel and sdist | Built successfully with version 0.4.0 |
| Isolated wheel installation and CLI help | Passed from installed site-packages; import and distribution version 0.4.0 |
| Approved synthetic export from installed wheel | Integrity validation passed; manifest and exported pyproject version 0.4.0 |
| Fresh standalone environment | Declared dependencies installed; AutoQA absent; validation passed; 1 approved test collected |
| Frozen compatibility | Full regression passed; no fixture diff from v0.3.0; archive/member checks retained |
| Tracked files and package inventories | No scoped credential-pattern matches or private/disposable paths in packages |

The exported project intentionally ships dependency declarations without a lockfile;
its fresh environment was installed with `uv sync`, then validated and collected with
its own Python interpreter. The AutoQA repository itself passed its locked check.
No skipped prerequisite is counted as success.

## Preserved browser acceptance

The original independent environment resolved declared dependencies and asserted that
AutoQA was absent. Its collected and executed browser scenarios produced:

| Owned-local execution | Actual outcomes | Operations | Screenshots | Traces |
| --- | --- | ---: | ---: | ---: |
| Healthy | 9 passed | 34 | 34 | 9 |
| Controlled search defect | 7 passed / 2 failed | 32 | 32 | 9 |
| Restored | 9 passed | 34 | 34 | 9 |

The failing cases were the two approved search expectations. Later unentered operations
were absent, not passed. Counts and referenced files were rechecked in this promotion;
the original artifacts remain untouched. Earlier focused tests also verified headed
execution, headless failures-only screenshots and disabled screenshots/traces.

Browser suites are not repeated for this metadata-only promotion. Current generated
framework compilation/validation/independent collection and full non-browser regression
verify version propagation and retained behavior. No external application benchmark,
live AI call or production-client session is used.

## Compatibility and security review

V0.3 is an ancestor of the candidate and promotion. All Batch A/B/C history is retained.
Frozen V0.1/V0.2 archive hashes and their member hashes are verified, with no fixture diff
against v0.3.0. Legacy models, signatures, generated-manifest formats, result/report
readers and commands are unchanged. Legacy generation/execution still records one coarse
scenario step; the newer operation-level evidence applies to exported frameworks.

Project-bound authorization checks remain below CLI interfaces. Generation verifies
current case approval and independently persisted receipt signatures/revisions; no AI
path approves cases. Source-backed run-framework rechecks current approvals. Independent
delivery validates its exported review snapshot and cannot observe later source revocation.

Paths reject traversal and link/junction components, source-project overlap and existing
destinations. Output is validated before publishing a new export directory; unrelated
files are not overwritten. File digests and approval receipts are unsigned local integrity
checks, not tamper-proof records against a writer controlling all inputs. Single-writer,
trusted-filesystem assumptions remain explicit; hostile concurrent replacement is not solved.

AuthorizationContext is caller intent, not authenticated identity or advanced role control.
Subprocess environments are reduced and timeouts bounded, but there is no OS sandbox.
Complete descendant-process cancellation on Windows remains limited. Advanced authentication,
multi-user identity/concurrency and arbitrary untrusted code execution are unsupported.

Step messages omit input values/raw assertion errors, while raw JUnit/logs, screenshots
and traces may still expose application data. Disabling standalone screenshots does not
disable trace images. Sensitivity annotations, automatic redaction and retention controls
remain limited. Operators must review client inputs and artifacts before distribution.

No private project, credential, browser state, generated suite, venv or new run evidence
is staged for Git. Frozen demo archives and historical provenance remain intentional
compatibility evidence. Credential-pattern review is scoped and is not a forensic audit
of every possible secret format or all Git history. Package inventories are inspected to
exclude private workspaces and disposable validation output.

## Deferred V0.5 improvements

1. Unify new operation contracts/results with legacy domain steps while preserving history.
2. Add richer sensitivity metadata, reviewed redaction and artifact retention policies.
3. Add authenticated approval identity, durable revision/revocation history and concurrency
   control before exposing the engine to remote or multiple users.
4. Strengthen process-tree cancellation and actual OS isolation; verify more platforms.
5. Expand owned browser coverage for remaining functional branches and separately evaluate
   authorized hosted/client execution. No universal compatibility guarantee is implied.

## Final release recommendation

Recommend 0.4.0 for stable release **within the documented verified scope**, subject to a
successful CI run on the final promoted PR head and final owner review. No unresolved
release blocker is identified within that scope; residual limitations above remain.

This promotion updates the existing development branch and PR #2 only. It does not
authorize or perform merge, a direct main push, a v0.4.0 tag or a GitHub Release.
Stable package metadata is not a claim that those publication steps already happened.
