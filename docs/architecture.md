# Architecture

## V0.2 extensions

The existing modular orchestration is retained. `observation.py` adds passive semantic control discovery and checks locator match counts in Chromium. `functional.py` defines non-executable action/assertion contracts and renders trusted functional templates. `independent_demo.py` provides a separate controlled application; fixture-specific expectations live only in examples/independent_contracts.py, outside the generator.

Planning accepts reviewed requirements through an additive --requirements option, persists approval/rejection, and leaves unknown behavior manual. Workflow inference and requirement evidence remain distinct. Importing a requirement cannot approve a test. Existing V0.1 JSON loads through additive default fields and legacy case-signature compatibility.

Generation validates imports/syntax with AST and Ruff, constrains all actions to checked observed controls, and binds files to scenario signatures. Execution separately collects Pytest tests before running and snapshots cases, planning and discovery. Reports use these snapshots for historical metrics, with compatible fallback for older runs. Discovery-only reports explicitly state NOT_EXECUTED and never create fake execution records.

Scope remains same-origin, GET/HEAD-only, public destinations or explicitly enabled loopback. Configured excluded_paths adds narrower operator-reviewed restrictions, and permitted requests are spaced by request_interval_ms. Rejected request origins/methods are recorded without query strings or credential-bearing URLs. No policy was widened for external acceptance.

The provider remains advisory: structured positive/negative/data/assertion ideas require review and cannot produce executable code or approval. The runner is a controlled subprocess, not an OS sandbox; accepting arbitrary model/client Python remains out of scope.

## Original architecture retained

AutoQA uses one sequential CLI orchestration path and focused Python modules. There are no autonomous worker agents, cloud services or application-code modifications. Typer handles inputs and Rich presents results; domain work lives outside the CLI.

The source package follows a flat modular layout to keep v0.1 navigable. `core.py` defines Pydantic contracts and local persistence. `exploration.py` owns one Chromium page, bounded breadth-first link traversal and semantic observations. `repository.py` reads source without executing it. `planning.py` converts evidence into reviewable cases. `testing.py` renders trusted templates, validates syntax, verifies artifact signatures and launches an isolated Pytest process. `reporting.py` renders actual records through escaped Jinja2 templates. `llm.py` defines a provider protocol and optional OpenAI implementation returning Pydantic recommendations only.

Data flow:

1. Initialize a project with validated configuration, private folders and a SQLite registration.
2. Confirm authorization and scope; persist observed UI pages, screenshot references, navigation edges and workflows. Static source findings remain SOURCE; hybrid path matches remain INFERRED.
3. Create JSON/Markdown cases. Expected results are observed regression baselines or explicitly unknown. Business requirements are never invented.
4. Persist selected approvals. Replanning preserves approval only for byte-equivalent scenario contracts; changed evidence resets it.
5. Generate reviewed heading/navigation templates. The manifest binds generated content to case signatures. Manual or unsupported cases do not become code.
6. Validate signatures and approval state before running. The subprocess uses a fresh browser per test, disables ambient Pytest plugins and restricts inherited environment variables. It is not an OS sandbox.
7. Parse real JUnit outcomes. Missing cases are NOT_EXECUTED. Preserve run-specific logs, screenshots, traces and JSON. Diagnose with uncertainty and render client reports.

SQLite stores only the project registry. Versioned JSON stores evidence, cases, manifests and execution artifacts for portability and future service adapters. No database holds credentials. Project logs use JSON lines. Writes to JSON records use temporary files and replacement; concurrent writers to one project are unsupported.

Future expansion should retain these typed contracts and replace orchestration/storage adapters as needed. An actual sandbox is required before accepting executable AI-generated or client-supplied Python code. Authentication and modifying scenarios require explicit additional design and review.
