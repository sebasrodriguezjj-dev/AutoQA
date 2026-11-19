# Roadmap and remaining work

## V0.2 current status

Local acceptance is verified: semantic functional controls, reviewed behavior contracts, positive/negative/boundary tests, retained approvals, behavioral assertions, independent-demo pass/fail/restore, richer diagnostics and snapshot reports. External discovery was attempted under unchanged security rules; its required API origin was blocked, so external functional execution remains unvalidated. This is a scope/generalization limitation, not a successful external test result. See v0.2-functional-testing.md and v02-external-validation.json.

The next development priorities are:

1. Design explicit per-origin read-only dependency scope, with separate navigation/resource permissions, validated DNS/pinning and redirect tests. Never add a wildcard origin or widen methods merely for one site.
2. Add passive readiness evidence, better empty/error-state association and accessible-name computation for complex SPAs. Distinguish UI completeness from successful HTTP navigation.
3. Improve stable scenario identities and deduplicate persistent menus without sacrificing page-specific behavior. Avoid stale exact expectations on shared mutable external data.
4. Add multi-page declarative contracts and reviewable assertions for dynamic result properties. Retain the prohibition on unknown outcomes and arbitrary code.
5. Strengthen process-tree cancellation and actual OS isolation before accepting untrusted executable code; Windows timeout cleanup remains limited.
6. Verify opt-in live AI only with configured provider/model and explicit authorization; then plan authenticated staging support using least-privilege accounts.

The original V0.1 roadmap below is historical context. Its search/form contract step has now been delivered for supported controlled workflows; advanced capabilities remain deferred.

## Historical V0.1 roadmap

## Verified foundation and vertical slice

- Python 3.14 package, uv lock, Typer/Rich CLI, isolated workspaces and owned local demo.
- Bounded read-only UI discovery with semantic observations, relationships and screenshots.
- Evidence-grounded test matrix, selected persisted approvals, trusted Python heading/navigation templates.
- Real execution, JUnit/JSON outcomes, traces/screenshots, conservative diagnosis and escaped reports.
- Bounded local repository inspection; manual source cases and inferred hybrid path matching.
- Local CI workflow generation with verified official action revisions and syntax tests. Hosted CI remains unverified.
- Optional official OpenAI SDK adapter with structured output validation, mocked tests and review-only recommendations. Live API access remains unverified.

## Exact next implementation step

Add an explicit reviewed scenario contract for the included demo's product search and required/email form validation. Define test inputs and expected results with the QA engineer, render semantic-locator templates, and add real browser pass/failure tests. Preserve the prohibition on automatically submitting arbitrary discovered forms. This extends meaningful coverage beyond heading and navigation regressions.

## Next phases

1. Enforce and test robust browser/process cancellation and network containment across Windows and Linux.
2. Add authenticated staging sessions using limited test accounts, secret redaction and uncommitted storage state; implement auth configure only once it works.
3. Expand framework-aware static analysis, deduplication and stable scenario identities; source path matching is currently heuristic.
4. Exercise generated CI in an explicitly authorized QA repository, including fail paths and artifacts.
5. Validate optional AI with a user-configured model/key and client data policy. Improve diagnostics while keeping claims uncertain and code execution restricted.
6. Design actual OS sandboxing before accepting any executable model-generated or client-authored test code.
7. Add reviewable maintenance proposals and audit trails; never weaken assertions automatically.
8. Later: authorized GitHub access, API testing, scheduled execution, SaaS/web dashboard, organizations, integrations and billing.

Not implemented: remote cloning, arbitrary remote repositories, active authentication, self-healing, maintenance command, scheduler, AI code execution/generation, API tests, business-requirements coverage measurement, full accessibility snapshots, advanced component/dataflow analysis, source test-coverage measurement, multi-user locking or hosted deployment. No placeholder commands are exposed for these capabilities.
