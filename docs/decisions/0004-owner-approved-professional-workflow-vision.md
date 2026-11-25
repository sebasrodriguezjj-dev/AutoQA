# ADR 0004: owner-approved professional workflow vision and version boundaries

Status: accepted future product requirements, implementation deferred; 2026-11-24.
Authority: the owner's V0.7 interrupted-development resume instruction. This explicit
approval expands future direction, not V0.7 runtime scope or release authority.

## Approved direction

Private, local-first, code-first, human-supervised, evidence-driven professional QA
Engineering; not SaaS. The [product vision](../product-vision.md) records all approved
requirements: local one-time Application Setup, independent guided projects, environment/
dependency validation and VS Code Developer Mode; separate per-project read-only-by-default
Application Repository and editable/versioned Automation Repository; local Git creation,
optional authorized private GitHub publication and branch/commit/diff/sync/PR/CI workflows;
application-change tracking with evidence-grounded impact analysis and no automatic
client-source changes; standalone frameworks independent of AutoQA.

Readable stable-ID/commented/described test source, steps and Page Objects must support
manual VS Code development, requested AI assistance and hybrid UI/IDE workflows. Future
safe manual-code reconciliation and reviewed maintenance preserve assertions/expectations;
manual execution result imports retain traceable provenance. Test Data Manager covers
credentials/documents/datasets/environment references, secure secrets outside tracked
source, shared manually written/generated-test references, fixtures, version/change
tracking, privacy and sensitive evidence protection.

Quality Overview, Coverage & Traceability, Execution History, Test Stability and Release
Readiness dashboards must separate actual verified results from predictions, mappings
and incomplete evidence. Three repository-level skills—test-case-engineer,
test-data-engineer and test-debugger—are used directly by the selected VS Code assistant;
AutoQA manages installation/configuration/updates after provider-specific compatibility
and conventions are verified. Do not add a duplicate coding chat inside AutoQA.

## Allocation and alternatives

Approximate V0.8: maintenance, reliability, manual-code reconciliation, test-data
foundations. Approximate V0.9: local UI, project/developer setup, repository management,
test-data UI, skill installation and dashboards. V1.0 validates the integrated professional
workflow. Exact future implementation scope needs separate owner authorization.

Implementing these concerns inside V0.7 would dilute planning acceptance and introduce
unreviewed source-editing, data/security, provider and UI boundaries. Defer implementation
and retain the explicit future requirements instead. Existing CLI/project registry,
standalone exports, credential references and JSON fixtures are foundations, not proof
that the complete future managers/interfaces/skills exist.

## Consequences and validation

V0.7 remains Intelligent QA Planning and Coverage Gap Analysis. No new UI, repository
manager, data manager, VS Code skill installation, manual-code trust exception or V0.8
repair is implemented by this decision. Existing security/approval/compatibility gates
remain. Future proposals must preserve code-first ownership, read-only application
source, independent automation, external secrets, human review and honest evidence levels.
Provider skill support is explicitly unverified until checked before implementation.
