# AutoQA roadmap

AutoQA is a supervised, professional local QA Automation Engineering agent for
authorized engagements, supporting its owner's services. It is not SaaS or
multi-tenant. Read the [product vision](product-vision.md) for the complete intended
workflow and the [project state](project-state.md) for the current verified handoff.

## Development direction and status

The owner-approved sequence below is enduring product direction. Current implemented
scope, stable release, candidate, active branch/PR, authorization and verification
belong in dated [project state](project-state.md) and version-specific delivery records.
Verify live GitHub before relying on status. A roadmap milestone is not automatic
permission to implement, merge or release. The owner has explicitly initiated V0.7;
V0.8 remains the next milestone after V0.7, without authorizing its implementation.

## Owner-defined future milestones (proposed, not implemented)

| Milestone | Intended objective | Status and authorization boundary |
| --- | --- | --- |
| V0.7 | Intelligent QA Planning and coverage-gap analysis. | Authorized development milestone; current delivery status is recorded in project-state. |
| V0.8 | Maintenance, diagnosis, reliability, reviewed repairs, safe manual-code reconciliation and test-data foundations. | Owner-approved future direction; exact implementation requires separate authorization, with no automatic repair/self-healing claim. |
| V0.9 | QA Operations, local UI, project/developer setup, repository management, test-data UI, VS Code skills, dashboards, history and CI integrations. | Approximate owner-approved allocation; current CLI/artifacts are the baseline, not delivery of these future interfaces. |
| V1.0 | Integrated professional workflow validation for a supervised end-to-end QA Engineering agent. | Owner-approved validation objective; no arbitrary client certification or SaaS conversion. |

Future roadmap changes require explicit owner authorization. Keep every proposed
scope distinguishable from implemented behavior and deferred ideas. Prioritize
reliability, maintainability, reproducibility, security, accurate reporting,
compatibility and practical QA engineering value over feature count. Human review
remains mandatory for sensitive, mutating or uncertain actions.

## Newly approved future requirements and scope boundary

The owner approved the expanded [V1.0 product requirements](product-vision.md) in the
V0.7 resume instruction: local Application Setup and independent guided projects;
environment validation and VS Code Developer Mode; separate read-only-by-default
Application Repository and editable Automation Repository; local Git and optional
explicitly authorized private GitHub operations; application change tracking/impact
analysis; readable stable-ID automation, manual/AI-assisted hybrid IDE workflows,
reviewed manual-code reconciliation and traceable manual-result imports; a privacy-aware
Test Data Manager; the five named quality/coverage/history/stability/readiness dashboards;
and provider-verified VS Code skill installation/configuration/update management.

The repository skills are `test-case-engineer`, `test-data-engineer`, `test-debugger`.
The selected VS Code assistant uses them; no duplicate in-application coding chat.
Provider-specific conventions must be verified before future implementation. Standalone
framework independence, assertion/expected-behavior preservation, secure external secrets
and truthful evidence levels remain mandatory. See
[ADR 0004](decisions/0004-owner-approved-professional-workflow-vision.md).

These are approved future requirements, not delivered V0.7 features. The allocation
above is approximate, and exact later scope needs separate owner authorization.
V0.7 remains bounded Intelligent QA Planning and Coverage Gap Analysis; V0.8 remains
the next milestone, without permission to begin its implementation in this task.

## V0.6.0 stable release scope

Read-only bounded framework analyzer; reviewed suite/pack metadata; stable-ID case,
pack, suite, tag and full execution; independent exported selection; scope/accounting
reports. H01 framework classification and H02 complete collection reconciliation are
verified repairs. See the [stable gate](v06-stable-release-gate.md) for promotion
verification and the unchanged [candidate audit](v06-release-candidate.md) for history.
One managed suite per project initially. No automatic client source refactoring,
universal framework understanding or intelligent coverage-gap analysis is delivered.
Static candidates are not runtime coverage; collection is not execution. Existing
legacy/domain/API schema versions and released exports are not rewritten.

## V0.5.0 retained stable foundation

V0.5.0 provides receipt-bound API contracts and UI/API standalone export, controlled application authentication references, deterministic data, conservative sensitive evidence policy and reusable package/install/export quality gates. See the [stable release gate](v05-stable-release-gate.md) for current evidence and limitations; the [0.5.0rc1 audit](v05-release-candidate.md) remains historical. PR #3 is integrated at 590832c229f9177c20eb4b928f78beac42488523 and annotated v0.5.0 points there; no GitHub Release entry was created.

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

The historical V0.5 intermittent API/evidence/JUnit incident remains unroot-caused.
Deterministic persistence and reconciliation protections do not establish its cause.
Static framework analysis remains heuristic, and independent delivery snapshots
cannot observe later source approval/membership revocation.

AuthorizationContext is caller intent, not authenticated identity or role enforcement. Approval receipts/manifests depend on trusted local writers; they are not signed hostile-filesystem protection. Storage is single-writer and approval updates are not a multi-file transaction. Execution is not an OS sandbox; Windows descendant-process timeout cleanup remains limited.

Legacy generate/run still wraps scenarios in one coarse step. V0.4 exports record entered navigation, actions and assertions separately with skip/interruption status. Unified legacy contracts and richer sensitivity annotations need improvement. Raw logs, JUnit, screenshots and traces may expose client data and require review before sharing. Historical runs have NOT_RECORDED steps.

External functional execution remains unvalidated after the documented dependency-origin block; scope restrictions were retained. Hosted generated CI and live AI provider access remain unverified. V0.5 supports a bounded application-authentication/API subset. Remote cloning, scheduling, self-healing, arbitrary model-generated executable code and multi-user operation remain absent.

## Deferred capabilities and improvement backlog (not implemented in full)

1. Unify the new framework operation blueprint/evidence with historical domain step contracts without changing legacy outcomes.
2. Extend V0.5 summary-only retention with reviewed field-level redaction, richer safe diagnostics and age-based cleanup.
3. Design authenticated interface adapters with least-privilege project authorization; keep interfaces separate from engine logic.
4. Add revision/concurrency control and durable approval history before multi-user exposure.
5. Strengthen process cancellation and OS isolation, then validate supported execution platforms.
6. Improve stable scenario identities, accessible-name/readiness evidence and multi-page declarative contracts.
7. Extend SPA compatibility only through separately reviewed exact resource permissions;
   bounded explicit resource rules and DNS/redirect controls already exist. Broader
   dependency scope is deferred; no wildcard permissions.
8. Validate hosted client-suite execution, optional live AI and authenticated staging
   only under explicit authorization and client data policy. Repository PR code
   verification is already hosted; it is distinct from client-suite certification.

FastAPI, React, MCP and cloud identity are possible future interface concerns, not delivered dependencies or capabilities. V0.6.0 promotion retains the V0.5 baseline within its verified scope; these deferred interface/platform capabilities are not included.

The backlog above is not an automatically approved milestone scope. Preserve the
original version-specific recommendations and acceptance evidence in their release
documents; evaluate future work against the owner-defined milestones and explicit
authorization. No V0.7 feature is included in this foundation delivery.
