# AutoQA product vision

AutoQA is a supervised, professional QA Automation Engineering agent for authorized
client applications and repositories. It is a local engineering tool supporting its
owner's professional services. It is not SaaS, a subscription offering or a
multi-tenant platform. A public source repository never makes client workspaces,
credentials or test evidence public.

This is the permanent product direction, adopted from the owner's foundation
instruction on 2026-11-23 (America/Costa_Rica). It describes the intended complete
workflow; it does not claim that every stage is already automated. The implemented
baseline is V0.6.0, released at `bbd54ad0821cb6962c09d8a1149a0f40b936764b`.
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

These are proposed development milestones, not implemented capabilities, release
promises or authorization to begin. Future roadmap changes require explicit owner
authorization. The foundation delivery stops before V0.7 and leaves its setup PR
unmerged for independent audit. Existing deferred ideas must be evaluated against
this direction rather than silently promoted into a version's scope.

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
