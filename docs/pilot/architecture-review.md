# Framework Agent pilot review

Review date: 2026-11-23 (America/Costa_Rica). Role: Framework Agent.
Assigned checkout: `C:/Users/sebas/Desktop/AutoQA-worktrees/architecture`.
Branch: `codex/pilot-architecture`; common briefing/base:
`713b6f808bae3156ee7759b16c7a3f24f9631865`.
Stable baseline supplied by the verified Lead:
`bbd54ad0821cb6962c09d8a1149a0f40b936764b` / V0.6.0.

## Independent task and ownership

This specialist read the common [pilot briefing](../multiagent-pilot-brief.md),
reviewed the V0.1–V0.6 architecture/release/audit/security/roadmap/verification
history and inspected actual application, service, CLI, planning, compiler,
management, runtime, domain/storage and reporting source. Only
`docs/architecture.md` and this review record are owned and changed here.
No product code, dependencies, tests, historical release reports or frozen fixtures
are modified. No client code, browser acceptance, live AI or release command runs.
The specialist does not push; the Lead reviews/integrates the commit centrally.

## Findings reconciled in the current map

| Finding | Evidence and treatment |
| --- | --- |
| Existing architecture.md covered V0.1/V0.2 only | Added the factual V0.6.0 module/dependency map above it; retained the entire original text verbatim under an explicit historical label. |
| A shared engine does not mean every CLI command uses it | [cli.py](../../src/autoqa/cli.py) routes explore/plan/legacy generate/run directly to existing services; diagnosis/report/API planning/build/run-framework use [ApplicationEngine](../../src/autoqa/application.py). Documented both paths and the forwarding InProcessAdapter limit. |
| Service names can overstate extraction | [engine.py](../../src/autoqa/engine.py), [PlanningService](../../src/autoqa/planning_service.py) and [DiscoveryService](../../src/autoqa/discovery_service.py) delegate to existing adapters; JUnitIngestionService is a parser wrapper rather than a dependency injected into every runner. Preserved the [V0.3 audit](../v03-release-audit.md) distinction. |
| Source runtime imports differ from exported independence | [framework._runtime_sources](../../src/autoqa/framework.py) replaces config/security compatibility imports with extracted Config/APIResourceRule and copied Scope source. Delivered runtime independence cannot be inferred from source-directory reexports alone. |
| Several contract versions coexist | Package/export metadata 0.6.0, domain 0.3, API 0.5, management/execution envelope 0.6, framework wire schema v1 and UI/API blueprint 0.4/0.5 remain distinct. No implicit migration. |
| Scenario and membership review are separate | [planning.py](../../src/autoqa/planning.py) binds scenario receipts; [management.py](../../src/autoqa/management.py) adds a digest-bound sidecar. Pack membership cannot grant scenario approval. |
| Collection and execution are different evidence | [runner.reconcile_collection](../../src/autoqa/framework_runtime/runner.py) handles H02 complete selected node reconciliation; execute maps actual JUnit/current-run operations. Collection creates no executed/PASSED outcomes; static inspection proves no runtime coverage. |
| Full and selected scope must remain distinct | [runtime management](../../src/autoqa/framework_runtime/management.py) deduplicates stable IDs and rejects invalid selections; runner labels only all/default FULL_REGRESSION and preserves unsupported/missing/failed scope. |
| Historical reasons need attribution | Linked original V0.3 plan, Batch A/C, V0.4/V0.5/V0.6 designs and audit reproductions instead of inventing retrospective ADRs. |

## Checks, coordination and limitations

Local Markdown destination checks, unchanged original-text suffix verification,
assigned-file ownership and `git diff --check` passed. One initial attempt to write
this review found the untracked empty pilot directory absent in the worktree;
creating the owned document's parent resolved it. No integration conflict or checkout
overlap occurred. The commit SHA is returned to the Lead, avoiding a self-reference.
The Lead owns full integrated quality/package/security gates and exact-head setup CI.

A current README contradiction was reported to the Lead: its V0.5 section still
described V0.6 as an unmerged candidate after stable release. README is outside this
specialist's ownership and was not edited here.

This is factual source inspection, not an independent runtime/security audit. Release
facts/test numbers in the common brief were supplied by the Lead's verified work;
the specialist does not claim to repeat them. The historical V0.5 intermittent
incident remains unroot-caused. Trusted single local writer/filesystem, unsigned
receipts, no OS sandbox, manual retention, incomplete Windows descendant cancellation
and incomplete platform/browser coverage remain. No V0.7 or later feature is added.
