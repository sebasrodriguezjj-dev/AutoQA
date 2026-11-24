# AutoQA V0.6 architecture - 0.6.0rc1

AutoQA Agent is a supervised, trusted-local professional QA Automation Engineering
tool supporting its owner's services. It is not SaaS or a multi-tenant service.
Base: annotated v0.5.0 at 590832c229f9177c20eb4b928f78beac42488523.

## Additive implementation

- `analyzer.py`: bounded filesystem/AST inspection without importing project code,
  executing tests, installing dependencies or modifying inspected files. Facts and
  heuristic structure candidates are distinguished from unverified runtime behavior.
- `framework_runtime/management.py`: strict schema 0.6 TestCase, TestPack, TestSuite,
  TestSelection, ExecutionPlan, ExecutionRun and ExecutionResult contracts. These
  coexist with the unchanged historical domain 0.3 and API 0.5 contracts.
- `management.py`: proposal and explicit membership review sidecar. Legacy matrices
  and scenario receipts are not migrated. Membership changes have their own digest
  receipt and full approval snapshot in the project event log. Scenario approval
  cannot be granted through suite review.
- Existing FrameworkService compiles the same receipt-bound UI Page Objects and API
  services. Exports add hashed review/management.json and operation-count metadata.
  Cases belong to multiple packs through IDs; generated test code exists once.
- Existing ApplicationEngine and Typer adapters pass typed selections to the existing
  standalone runner. Standalone execution requires no AutoQA installation.
- Runner selects exact generated Pytest node IDs through argument lists, collects,
  executes and reconciles JUnit with current-run operation evidence. No shell input,
  arbitrary node ID or selection expression is accepted. Reports extend existing
  JSON/escaped HTML with selected scope and logical-case accounting.

## Review and execution boundaries

One project currently has one managed suite with a configurable stable suite ID and
multiple packs. Operator-reviewed tags/priority/enabled state are metadata; scenario
content, type and approval must still match the source matrix and scenario receipts.
Default export without a membership sidecar derives an approved-enabled inventory
from existing scenario review; it invents no pack classification. Custom membership
requires suite-approve. Source-backed execution rejects stale membership snapshots.
Standalone exports cannot observe later source revocation.

Selection is sorted, deterministic and deduplicated. All/suite scope is approved and
enabled inventory, including approved unsupported cases; unsupported scope cannot
silently disappear from a successful full regression. Explicit disabled/pending,
unknown or empty selections fail before target requests. Historical exports without
management metadata use a read-only adapter over their approved manifest cases;
old generated runtime files are not rewritten.

Each run directory retains the selection snapshot/digest, project/suite/pack IDs,
selected case IDs, UTC timestamps, result/evidence references and counts. Logical
case counts are separate from parameter-row invocation records. Overall status is
non-success for missing, ambiguous, unsupported, skipped or failing selected scope.
The V0.5 duplicate/foreign-run/persistence safeguards remain; new exports additionally
check the complete expected operation count against their reviewed blueprint.

No arbitrary client source refactoring, repository execution, framework replacement,
remote service, OS sandbox, authenticated approval identity or concurrent writer
support is introduced. See [security](security.md), [analyzer](v06-framework-analyzer.md),
[test management](v06-test-management.md) and [candidate audit](v06-release-candidate.md).
