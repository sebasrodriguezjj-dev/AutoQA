# Batch A checkpoint

Base: `1853c35b5a666b1c1680d9dc0684014452f82430`.

Stage 1: versioned contracts and read-only legacy projections implemented. Gate: 111 passed,
four browser tests deselected; Ruff check/format passed. Initial sandbox run had 65 fixture
setup errors due to denied pytest temporary-directory access (46 passed); elevated rerun passed.
Legacy core models/signatures remain unchanged. Converted behavior is conservatively descriptive.
Stage 1 commit: `b7566a6a331c9bbb416e64d4a7700280c084c442`.

Stage 2: extracted local storage, registry and selection; atomic config/JSON replacement,
path confinement, link/junction rejection and completed-run protection in the adapter.
Gate: 112 passed, one privilege-dependent link test skipped, four browser tests deselected.
Replaced privilege-dependent setup with deterministic link/junction branch checks; targeted
rerun: 12 passed, no skips. Ruff passed across production source and new tests.

Stage 3: pending.
