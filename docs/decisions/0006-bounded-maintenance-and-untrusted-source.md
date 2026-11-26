# ADR 0006: Bounded maintenance and untrusted source trust model

Status: authorized V0.8 implementation design. Date: 2026-11-25 (America/Costa_Rica).
Owner authorization covers diagnosis, reviewed repair/reconciliation, application impact
and data foundations; not new arbitrary execution, merge/tag or V0.9 interfaces.
See [frozen interface and scope](../v08-interface-agreement.md).

## Decision and alternatives

Retain trusted compiler and exact approval/manifest checks. Inspect external source only
as bounded data, compare against a validated managed baseline, and convert the narrow
supported locator edit into a declarative pending case revision. Review is distinct from
application; application is distinct from scenario approval and suite membership. Source,
case, observed semantic evidence, data and proposal digests are checked at every boundary.
Prefer fresh validated exports, never in-place updates of manually owned automation.

Reject arbitrary patch execution, pytest collection/import as inspection, manifest-refresh
trust flags and AST-as-sandbox claims. Static AST equality is only a supported-change
classifier. The edited source itself is never executed. Test-data aliases materialize
synthetic values through existing typed scenarios; credential values stay at the existing
authorized execution boundary. Impact and cause findings remain hypotheses, not proof.

## Threat model

| Threat | Implemented design boundary | Residual/deferred limit |
| --- | --- | --- |
| Malicious source, Python, pytest plugins/conftest/imports/dependencies | Bounded static bytes/AST only; no inspected imports, collection, installs or execution; trusted compiler emits fresh code | Existing explicitly approved generated execution trusts local filesystem/operator; no OS sandbox |
| Prompt injection in source/evidence | Data only, no model or interpreted commands; output concise attributed facts/hypotheses | No universal semantic injection detector; future AI remains separately requested advisory work |
| Unauthorized writes/production execution | Read-only analysis; project-bound explicit plan/review/maintain intent; no execute intent from maintenance; existing exact network/auth constraints | Unsigned local intent is not identity; operator must establish staging scope |
| Links/junctions/traversal/path substitution | Reject links on roots/ancestors/entries and confined relative paths; regular-file/size/count bounds; bind supplied root identity and source hashes | Trusted single writer; no hostile-filesystem race/sandbox guarantee |
| Conflicting identity/stale approvals/tampered proposals | Strict DTOs, duplicate rejection, canonical digests and exact current source/case/evidence/data/decision binding; existing receipts and membership remain independent | Hashes are not authenticated identity; no concurrent multi-user transaction model |
| Assertions removed/skips/waits/changed permissions | Allowlist unique locator substitution only; preserve behavior and actions, no arbitrary synchronization patch; pending revision and renewed approval | Unknown manual source stays unsupported; arbitrary Pytest reconciliation deferred |
| Credentials/client data/raw errors/internal paths | Hash-only roots, generic errors, suppressed run evidence, references only for credentials; no secret resolution during analysis | Not universal PII/secret redaction; manual retention/local privacy still required |
| Sensitive files/data references | Explicit authorized roots, bounded regular files, reject links/traversal and changed fingerprints; no remote fetch/upload | No credential vault or arbitrary data generation; low-entropy secrets must not be stored/hashed as data |
| Shell-command injection | Structured subprocess arguments only for authorized owned tests; source analysis invokes no shell or inspected commands | OS-level isolation deferred |
| Misleading imported evidence | Bind run scope, case/invocation and operation records to historical snapshots; incomplete/inconsistent evidence is not an application defect; imported claims remain unauthenticated | No proof that an arbitrary imported file was truly executed; no confirmed universal root cause |

## Compatibility and verification

Legacy schemas 0.3/0.5/0.6 and planning 0.7 coexist with additive 0.8. Approval signatures,
receipt/manifest integrity, H01/H02 selected-scope accounting, H03 observed semantic bindings,
privacy suppression and independent exports remain. ADR 0004's professional future vision
is preserved; this is a foundation, not UI/repository manager/self-healing delivery.
No dependencies or security tool installs are proposed. Existing scoped reproducible
credential/archive inventory checks are extended to new boundaries and source tests.
Mandatory A-J acceptance includes actual owned UI/API execution, negative/adversarial
security and exact-head CI. Historical V0.5 incident remains unroot-caused absent evidence.
