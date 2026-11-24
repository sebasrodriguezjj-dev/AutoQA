# QA and security pilot review

Review date: 2026-11-23 (America/Costa_Rica). Reviewer: native delegated QA & Security
Agent. Assigned isolated worktree: `C:/Users/sebas/Desktop/AutoQA-worktrees/qa-security`;
branch `codex/pilot-qa-security`; shared briefing commit
`713b6f808bae3156ee7759b16c7a3f24f9631865`.

## Independent assignment and evidence

Read the common [pilot brief](../multiagent-pilot-brief.md), historical Markdown
release/architecture/security/roadmap/verification documents from V0.1 through V0.6,
README, current release script, workflows, package configuration and relevant
compatibility/reliability/H01/H02 test definitions. Existing records were treated as
dated evidence, not current GitHub observations. This specialist did not independently
query live GitHub or rerun product execution; release-state observations came from
the Lead's verified common briefing. The Lead owns final integrated gates and hosted CI.

Owned only [release-gates.md](../release-gates.md) and this review. No product code,
test assertion, fixture, dependency, historical audit or other checkout was modified.
No client code, client target, live provider or manual workflow was executed; no push,
merge or tag was performed by this specialist. Work is one locally committed docs task.

## Findings and disposition

| Review item | Finding and action |
| --- | --- |
| Mandatory gate commands | Script and PR workflow agree on locked install, Ruff, non-browser/live-AI exclusion and package/export gates. Permanent instructions preserve all stages and nonzero failure propagation. |
| Script scope | Package smoke actually runs owned-loopback case/pack/all and checks genuine operation/accounting records. Documentation must not call all package acceptance collection-only. The Lead corrected current CI prose before the pilot. |
| Exact-head semantics | Current pull_request checkout uses a synthetic merge ref. Permanent instructions distinguish exact-head run association from checkout SHA; no push-main/tag CI claim is made. |
| Historical evidence | V0.1/V0.2 archives/members/signatures, legacy reports and release audits remain unchanged. New current rules link to detailed evidence rather than replacing it. |
| H01/H02 | Existing test definitions cover plain app metadata, Pytest conventions/exclusions, mixed tooling and full selected collection reconciliation, including foreign modules. Static analysis/collection is never execution/coverage proof. |
| Reliability risk | The historical V0.5 intermittent incident remains unroot-caused. Windows handle and distinct-identity stress tests do not establish its cause; permanent failure, duplicate JUnit and absent/foreign step evidence remain failures. |
| Browser/platform claims | Linux CI intentionally skips native Windows sharing semantics and excludes browsers. Historical Windows/Chromium evidence stays separately labeled. No Linux-browser or arbitrary-client certification. |
| Security/trust | No sandbox, authenticated multi-user identity, signed receipts, hostile-filesystem isolation or universal redaction is claimed. Snapshot revocation, legacy capture sensitivity and manual retention remain explicit. |
| Current README inconsistency | The retained V0.5 paragraph called V0.6 unmerged candidate despite the stable header. Reported to Lead, who confirmed correction in the integration checkout. Candidate-era CLI labels were also reported for clarification. |
| Checks outside script | Credential/tracked inventory, Markdown destinations, remote state and CI log inspection need explicit Lead checks; they are not automatically provided by the release script. |
| Agent configuration scope | Lead reports native pilot delegation observed, but role TOML is only parsed; automatic role discovery is not certified and installed CLI multi_agent remains false. Instructions must preserve this distinction. |

No new reproduced runtime blocker was established by this bounded document/source
review. That statement is not an independent rerun of release acceptance or a
comprehensive security audit. Final setup success depends on Lead integration,
required local gates and exact published-head GitHub checks.

## Specialist verification and handoff

Validated every relative Markdown destination in both owned files, confirmed only
owned docs changed and ran `git diff --check`. Source references were inspected
against the assigned baseline. The final local commit SHA is delivered to the Lead
outside this file to avoid a self-reference. No conflicting writes or merge conflicts
occurred in this isolated task; Lead integration must independently verify that claim
for the combined pilot. The worktree remains available and clean after commit.
