# AutoQA roadmap

## V0.5.0rc1 current candidate

The local candidate adds receipt-bound API contracts and UI/API standalone export, controlled application authentication references, deterministic data, conservative sensitive evidence policy and reusable package/install/export quality gates. See [candidate audit](v05-release-candidate.md) for actual evidence and limitations. It is not a stable release or hosted service.

## V0.4.0 retained release scope

V0.4.0 provides the standalone Page Object framework builder, approved-scenario compilation, operation evidence, independent validation/runner/reporting and three additive CLI commands. Preserved local acceptance demonstrates 9 pass / controlled 7 pass + 2 fail / restored 9 pass without AutoQA installed. See the [stable release gate](v04-stable-release-gate.md) for current verification and limitations, and the [0.4.0rc1 candidate audit](v04-release-candidate.md) for historical evidence. PR verification does not certify hosted browser/client execution or mean a GitHub Release was published.

## V0.3.0 retained foundation

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

Legacy generate/run still wraps scenarios in one coarse step. V0.4 exports record entered navigation, actions and assertions separately with skip/interruption status. Unified legacy contracts and richer sensitivity annotations need improvement. Raw logs, JUnit, screenshots and traces may expose client data and require review before sharing. Historical runs have NOT_RECORDED steps.

External functional execution remains unvalidated after the documented dependency-origin block; scope restrictions were retained. Hosted generated CI and live AI provider access remain unverified. V0.5 supports a bounded application-authentication/API subset. Remote cloning, scheduling, self-healing, arbitrary model-generated executable code and multi-user operation remain absent.

## V0.6 opportunities (not implemented)

1. Unify the new framework operation blueprint/evidence with historical domain step contracts without changing legacy outcomes.
2. Extend V0.5 summary-only retention with reviewed field-level redaction, richer safe diagnostics and age-based cleanup.
3. Design authenticated interface adapters with least-privilege project authorization; keep interfaces separate from engine logic.
4. Add revision/concurrency control and durable approval history before multi-user exposure.
5. Strengthen process cancellation and OS isolation, then validate supported execution platforms.
6. Improve stable scenario identities, accessible-name/readiness evidence and multi-page declarative contracts.
7. Design explicit per-origin dependency permissions with DNS/redirect validation before expanding SPA scope; no wildcard permissions.
8. Validate hosted CI, optional live AI and authenticated staging only under explicit authorization and client data policy.

FastAPI, React, MCP and cloud identity are possible future interface concerns, not delivered dependencies or capabilities. V0.4.0 is the retained stable baseline and V0.5.0rc1 remains a local candidate; these deferred interface/platform capabilities are not included.
