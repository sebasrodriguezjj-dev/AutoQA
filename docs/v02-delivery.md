# V0.2 delivery inventory

## Code added

- src/autoqa/observation.py: passive semantics and checked locator candidates.
- src/autoqa/functional.py: typed behavior contracts, validation and deterministic templates.
- src/autoqa/independent_demo.py: owned independent Supply Lab application.
- examples/independent_contracts.py: controlled requirements resolved against actual evidence IDs, outside production generation.
- examples/validate_v02.py: reproducible standard-CLI healthy/regression/restored benchmark.
- examples/finalize_reports.py: saved-report rendering and preview generation.
- tests/test_functional.py: real independent-demo discovery/contract/security and defect/restore tests.
- tests/test_contracts.py: contract safety, meaningful assertions, injection-as-data and snapshot/NOT_EXECUTED report tests.
- tests/test_live_ai.py: explicitly opt-in synthetic-evidence live provider test; skipped by default.

## Existing code extended

- core.py: additive backward-compatible models, evidence records, locator metadata, behavior case data, rejected status and safe scope configuration.
- exploration.py: passive enriched controls/workflows/evidence and blocked-request observations.
- planning.py: reviewed contract import, positive/negative manual proposals, retained approvals/rejections, legacy signatures.
- testing.py: functional templates, syntax/Ruff validation, test collection, stable IDs and immutable run snapshots.
- security.py: narrower excluded paths, request spacing and sanitized blocked-origin evidence; no broadened origin/method permissions.
- reporting.py and templates/report.html: actual workflow metrics, defect candidates, snapshot accuracy, linked evidence and explicit no-execution reports.
- llm.py: typed positive/negative/boundary, proposed-data and assertion recommendations, always review-only.
- cli.py: existing commands retained; additive demo variant, plan --requirements and plan --reject.
- __init__.py, pyproject.toml, uv.lock: package version 0.2.0; dependency versions retained.
- .gitignore: additional local test/cache exclusions.
- tests/test_core.py: published-prefix scope exclusion coverage; original tests retained.

## Documentation and evidence

README, architecture, CLI reference, security, roadmap and verification were updated. v0.2-functional-testing.md documents contracts, commands, benchmarks and limits. v02-baseline-tests.xml, v02-functional-tests.xml, v02-internal-tests.xml, v02-benchmarks.json and v02-external-validation.json contain actual verification output/metrics.

The independent report is projects/independent-v02/reports/qa-report.html; generated Python is projects/independent-v02/automation/test_observed.py. Healthy, intentionally failing and restored phases retain their separate run artifacts and report snapshots. The external report is projects/toolshop-v02/reports/qa-report.html and explicitly records NOT_EXECUTED because no reliable functional expectations were established under the enforced scope policy.

The original projects/demo-project report/history and the read-only request attachment were not overwritten. Build artifacts are in dist/. No remote workflow push, live AI request, authenticated action or external form submission was performed.

V0.2's local functional acceptance is verified. External functional generalization remains unvalidated: eight pages were observed, but separate API requests were blocked by existing scope. This delivery does not claim a fully externally validated release.
