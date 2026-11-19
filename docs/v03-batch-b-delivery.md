# AutoQA V0.3 Batch B delivery

## Outcome

Stage 4 (`d6e261453cd59f29798ed49555edbb3deb018d93`) adds a planning/review service and explicit project-bound operation contexts to planning, review, case persistence, generation and execution. Stage 5 (`8e6dc67835519c63210ce1e38f233b487fcd5be4`) adds discovery orchestration and applies the same context check to browser and repository discovery entry points. These are local commits; no push, merge or PR was performed by this work.

## Architecture and security

`PlanningService` exposes plan, approve, reject, signature comparison and generation in-process. Existing deterministic planning and functional validation remain in their established modules. Case matrix writes use the existing local storage adapter. `DiscoveryService` coordinates repository inspection, source-only discovery, UI exploration and hybrid correlation, returning a result containing the existing discovery models and findings. Existing browser lifecycle, scope, DNS, redirect, readiness, request and traversal controls remain in the existing adapters; this change does not grant API-resource permissions. Readiness remains observation rather than evidence of business functionality. Source matches remain inferred.

`AuthorizationContext` requires a resolved project root and explicitly listed operation. Protected functions reject absent, wrong-project or insufficient context before their work. This context expresses caller intent, not authenticated identity or a tamper-proof capability: an embedding application must authenticate and authorize its callers and protect local project files. AI recommendations cannot approve cases through these services. Existing generation checks for approved feasible cases, evidence, scope, safe contract rendering and suite integrity remain in place; run checks still bind the manifest to case signatures. Legacy signatures and case JSON are unchanged. Existing case approval status is not independently cryptographically signed before first generation; a trusted local writer can alter project files, so this is not a hostile-filesystem security boundary.

The CLI retains its flags and exit handling; it constructs contexts from explicit CLI actions (`--authorized` for discovery and `--approved` for generation). Direct Python callers of protected operations must now pass `authorization=AuthorizationContext(project.root, frozenset({...}))`; omission fails closed. This is an intentional compatibility transition. Pure signature and validation functions remain callable without authorization. Legacy projects remain readable without migration. There is no automatic identity or permission management.

## Changed files

Production: `src/autoqa/authorization.py` (initial scaffold in `eb57329`), `planning_service.py`, `discovery_service.py`, `planning.py`, `testing.py`, `exploration.py`, `repository.py`, and `cli.py`. Tests: `test_authorization.py`, `test_discovery_service.py`, `test_pipeline.py`, `test_functional.py`, `test_external_compatibility.py`, and `test_compatibility_baseline.py`. This delivery and the checkpoint document record the work. Frozen compatibility fixtures, dependencies and lockfile have no diff from Batch A.

## Verification

Commands ran using `.venv/Scripts/python.exe` from the repository root, with `-p no:cacheprovider` and separate disposable `--basetemp` directories.

- Stage 4 targeted: `python -m pytest tests/test_authorization.py tests/test_pipeline.py tests/test_compatibility_baseline.py tests/test_contracts.py -m 'not browser' -q ...`: **80 passed, 0 failed, 0 skipped, 4 deselected**.
- Stage 5 targeted: `python -m pytest tests/test_discovery_service.py tests/test_pipeline.py tests/test_external_compatibility.py tests/test_compatibility_baseline.py -m 'not browser' -q ...`: **97 passed, 0 failed, 0 skipped, 10 deselected** (before the additional service browser case).
- Owned local browser tests: `python -m pytest tests/test_pipeline.py tests/test_external_compatibility.py -m browser -q ...`: **10 passed, 0 failed, 0 skipped, 38 deselected**. `python -m pytest tests/test_discovery_service.py -q ...`: **3 passed, 0 failed, 0 skipped, 0 deselected**, including one real-browser hybrid service test and two non-browser cases. No public website was tested.
- Final combined: `python -m pytest tests -m 'not browser' --ignore=tests/test_live_ai.py -q ...`: **172 passed, 0 failed, 0 skipped, 13 browser cases deselected**. The live AI module (one test) was explicitly not executed. Eleven distinct browser cases ran in the focused commands; the two functional browser cases were not executed.
- `python -m ruff check src tests` and `python -m ruff format --check src tests`: passed (40 files formatted). `git diff c5e71f4 -- tests/fixtures pyproject.toml uv.lock`: empty.

An initial Stage 4 run had 12 failures because CLI test doubles did not accept the new authorization keyword. Their signatures were updated, without changing assertions; the targeted rerun passed. No live AI call was made.

## Limitations and Batch C prerequisites

The planning service currently delegates to existing planning functions rather than extracting all pure case-construction rules into the domain. Discovery adapters still persist their own artifacts; the application service coordinates them but does not inject storage or browser ports. Source-only inspection and the real hybrid path were tested, but the full functional browser pass/defect/restore acceptance was not rerun. The existing workflow is single-writer, and the authorization context is an explicit local intent boundary rather than an identity provider. Existing approvals are legacy state; no new per-approval cryptographic record or migration is introduced. Direct integration callers and examples using protected Python functions must be updated to pass contexts.

Batch C should finish generation/execution separation, define authenticated callers and concurrency controls before exposing remote interfaces, address durable approval provenance and pre-generation drift protection without invalidating legacy approvals, and rerun the owned functional acceptance workflow. Batch B is ready as a local, compatibility-tested incremental boundary, subject to these limitations; it is not a complete shared-engine or security isolation release.
