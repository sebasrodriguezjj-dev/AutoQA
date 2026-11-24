# Foundation pilot briefing

Verified on 2026-11-23, America/Costa_Rica. Every pilot specialist receives this same
committed context and the owner's foundation-only authorization. This brief is a
historical pilot snapshot; later work starts with fresh GitHub verification.

## Product and objective

AutoQA is a supervised professional local QA Automation Engineering agent for authorized
client applications/repositories. It is not SaaS or multi-tenant. Reliability,
maintainability, reproducibility, security, accurate reporting, compatibility and
practical engineering value take priority over feature count. Sensitive, mutating or
uncertain actions require human review. No V0.7 implementation is authorized.

## Verified release and boundaries

Official V0.6.0 main/tag target: `bbd54ad0821cb6962c09d8a1149a0f40b936764b`.
Annotated tag object: `bea83dc984687dcde97416a8fa57bd2849f8aa0f`.
PR #4 merged with parents V0.5 main and promoted `530e436777c149164cb14be8fc9c34178ce09d5f`.
[Exact release-head CI](https://github.com/sebasrodriguezjj-dev/AutoQA/actions/runs/45296528515)
passed all steps: Linux/Python 3.14.4, 304 passed / 1 expected Windows-only skip /
18 deselected in 41.93s; installed package/export/independent execution passed.
Local full gates: Windows/Python 3.14.3, 305 passed / 18 deselected in 235.66s;
Ruff 67 files, lock 37 packages, build/install/export/independent collection and
single/pack/full execution passed. Integrated main: identical verified tree, correct
parents, version and remote refs, plus 92 focused passes in 37.91s.

H01 classification and H02 complete collection reconciliation are verified repairs.
Preserve the unroot-caused historical V0.5 intermittent incident. Trusted local writer,
unsigned receipts, no OS sandbox, limited Windows descendant cleanup, manual retention,
no universal secret/PII redaction and incomplete cross-platform browser coverage remain.
Frozen V0.1/V0.2 fixtures, legacy CLI/import/signature/artifact/report contracts,
domain 0.3, API 0.5 and management 0.6 schemas coexist; do not migrate them implicitly.
Independent exports cannot observe later source revocation. Never execute client code.

## Historical reading and factual discipline

Before writing summaries, read every existing docs/*.md release, architecture, security,
roadmap and verification document covering V0.1 through V0.6, plus README and impacted
source/tests. Retain all historical evidence; newer factual context must link to it,
not erase it. Read new permanent context files if present. Do not invent historical
motivations: cite the original design or label a current decision as newly adopted.
V0.3 delivered domain/review/execution/report/evidence boundaries; V0.4 independent
Page Objects; V0.5 reviewed API/auth/deterministic fixtures/protected evidence;
V0.6 static inspection, reviewed management and scope-aware execution/reporting.
Future owner-defined milestones: V0.7 Intelligent QA Planning/coverage gaps; V0.8
maintenance/diagnosis/reliability/reviewed repairs; V0.9 QA Operations/dashboards/
history/CI integration; V1.0 professionally validated supervised end-to-end QA agent.
Roadmap changes require explicit owner authorization. A milestone is not permission
to implement it. Next action after this delivery is owner-triggered independent audit.

## Ownership and definition of done

Lead owns root checkout, AGENTS.md, project-state, workflow, decisions, role definitions,
integration and all GitHub publication. Specialists use their assigned absolute worktree,
never root checkout, and never push. No two agents write one checkout. Specialist owns
only its assigned files, commits them locally and returns SHA, factual source references,
verification and limitations. Lead inspects commits before central integration.

Backend/product reviewer: docs/product-vision.md, docs/roadmap.md and
 docs/pilot/product-review.md only.
Framework reviewer: docs/architecture.md and docs/pilot/architecture-review.md only.
QA/security reviewer: docs/release-gates.md and docs/pilot/qa-security-review.md only.

For this documentation-only pilot, validate local Markdown destinations and factual
claims; do not add product code, dependencies or tests. Record review findings, source
references and unverified claims. Lead runs Ruff, full non-browser regression, frozen
compatibility, lock, package, links and scoped inventory gates on the integrated setup.
One setup PR, exact-head successful CI, remain unmerged; no V0.7 or history rewrite.
