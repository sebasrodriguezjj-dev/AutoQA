# V0.8 maintenance, diagnosis and reliability guide

V0.8 is a bounded local engineering foundation. It adds structured read-only diagnosis,
potential application impact, synthetic test-data aliases and separately reviewed
declarative locator repairs. It does not execute inspected repositories or provide an
autonomous repair system. See [interfaces](v08-interface-agreement.md),
[threat model](decisions/0006-bounded-maintenance-and-untrusted-source.md),
[checkpoint](v08-checkpoint.md) and [independent review](v08-independent-review.md).

## Recorded diagnosis and application impact

```powershell
uv run autoqa diagnose-run PATH/TO/results.json --project projects/owned
uv run autoqa impact-review before.json after.json --project projects/owned
```

Diagnosis reads bounded local recorded results, historical case identities and selected
invocation/operation evidence. It never substitutes latest cases for missing snapshots.
Raw errors, expected-value contents and capture references are suppressed in the new
report. Symptoms, possible application/automation causes, missing evidence and next
checks remain distinct. Missing failure-operation records, orphan evidence, nonzero
run outcomes and reconciliation defects cannot establish a healthy run or confirmed
application defect. Imported records are unauthenticated claims. No root-cause guarantee.
Existing legacy diagnose/report commands retain their original behavior.

Impact accepts explicitly supplied schema 0.8 ApplicationInventory JSON snapshots, not
arbitrary application source or automatic Git operations. Each object declares ID, kind
(route/control/component/api_contract/validation/workflow), relative source_location,
bounded string semantics, provenance and optional case_ids/requirement_ids/page_objects.
IDs reused with changed meaning are changes, not proof of equivalence. Findings are
potential only; supplied relationships do not establish current V0.7 reviewed bindings.
Unlisted objects/cases and unsupported effects remain unknown. No approval or execution.

## Reusable synthetic data and credential references

Example inventory (project_id must equal the selected project name):

```json
{"schema_version":"0.8","project_id":"owned","definitions":[
  {"alias":"datasets.health","kind":"value","environments":["local"],
   "sensitivity":"SYNTHETIC","values":[{"query":"owned-synthetic"}]},
  {"alias":"users.standard","kind":"credential","environments":["local"],
   "sensitivity":"SECRET_REFERENCE","reference":"AUTOQA_SECRET_STANDARD"}
]}
```

```powershell
uv run autoqa test-data inspect --input data.json --project projects/owned
uv run autoqa test-data import data.json --project projects/owned
uv run autoqa test-data inspect --project projects/owned
uv run autoqa test-data validate datasets.health --environment local --project projects/owned
uv run autoqa test-data bind datasets.health TC-API --environment local --authorized --project projects/owned
```

Import uses explicit plan intent. Bind requires separate maintain and review intent and
creates a pending API case revision, preserving request/expectations/environment and
invalidating the old approval receipt. Renew scenario and independent suite approval
before a fresh trusted export. JSON/CSV datasets use a relative reference and explicit
repeatable `--root DIRECTORY` authorization at import; ambiguous roots, links/junctions,
traversal, changed roots/content and oversized/nonregular files fail. Raw file aliases
can be inventoried/validated but cannot become executable API rows. JSON/CSV or inline
rows obey existing DataFixture limits and synthetic nonsecret validation.

Credential aliases contain only declared AUTOQA_SECRET_* environment-variable names.
Analysis never resolves values or hashes secret values. Credential binding supports
replacement of an existing bearer/cookie token_env only, with pending renewed approval;
basic authentication alias binding is unsupported. Validation means the definition and
current binding are valid, not that a credential exists or execution will succeed.
Missing values fail at the existing authorized execution boundary without exposing them.
There is no vault, arbitrary generator or full Test Data Manager. Previously exported
independent snapshots cannot observe later alias revocation; new binding/maintenance
checks must use the current data identity.

## Locator maintenance and manual reconciliation

Read-only proposal requires a valid managed baseline export, current approved functional
case and an independently observed unique current replacement. locator.json contains
strategy (role/label/placeholder/test_id), value, optional name and actual integer count 1.
Only the current canonical checked candidate is supported. Collection locators,
synchronization/wait changes and other repair kinds remain explicitly manual.

```powershell
uv run autoqa reconcile-source BASELINE MANUAL_COPY --project projects/owned
uv run autoqa maintenance propose BASELINE TC-FUNC-AMOUNT EL-AMOUNT locator.json --manual-source MANUAL_COPY --project projects/owned
# Save the JSON output as proposal.json after reviewing its explicit change.
uv run autoqa maintenance review BASELINE proposal.json --decision accepted --manual-source MANUAL_COPY --project projects/owned
uv run autoqa maintenance apply BASELINE proposal.json --authorized --manual-source MANUAL_COPY --project projects/owned
```

Acceptance writes only the exact proposal decision. Apply separately checks project,
source root/files, current case signature, semantic observations, data/membership and
optional manual revision. It changes the managed project case to a disclosed pending
revision, preserving assertions, actions, expectations and permissions. It never writes
automation source. Existing scenario approval and separate suite membership review remain
mandatory; use `plan --approve`, `suite-propose`/`suite-approve`, then `build-framework
NEW_DESTINATION --approved`. Old receipts cannot authorize the revised case. Never
overwrite manually owned automation; generated output uses fresh trusted templates.

The supported manual subset is exactly one generated Page Object locator-property
literal substitution with all remaining AST and other repository content unchanged,
an explicit blueprint method/case relationship and an independently observed replacement.
Comments/formatting are not executable changes; they do not authorize arbitrary edits.
Changed assertions, imports, dependencies, test data, removed/new/ambiguous/moved source
remain reported and manual unless explicitly supported. Similar names do not establish
identity. Arbitrary Pytest remains independently owned and cannot enter managed execution
by refreshing manifest hashes. Reconciliation never imports, collects or installs source.

## Bounds, authorization and limits

New JSON inputs are at most 1 MB; source revision at most 2000 entries, 1000 files,
5 MB total and 1 MB/file; new CLI JSON output at most 2 MB. Strict DTO bounds may be
tighter. Malformed/duplicate/nonfinite input and conflicting identities fail generically.
UNC/device/URL/drive-relative/alternate-stream paths are rejected before filesystem
access; ancestors are checked before child probes. These are single-writer local
checks, not protection against hostile concurrent path races or an OS sandbox.

Equivalent supported unordered inputs and irrelevant source timestamps do not manufacture
new identity; meaningful changes invalidate review. Source root identity is hash-bound.
Conservative whole-context maintenance binding may require review after unrelated changes.
Suppression is not universal secret/PII redaction; operator classification and safe
artifact sharing/retention remain required. Existing network/DNS/redirect/auth rules,
unsigned receipts, platform limits and the unroot-caused V0.5 incident remain unchanged.
The milestone adds no model dependency, optional AI behavior, UI, repository manager,
VS Code skills, dashboards or V0.9 implementation.
