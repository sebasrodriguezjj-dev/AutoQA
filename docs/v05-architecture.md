# AutoQA V0.5 architecture — 0.5.0rc1

## Verified baseline and contract checkpoint

Development starts at the official annotated v0.4.0 target
`41b940642c389bb426cd6fb836178a99453f4792`, with clean main and unchanged
frozen V0.1/V0.2 archive/member fixtures. No existing V0.5 branch or user edits
were present. Development is local on `feat/v05-development`.

The V0.4 framework builder, ApplicationEngine, project storage, manual review
and independent approval receipts remain the integration boundaries. The legacy
V0.3 domain contracts and serialized fixtures are not migrated.

V0.5 declarative API contracts live in `framework_runtime/contracts.py`, copied
verbatim into standalone exports. `TestCase.kind=api` binds the complete contract
to existing receipt signatures, including environment origins, request/mutation
scope, assertions, authentication references, data and evidence policy. Historical
non-API signatures retain their previous algorithm.

`plan-api REQUIREMENTS --project PATH` performs no network requests and creates
pending scenarios. Existing `plan --approve ID` / `--reject ID` remain the review
interface. Changed API contracts return to pending. No AI path approves a case.

First checkpoint validation: 93 tests passed across API contracts, domain,
contracts and frozen compatibility (non-browser). One initial test collection
error used Pytest's reserved parameter name `request`; it was corrected to
`request_spec` without weakening assertions.
