# AutoQA product vision

AutoQA is a supervised, professional QA Automation Engineering agent for authorized
client applications and repositories. It is a local engineering tool supporting its
owner's professional services. It is not SaaS, a subscription offering or a
multi-tenant platform. A public source repository never makes client workspaces,
credentials or test evidence public.

This is the permanent product direction, adopted from the owner's foundation
instruction on 2026-11-23 (America/Costa_Rica). It describes the intended complete
workflow; it does not claim that every stage is already automated. Version-specific delivered capabilities are recorded below; stable release and
candidate status belong in the dated project-state handoff.
Current GitHub observations and the next authorized objective belong in
[project state](project-state.md); verify them before relying on this snapshot.

## Intended complete engineering workflow

| Stage | Intended professional outcome | V0.6.0 implementation boundary |
| --- | --- | --- |
| 1. Understand application and requirements | Establish approved scope, expected behavior and available evidence. | Bounded browser/local source/hybrid discovery and reviewed requirement import; readiness and inferred facts do not prove business behavior. |
| 2. Inspect existing automation | Identify framework structure, constraints and maintenance concerns. | Bounded read-only static framework analysis; inspected source is never imported, executed or installed. Static candidates do not prove runtime coverage. |
| 3. Audit or generate the framework | Preserve useful existing automation and propose a maintainable reviewed framework. | Static audit recommendations and independent approved UI/API framework export with Page Objects; no automatic refactoring or replacement of an existing client framework. |
| 4. Propose test cases and coverage | Present grounded cases, priorities and explicit coverage gaps for review. | Evidence-based deterministic proposals, imported behavior/API contracts and optional review-only AI recommendations. Intelligent QA Planning and coverage-gap analysis are future V0.7 work. |
| 5. Organize test suites and packs | Maintain explicit reviewed membership without duplicated tests. | One managed suite per project with multiple packs, tags and stable case IDs; scenario approval and membership approval are separate. |
| 6. Execute individual cases or regression | Run the selected authorized, approved scope reproducibly. | Case/pack/suite/tag/full selection, overlap deduplication, independent Pytest/Playwright UI/API execution and failure on invalid or incomplete scope. |
| 7. Record genuine test evidence | Keep measured outcomes and attributable evidence with reproducible context. | Real JUnit/JSON/HTML, run snapshots and current-run operation reconciliation; collection is not execution, missing records are not passes and protected evidence is restricted. |
| 8. Diagnose failures | Distinguish observed symptoms, likely causes and uncertainty. | Conservative failure classification and run-scoped evidence references; no universal root-cause guarantee. Further diagnosis/reliability work belongs to V0.8. |
| 9. Propose reviewable maintenance | Explain bounded repairs and their risks before changing approved automation. | Existing advice remains review-only. Automated maintenance, self-healing and reviewed repair workflows are deferred to V0.8; no automatic repairs are delivered. |
| 10. Generate professional QA reports | Explain actual scope, outcomes, evidence, unexecuted work and limitations. | Escaped HTML and JSON reports with selected/full scope accounting; application code/requirements coverage is not inferred from observation counts. |

## Human supervision and priorities

Human review remains mandatory for sensitive, mutating or uncertain actions. The
operator establishes authorization, reviews exact targets, contracts, credentials,
fixture data and mutation scope, and approves scenarios before new generation or
execution. Changes to reviewed behavior require renewed approval. Suite approval
cannot approve scenario content. AI advice, static classification, imported
requirements and a successful collection do not grant authorization or establish a
verified outcome.

Prioritize reliability, maintainability, reproducibility, security, accurate
reporting, compatibility and practical QA engineering value. Never optimize for
feature count alone. A bounded truthful result with explicit limitations is more
useful than unsupported coverage or success claims. Preserve actual failures and
historical evidence; never weaken assertions or fabricate approvals, measurements,
root causes or test outcomes to complete a demonstration.

## Established capabilities and their evidence

| Release | Delivered capability | Retained primary evidence |
| --- | --- | --- |
| V0.1-V0.2 | Local CLI, bounded discovery, reviewed declarative functional cases, trusted generation, real execution, diagnosis and reporting. | [Verification](verification.md), [V0.2 guide](v0.2-functional-testing.md), [delivery](v02-delivery.md), [external compatibility review](v021-external-compatibility-review.md). |
| V0.3 | Versioned domain/readers, local storage/reporting boundaries, planning/review services, project-bound intent checks, approval receipts, execution services and ApplicationEngine. | [Final delivery](v03-final-delivery.md), [audit](v03-release-audit.md), [release finalization](v03-release-finalization.md), [frozen compatibility](v03-compatibility-baseline.md). |
| V0.4 | Independent Playwright/Pytest Page Object frameworks, approved compiler/exporter and per-operation standalone evidence. | [Architecture](v04-architecture.md), [candidate audit](v04-release-candidate.md), [stable gate](v04-stable-release-gate.md). |
| V0.5 | Reviewed API automation, supplied application authentication references, deterministic fixtures and protected evidence policies. | [Architecture](v05-architecture.md), [candidate audit](v05-release-candidate.md), [stable gate](v05-stable-release-gate.md). |
| V0.6 | Static framework analysis, reviewed test management, single/pack/suite/tag/full execution and scope-aware reporting, including H01/H02 repairs. | [Architecture](v06-architecture.md), [candidate audit](v06-release-candidate.md), [stable gate](v06-stable-release-gate.md), [analyzer limits](v06-framework-analyzer.md), [management](v06-test-management.md). |

Historical release documents retain their original dates, versions and verification
claims. Their candidate status or old publication restrictions describe that record,
not current GitHub status. New context links to that evidence rather than replacing it.
The engineering multi-agent organization develops AutoQA; it does not imply autonomous
worker agents have been added to AutoQA's runtime.

## Proposed future milestones

The [roadmap](roadmap.md) records the owner-defined sequence: V0.7 Intelligent QA
Planning and coverage-gap analysis; V0.8 maintenance, diagnosis, reliability and
reviewed repairs; V0.9 QA Operations, dashboards, history and CI integrations;
V1.0 a professionally validated supervised end-to-end QA agent.

Milestones describe intended outcomes, not automatic development/release authority or
proof that every capability is implemented. Future roadmap changes require explicit
owner authorization. Consult [project state](project-state.md) and version-specific
acceptance records for the current delivered subset and active authorized objective.
Existing deferred ideas must be evaluated against the enduring product direction.

## V0.7 planning capability

The additive requirements planner accepts bounded supplied JSON, relates explicitly
reviewed requirements to current receipt-bound cases, distinguishes confirmed/proposed/
missing/unsupported/unknown/stale mappings, ranks manual proposals with explainable
risk and supports snapshot-bound planning disposition. It does not prove semantic
correctness of a human mapping or complete application coverage. Analysis is read-only;
only explicit import/review writes new sidecars. Accepted proposals do not approve cases
or suite membership. Execution coverage is NOT_ASSESSED; no percentages are fabricated.
See [planning guide](v07-intelligent-planning.md) for the exact workflow and boundaries.

## Owner-approved V1.0 product requirements (future scope)

The owner approved this expanded direction during the interrupted V0.7 cycle. It is
**private, local-first, code-first, human-supervised, evidence-driven professional QA
Engineering**, not SaaS. Private client projects/data remain private regardless of source
repository visibility. These requirements do not expand V0.7 beyond Intelligent QA
Planning and Coverage Gap Analysis. Later implementation needs separate authorization.

- **Local application/workspace:** one-time Application Setup, multiple independent QA
  projects, guided per-project setup, environment/dependency validation and Developer
  Mode with direct VS Code integration. The current CLI/project registry is a foundation,
  not an implemented guided desktop/UI experience.
- **Repository Management:** independent per-project Application Repository and Automation
  Repository. Client application source is read-only by default; automation source is
  independently editable and version-controlled. Support local Git creation and optional
  explicitly authorized private GitHub publication, branches/commits/diffs/synchronization/
  PRs/CI, application-change tracking and evidence-grounded impact analysis. Never
  automatically modify the client's application repository. Exported frameworks remain
  usable independently of AutoQA. Engineering-agent Git tools are not a delivered product
  Repository Management interface.
- **Professional automation engineering:** readable source with stable case IDs,
  descriptions, useful comments, steps and Page Objects; manual VS Code development,
  requested AI assistance and hybrid UI/IDE workflows. Safely reconcile manually edited
  automation, propose maintenance for review, preserve assertions/expected behavior and
  support traceable imports of manually executed results. Existing integrity guards must
  not be bypassed to simulate this future capability.
- **Test Data Manager:** credentials, documents, datasets and environment-specific
  references; secure secrets outside tracked source; references usable by manually
  authored and generated tests; reusable fixtures, data versioning/relevant change tracking,
  evidence privacy and sensitive-data protection. Current environment credential references
  and deterministic fixtures do not constitute the full future manager.
- **Dashboards:** Quality Overview, Coverage & Traceability, Execution History, Test
  Stability and Release Readiness. Every view must distinguish actual verified results,
  predictions, static mappings and incomplete evidence. Planning mappings are never
  relabeled as executed coverage.
- **VS Code Agent Skills:** three preinstalled repository-level skills named
  `test-case-engineer`, `test-data-engineer` and `test-debugger`, used by the selected coding
  assistant directly in VS Code. AutoQA manages installation/configuration/updates. Verify
  each provider's compatibility and installation conventions before implementation; do
  not build a duplicate coding chat inside AutoQA. V0.7 neither installs these skills
  nor claims cross-provider support.

Approximate allocation: V0.8 maintenance/reliability/manual-code reconciliation/test-data
foundations; V0.9 local UI, project/developer setup, repository management, test-data UI,
VS Code skill installation and dashboards; V1.0 integrated professional workflow
validation. Exact later-version scope remains subject to separate owner authorization.
See [roadmap](roadmap.md) and [ADR 0004](decisions/0004-owner-approved-professional-workflow-vision.md).

## Operating limits that must remain visible

V0.6.0 requires a trusted local operator/filesystem and single-writer storage. Intent
contexts and unsigned approval receipts are not authenticated identities or
hostile-filesystem protection. There is no OS sandbox, complete Windows descendant
cancellation guarantee, universal PII/secret redaction or automatic retention purge.
Independent exports cannot observe later source revocation. API/authenticated exports
restrict persistent capture; unauthenticated UI/legacy logs, screenshots and traces
retain sensitivity risks. Broad client, hosted HTTPS and cross-platform/browser
certification is absent. The historical V0.5 intermittent API/evidence/JUnit incident
remains unroot-caused despite separately tested deterministic protections.

Use approved targets and synthetic data for engineering verification. Never execute
untrusted client code or install inspected repositories merely to discover their
framework. See [security](security.md) for the full boundary and [architecture](architecture.md)
for actual modules and compatibility contracts. No new network permission follows
from this vision or roadmap.
