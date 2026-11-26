# ADR 0007: Approved maintenance and historical invocation integrity

Date: 2026-11-25. Status: H04/H05 authorized correction, verification pending.
Authority: AUTOQA-AUDIT-20261125-02 / AUD-DEV-20261125-02 and explicit owner remediation
authorization. This does not authorize merge, release, roadmap changes or new features.

## Evidence and alternatives

At audited a265ebf, independent local H04 tests demonstrate amount-other entering
Page Objects/blueprints after amount-new review, collateral changes and managed-path
bypasses. H05 genuine three-row API execution loses rows in controlled copies while
diagnosis still reports health. Original fail-before logs remain local; see the
[checkpoint](../v08-checkpoint.md). Earlier green candidate gates did not cover these gaps.

Free-form revision descriptions, accepting the latest locator, trusting refreshed
manual-source hashes and deriving completeness from result records cannot enforce
reviewed intent. Freezing an old suite receipt would prevent mandatory renewed review.

## H04 decision

An optional typed maintenance_revision SHA-256 reference is present only on newly
maintained cases. None is omitted from serialization, preserving old case bytes and
signature inputs. The existing signature and separately renewed receipt bind the
reference; existing exported validators already hash every present case field.
An independently persisted strict active-case index must agree in both directions
with case references, so losing the reference, index or ledger cannot disable checks.

A strict private project ledger binds the complete accepted proposal, exact pending
case content, semantic/configuration/data context and hashes of expanded trusted
operations. Construct the authorized operation delta from the validated baseline:
replace the target locator only in the target case's mapped methods. Compare every
represented case's current trusted rendering against that delta. A shared locator
must not authorize collateral operations. Ambiguous or multi-case changes remain manual.

Read-only validation runs before scenario approval, suite approval, direct compilation,
legacy generation/run and source-backed standalone execution. It validates ledger
identity, the still-accepted decision, source/manual revision and exact operation hashes.
Review status, approval timestamps and suite receipts are not immutable case content;
the existing current scenario and membership contracts remain separately mandatory.

The private ledger retains absolute baseline/manual paths solely to recheck source
identity at later local boundaries. This is a narrow exception to ADR0006's hash-only
public source projection: paths are not exported, returned by CLI or placed in diagnosis.
The baseline must remain available and unchanged. The ledger is private project output
and must never be committed or published. Runtime exports carry only the case reference
and independently validated generated code; they do not import the ledger or AutoQA.

Full case-content inventory/context binding is conservative: unrelated content/data/
observation changes can require a new proposal or manual handling. This is not general
multi-case iterative maintenance or autonomous repair. Historical exports remain immutable
and independent, and cannot observe later source revocation.

## H05 decision

New executions add bounded diagnostic_scope derived from the validated reviewed manifest
and actual selection before execution. Historical expected IDs/cardinality, signatures,
run/project identity and plan digest contain no fixture values, expectations or secrets.
The historical five-field diagnostic_snapshot remains unchanged. Diagnosis reconciles
the complete scope and operation evidence with recorded outcomes/accounting. Missing
legacy scope remains explicit uncertainty; latest project state never fills historical
gaps. Observed failures remain observations and hypotheses, never confirmed root causes.

## Security, compatibility and verification

No dependencies, inspected-code execution, receipt/signature algorithm rewrites, manifest
refreshes or frozen fixture changes. Records remain unsigned trusted-local integrity,
not authenticated proof; single writer and no sandbox/hostile-race guarantee remain.
Preserve ADR0004/0005/0006, authorization, privacy, network and standalone contracts.

Mandatory evidence: recovered fail-before and fresh pass-after, independently reviewed
negative tests, owned Chromium repair/defect, actual independent parameterized API and
nonparameterized execution, installed-wheel correction checks, full release script and
exact-final-HEAD hosted CI. See the dated checkpoint for actual completion; this ADR is
not a passing test result or an independent audit approval.
