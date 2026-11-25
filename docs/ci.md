# GitHub Actions integration

## AutoQA code verification

[PR verification](../.github/workflows/autoqa-pr-verification.yml) runs on pull requests
with Python 3.14, `uv sync --locked`, Ruff lint/format checks and the non-browser
regression. It explicitly ignores `tests/test_live_ai.py`. It does not install Chromium,
execute client suites, use external application targets or read client secrets.
Dependency/tool downloads require network access; regression uses synthetic data and
disposable local projects. Every command must succeed; test failures fail the job.

Retained V0.4 non-browser coverage includes blueprint/approval/export integrity, CLI, step policies,
diagnostics and an independent export installation/validation/collection smoke test.
The latter installs its declared pinned dependencies using normal registry resolution,
asserts AutoQA is not installed in the export environment and does not launch a browser.
The locked root install's cached wheels do not guarantee offline resolver metadata on a
fresh runner. Registry/dependency failures fail explicitly. Browser acceptance remains
separate owned-local evidence; Linux non-browser CI does not certify Linux browser
behavior or production client execution.

```powershell
uv sync --locked
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run python -m pytest tests -m "not browser" --ignore=tests/test_live_ai.py -q
```

## V0.5 reusable gates

`uv run python scripts/verify_release.py` runs metadata, Ruff, lock consistency,
non-browser regression, build, isolated installed-wheel CLI, approved export and
standalone dependency installation/validation/collection. `--phase checks` and
`--phase package` run the two bounded stages separately. Paths are derived from
the checkout; outputs use a fresh ignored `.test-work/release-gate-*` directory.
Any failed subprocess exits nonzero. No browser, external application or live AI
is contacted by the package stage. V0.6 additionally executes single/pack/full selections
against its owned synthetic loopback API and checks actual outcomes and operations.

The PR workflow also runs the package stage. V0.5 API regression starts owned
loopback servers with synthetic data/credentials, including healthy/defect/restored
and missing-auth outcomes. It never requires client secrets or a private workspace.
The authorized V0.5 engineering review publishes the candidate branch and one PR.
Exact-head hosted results are recorded in that PR and its delivery report; pending
runs do not count as success. The native Windows sharing-handle test is expected to
skip on Linux, while the remaining non-browser suite must pass. Dependency registry
access remains required.

## Manual project execution

`autoqa integrate --provider github --project projects/NAME` writes a manual-only
`.github/workflows/autoqa-NAME.yml`. It requires a generated suite, root `pyproject.toml`
and `uv.lock`, validates a repository-relative project path and refuses to overwrite an
existing workflow. It never commits or pushes. The generator and checked-in demo workflow
use only `workflow_dispatch`; they do not run on PRs.

The demo workflow is not runnable from this public repository's checkout alone:
`projects/demo-project` is deliberately ignored and absent from GitHub runners, and an
authorized target URL must be configured. The earlier PR failure came from these missing
execution prerequisites; it did not establish a core-engine regression.

Before dispatching in a controlled QA environment:

1. Review the scenario expectations, approval receipts and generated Python suite.
2. Provision the selected project on the runner through a separately reviewed private
   mechanism before its preflight step. This repository does not implement provisioning.
   Required files include config, discovery workflow map, test matrix, generated manifest
   and Python suite. New receipt-bound manifests also require the matching approval
   receipt store. Preserve the project layout and integrity records; never fabricate
   approvals, force-add a private workspace or commit client evidence here.
3. Set repository Actions variable `AUTOQA_BASE_URL` to the authorized reachable target
   origin. Configure its exact hostname in `allowed_domains`; observed paths must match.
   Public staging uses `allow_localhost: false`. The workflow neither deploys nor starts
   an application. A localhost demo requires explicit server startup/readiness on the
   same runner and matching loopback configuration.
4. Configure runner Python 3.14 and review all scope rules. Advanced authentication is
   unsupported. Do not introduce client secrets into PR jobs. Future private provisioning
   needs its own reviewed access controls before use.
5. Review reports, traces and screenshots before sharing; the manual workflow attempts
   reporting/upload even on failure and retains artifacts for seven days.

Preflight explicitly fails on empty target URL or missing project files. Generation and
execution continue to enforce approvals and manifest integrity; no missing prerequisite
or failing test is converted to success. A manual dispatch without private provisioning
is expected to fail, and should not be used as the codebase's PR check. A new manual-only
workflow is dispatchable in GitHub once present on the default branch.

Actions retain immutable revisions recorded in [action revisions](action-revisions.json),
read-only contents permissions and checkout without persisted credentials. Hosted manual
client execution remains unverified; PR code verification is reported separately.

## V0.7 installed planning acceptance

The reusable package phase also exercises all four new commands from the isolated
installed wheel: read-only intelligent plan/coverage, explicit requirements import,
snapshot-bound planning acceptance and nonzero stale-review refusal. It checks unchanged
existing case/receipt/suite files and NOT_ASSESSED execution coverage. Existing independent
UI collection and owned API case/pack/full execution gates remain; no browser/provider/
client target is added. Every failed assertion/command remains fatal. The exact-head
PR result and actual synthetic merge checkout are recorded in the delivery handoff.
