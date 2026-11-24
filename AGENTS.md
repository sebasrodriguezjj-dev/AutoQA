# AutoQA engineering instructions

AutoQA is a supervised local professional QA Automation Engineering agent for authorized
engagements. It is not SaaS or multi-tenant. Reliability, maintainability,
reproducibility, security, accurate reporting, compatibility and practical QA value
outrank feature count. Human review is mandatory for sensitive, mutating or uncertain
actions. Product roadmap changes require explicit owner authorization.

## Read before modifying project code

Every agent must first read [product vision](docs/product-vision.md),
[project state](docs/project-state.md), [architecture](docs/architecture.md),
[roadmap](docs/roadmap.md), [release gates](docs/release-gates.md),
[multi-agent workflow](docs/multiagent-workflow.md), [security](docs/security.md),
applicable [decisions](docs/decisions/README.md), and the active milestone's historical
release/design evidence. Inspect impacted modules and tests before changing them.
Project-state text is a dated handoff: the Lead must verify current GitHub branches,
PRs and exact-head CI before treating it as current. Read the local Git state too.

Before work: confirm origin, branch, clean/dirty state and authorization boundaries;
identify the active roadmap milestone; define acceptance criteria and file ownership.
Never discard owner edits. A future milestone in the roadmap is not implementation
authorization. Read the dated project-state handoff for the active objective and explicit
owner authorization, then verify live GitHub state. Do not treat a completed task's
historical restrictions as current instructions or infer permission from a roadmap.
Keep temporary branch/PR/version status in project-state, not in enduring rules.

## Organization and isolation

The Lead owns product alignment, consistent briefings, planning/delegation, architecture
decisions, integration, full gates, GitHub publication and final handoff. Use up to three
specialists: Backend (domain/services/storage/rules), Framework (Playwright/Pytest,
UI/API compiler/exporter/runtime/CLI), QA & Security (independent negative/adversarial
tests, compatibility/evidence/security review). See [role briefs](docs/agents/README.md).

Delegate independent work when useful within the owner's scope. Give every specialist
the same verified context SHA, purpose, release, active goal, invariants, security
limits, ownership, acceptance/tests and definition of done. Every coding specialist
uses an isolated worktree; explicitly set its workdir. Never allow two agents to
modify the same checkout. Freeze ownership before dispatch; shared files belong to
the Lead. Specialists commit locally and deliver SHA, tests/evidence and limitations.
Only the Lead integrates, pushes official branches and creates/updates the one task PR.
No force-push, history rewrite or release-branch deletion.

## During work

Keep scope narrow, preserve historical contracts and evidence, and add genuine regression
tests for behavior changes. Never weaken assertions or suppress failures to turn a gate
green. Do not execute untrusted client code, install inspected repository dependencies
or run arbitrary AI Python. Use approved targets and synthetic data. Recommendations
cannot approve scenarios or mutations. Preserve project-bound intent and separate
scenario/membership review; receipts are unsigned trusted-local integrity, not identity.

Preserve legacy CLI/import/signature/artifact/report formats, read-without-write behavior,
frozen archives/member hashes, explicit missing/unsupported states and standalone export
independence. Do not conflate collection with executed evidence or selected scope with
full regression. Keep dependency/lock changes explicit. Significant architectural changes
need a new ADR with evidence, alternatives, compatibility and owner authorization.

Never commit client workspaces, credentials, auth state, generated frameworks, reports,
screenshots/traces, environments or disposable output. Static client inspection stays
read-only. Respect exact origins/methods/paths, DNS/redirect controls, declared credential
references, protected evidence and trusted single-writer boundaries. There is no OS sandbox,
universal redaction or complete platform guarantee. Keep residual risks visible.

## Before delivery

Run focused tests appropriate to the behavior, then all [mandatory gates](docs/release-gates.md):
Ruff, full non-browser regression, frozen compatibility, lock consistency, build,
installed package/CLI and independent export/collection/execution. Check documentation
links and credential/artifact inventories. Browser/live AI/client acceptance needs the
corresponding authorization and prerequisites; historical results are labeled historical.

Update relevant context, state and decisions at every development/release handoff.
Commit verified work, push the official branch, create/update one PR and inspect all
mandatory CI jobs associated with its exact current HEAD. Record actual executed checkout
and platform scope; never substitute earlier/pending CI. The Lead cannot declare success
unless GitHub reflects the verified implementation or an explicit blocker. When blocked,
publish safe verified work to a draft PR when possible and report the exact blocker.
Roadmap changes, releases and merge/tag actions require explicit owner authorization;
successful gates alone do not grant it. Respect the current owner's task boundary and
leave review PRs unmerged unless their merge is explicitly authorized. Record residual
risks and stop at that boundary. Do not hardcode a current PR, release or temporary
merge prohibition into these permanent instructions.
