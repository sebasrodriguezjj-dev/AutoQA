# Verification record

## V0.2 verification — November 18, 2026

The unchanged V0.1 baseline was rerun before implementation: **40 passed in 27.55 seconds**. The initial sandboxed attempt encountered Pytest temporary-directory permission errors; the approved baseline run succeeded. No application tests were disabled or weakened.

Final V0.2 regression execution: **55 passed, 1 skipped in 79.85 seconds**. The skipped test is the explicitly opt-in live-AI test; an environment key alone does not opt in. Full JUnit: v02-internal-tests.xml. Earlier checkpoints include 36 non-browser passes and an independent integration pass/fail/restore run. A generated import-order problem was caught by Ruff and fixed in the generator before acceptance. New coverage includes checked locators, contract/evidence/action validation, injection-as-data, sensitive controls, option evidence, approval/rejection persistence, historical snapshot reporting, pre-execution collection, safe exclusions and NOT_EXECUTED reports.

The independent acceptance harness used the **standard CLI**, with its own local HTTP application and reviewed fixture requirements. It discovered **5 pages, 12 workflows, 42 semantic elements and 23 interactive controls**. It proposed 31 cases, approved/generated/executed 9 (eight functional contracts and one product-identity navigation case), and retained 22 pending cases. The known fixture contains five supported functional workflow types and all five were identified as potential workflows; this is a type-level discovery measure, not requirements coverage.

| Stage | Run ID | Actual results | Duration |
| --- | --- | --- | --- |
| Healthy | 20261118T203606-8eca579b | 9 PASSED | 19.093 s |
| Search regression | 20261118T203633-db46a44e | 7 PASSED, 2 FAILED | 28.412 s |
| Restored | 20261118T203708-a3d2e1aa | 9 PASSED | 15.884 s |

The two failures were TC-F-search-found and TC-F-search-empty. Reports classify their search mismatch as application-defect candidates with low confidence, preserve actual errors/evidence and require human review. Restoring the fixture restored both tests without changing generated code or assertions. No generated locator edits were required. Eight authored fixture contracts were reviewed as valid; precision of all proposed scenarios is not measured. Raw runs, collection logs, traces, screenshots and report snapshots remain under projects/independent-v02/artifacts. The benchmark is v02-benchmarks.json.

External validation used practicesoftwaretesting.com after local verification. Its published robots.txt was reviewed: root allowed, /account, /admin, /auth and /checkout excluded. Those prefixes were configured as narrower scope restrictions. The standard explore command used **max 8 pages, depth 2, one page, 500 ms request spacing**. Actual output: **8 pages, 24 workflow records, 401 semantic elements and 203 interactive-control observations across pages**. These counts include repeated menus/controls, not unique application features.

The unchanged policy blocked 38 request observations to api.practicesoftwaretesting.com, as well as external analytics and other restricted requests. Discovery recorded controls but no reliable product/search expected outcomes. All **22 proposed cases stayed pending/manual**; **0 approved, 0 generated, 0 executed**. The generation command refused to create unapproved tests. No authentication, contact submission, checkout, purchase or access-control bypass occurred. Same-origin/query/method restrictions were not relaxed. This establishes a safe external attempt and a real generalization limitation; it does **not** validate three external functional tests. See v02-external-validation.json and projects/toolshop-v02/reports/qa-report.html, which explicitly says NOT_EXECUTED.

AI tests used mocked responses. The optional live test requires AUTOQA_LIVE_AI=1 plus an explicit model/key; it was not opted in, and no live provider success is claimed. Dependency releases remain those locked for V0.1; only the local package version changed to 0.2.0. `uv lock --offline` and `uv sync --locked --offline` succeeded using the existing cache.

Final report/scope/contract checks after visual refinement: **37 passed in 0.79 seconds**. Ruff lint and format checks passed. `uv build --offline` produced autoqa_agent-0.2.0-py3-none-any.whl and autoqa_agent-0.2.0.tar.gz. Archive inspection verified the functional module/report template and exclusion of projects/, .test-work/ and private .env artifacts. Both client reports were rendered in Chromium and visually inspected; all 31 local-report links and all 11 external-report links resolved to existing files. Previews are saved under each project's artifacts/report-preview-v02.png. The V0.1 report referenced in the request remains preserved.

See v0.2-functional-testing.md for exact commands, schema, benchmark definitions and remaining limits. The V0.1 record below is retained unchanged as historical verification.

## V0.1 historical record

Verified locally on Windows with Python 3.14.3 on November 17, 2026 (America/Costa_Rica). Machine-generated execution timestamps and artifact IDs use UTC, which is November 18 during the evening local verification session.

## Environment

The workspace was initially empty. Python 3.14.3, 3.11 and 3.10 were available; the preferred 3.14 baseline was selected. uv 0.13.9 was installed. Stable packages were resolved from the registry and locked in uv.lock. Public PyPI release pages were checked for [Playwright](https://pypi.org/project/playwright/), [Pytest](https://pypi.org/project/pytest/) and [Typer](https://pypi.org/project/typer/). No prerelease selection was enabled.

Resolved and imported versions are recorded in versions.json. Imports passed for Playwright, Pytest, pytest-playwright, Typer, Rich, Pydantic, PyYAML, Jinja2 and the optional OpenAI SDK. Chromium 159.0.8154.6 (revision 1255) was downloaded and launched successfully. The SDK's installed Responses.parse signature was inspected to confirm structured-output support; no live provider call was made.

## Internal tests

Latest full execution:

```text
python -m uv run pytest --junitxml=docs/internal-test-results.xml -q
40 passed in 19.15s
```

The JUnit file is real test output. Tests cover initialization, project isolation, invalid/reserved names, config validation/round trips, project selection, authorization, URL scope, encoded sensitive routes, private DNS results, semantic UI discovery, page/depth bounds, workflow extraction, matrices, approvals, preservation of modified files, generation, JUnit parsing, report escaping, source inspection, source-only planning, hybrid correlation, mocked AI requests/refusals/evidence validation and CI generation.

Four tests launch real Chromium against an owned local HTTP server. They verify the complete four-test generated suite, an intentionally changed heading that produces a real failed generated test, blocked POST/cross-origin redirect behavior, and crawl bounds. The deliberate regression is asserted as a failure by its enclosing integration test. No expected assertion was weakened.

An earlier unit-test run exposed missing imports; these were corrected before the passing full run. Ruff formatting initially changed saved generated demo files; integrity checks refused them. They were preserved under projects/demo-project/artifacts/formatter-backup, project artifacts were excluded from Ruff, and a fresh suite was generated and executed successfully.

## Actual CLI acceptance demonstration

The following commands were exercised against the included app at http://127.0.0.1:8000:

- init demo-project
- explore --url ... --authorized --allow-localhost
- plan and selected plan --approve flags
- generate --approved
- run
- diagnose
- report --format html and report --format json
- explore --repo src/autoqa --url ... --authorized --allow-localhost
- integrate --provider github

Final hybrid observations: **5 pages, 7 workflows, 24 visible elements, 0 discovery errors**. Static inspection: **14 source files, 3 route candidates, 3 inferred path matches**. Planning produced **27 cases**, including 2 manual form/search review cases. Five scenarios were reviewed and approved:

| ID | Scenario | Actual result |
| --- | --- | --- |
| TC-001 | Homepage heading | PASSED |
| TC-003 | Catalog navigation | PASSED |
| TC-006 | Catalog heading | PASSED |
| TC-010 | Atlas Notebook detail navigation | PASSED |
| TC-013 | Contact heading | PASSED |

Final run: `20261118T011118-3241d176`, **5 passed, 0 failed, 0 skipped, 0 errors, 0 not executed**, Pytest exit 0, measured runner duration **5.848 seconds**. Raw JUnit, JSON, pytest.log, five screenshots and five traces remain in that run's artifact directory. Diagnosis reported no failures for that run.

The rendered HTML was opened in Chromium and its full-page screenshot visually inspected. It includes measured metrics, case outcomes, workflow/approval counts, limitations and deliverable links. The screenshot is saved at projects/demo-project/artifacts/report-preview.png.

## CI and limits of verification

The local workflow is .github/workflows/autoqa-demo-project.yml. Official release tags and immutable commits were resolved through GitHub's releases/latest and commits/tag APIs; action-revisions.json records the results. Sources: [checkout releases](https://github.com/actions/checkout/releases), [setup-uv releases](https://github.com/astral-sh/setup-uv/releases), [upload-artifact releases](https://github.com/actions/upload-artifact/releases).

Workflow YAML, triggers, permissions and local generation were tested. No workflow was pushed or run on GitHub. No cloud credentials were supplied, and no live AI response is claimed. Advanced auth, maintenance, remote repositories, arbitrary AI code generation and business-rule automation remain incomplete as listed in roadmap.md.

See README.md for copy-paste PowerShell instructions and all working commands. This record establishes the local MVP acceptance flow; it does not claim the full future roadmap is complete.

Final packaging checks also passed: `uv sync --locked`, CLI help, Ruff lint, Ruff format check, and `uv build`. Both wheel and source distribution were produced in dist/. Archive inspection confirmed that the wheel includes the Jinja2 template and the source distribution contains no projects/ artifacts or private environment file. The generated on-disk workflow YAML was independently parsed and its triggers/permissions checked.
