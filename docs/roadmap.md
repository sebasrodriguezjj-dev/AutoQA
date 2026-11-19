# AutoQA roadmap

## V0.3.0 delivered

AutoQA is a private professional QA engineering tool supporting its owner's QA Automation Engineering services. A public source repository does not make client artifacts public. The product direction is a trustworthy local engineering engine, with no SaaS/subscription or billing plan.

- Python 3.14, uv, Typer/Rich, Pydantic, Playwright/Pytest, Jinja2, YAML and local SQLite registry; optional OpenAI recommendations.
- Batch A: versioned domain contracts, legacy projections, local storage boundary and separated report projections. Domain contracts are additive; compatible legacy producers/layouts remain.
- Batch B: project-bound authorization intent, planning/review services and bounded browser/local-repository/hybrid discovery.
- Batch C: persisted approval receipts bound to reviewed scenarios, reusable generation/execution/JUnit services, shared ApplicationEngine/InProcessAdapter and coarse scenario-step evidence.
- Trusted template generation, AST/Ruff checks, collection-first execution, actual JUnit results, headed/headless configuration, screenshot policies, traces, diagnosis and HTML/JSON reporting.
- Finalization: diagnostic lookup includes recorded step screenshots and historical evidence; package/import/lock version is 0.3.0.

See [final delivery](v03-final-delivery.md), [release audit](v03-release-audit.md), [finalization verification](v03-release-finalization.md) and [CLI reference](cli-reference.md). The CLI exposes init, demo, explore, plan, generate, run, diagnose, report and integrate. Integrate only writes a local reviewable GitHub Actions workflow.

## Current limits

AuthorizationContext is caller intent, not authenticated identity or role enforcement. Approval receipts/manifests depend on trusted local writers; they are not signed hostile-filesystem protection. Storage is single-writer and approval updates are not a multi-file transaction. Execution is not an OS sandbox; Windows descendant-process timeout cleanup remains limited.

Evidence wraps each generated scenario in one coarse step rather than individual Playwright actions. Skipped/interrupted step semantics and sensitivity annotations need improvement. Raw logs, JUnit, screenshots and traces may expose client data and require review before sharing. Historical runs have NOT_RECORDED steps.

External functional execution remains unvalidated after the documented dependency-origin block; scope restrictions were retained. Hosted generated CI and live AI provider access remain unverified. Authentication, remote cloning, API test generation, scheduling, self-healing, arbitrary model-generated executable code and multi-user operation are not implemented.

## V0.4 development direction (not implemented)

1. Define richer typed executable step contracts, per-action evidence and explicit missing/skipped/interrupted outcomes.
2. Add sensitivity annotations, artifact redaction/retention policies and reviewable evidence controls.
3. Design authenticated interface adapters with least-privilege project authorization; keep interfaces separate from engine logic.
4. Add revision/concurrency control and durable approval history before multi-user exposure.
5. Strengthen process cancellation and OS isolation, then validate supported execution platforms.
6. Improve stable scenario identities, accessible-name/readiness evidence and multi-page declarative contracts.
7. Design explicit per-origin dependency permissions with DNS/redirect validation before expanding SPA scope; no wildcard permissions.
8. Validate hosted CI, optional live AI and authenticated staging only under explicit authorization and client data policy.

FastAPI, React, MCP and cloud identity are possible future interface concerns, not dependencies or delivered capabilities of V0.3. No V0.4 implementation is part of this release.
