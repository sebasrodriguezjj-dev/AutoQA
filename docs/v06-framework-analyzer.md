# V0.6 framework analyzer

`autoqa analyze-framework PATH` prints a JSON factual static audit and decision.
It does not execute/import source, run tests, install dependencies or write files.
Inspection of an existing framework is read-only. Generation remains the separate
existing `build-framework DEST --approved --project PROJECT` operator command and
still refuses overwrite. Recommendations do not authorize client code changes.

| Classification | Meaning and decision |
| --- | --- |
| NO_FRAMEWORK | No recognized test structure in inspected scope; offer approved builder workflow |
| SUPPORTED_FRAMEWORK | Recognized Python/Pytest-style test structure; audit compatible improvements |
| PARTIALLY_SUPPORTED | Mixed/unknown syntax or integrations, duplicate names or dynamic collection concerns |
| UNSUPPORTED | Recognized non-Pytest configuration without supported Python tests; preserve it |
| ANALYSIS_BLOCKED | Invalid/unreadable/linked root, traversal/link, resource budget or incomplete inspection |

The report lists inspected Python files, location-qualified source test identities,
fixture decorator candidates, Page Object naming/location candidates, configuration,
maintainability concerns, scope limits and a create-or-improve decision. These source
identities are not approved executable case IDs or actual Pytest collection results.
Duplicate names are conservative review findings and may be legitimate in distinct
classes. A Page-named class alone does not establish a correct Page Object design.

Limits: at most 2,000 visited directory/file entries, depth 20, 512,000 bytes per
Python source and 5 MB total source. VCS, environments, node_modules, caches and run
artifacts are excluded. Linked inspected paths/junctions and unreadable traversal
block analysis; no hostile filesystem mutation/TOCTOU protection is claimed.
Unsupported configurations include detected Node/Java/Cypress/Playwright TypeScript,
Robot/feature files and Python unittest/Selenium integration concerns. Detection is
heuristic, not a complete parser for every framework/configuration language.

No recognized structure is not proof that a repository has no tests. Imports,
plugins, dependencies, dynamic collection, custom runners, configuration semantics,
actual coverage and runtime behavior remain unverified. No claim of complete
coverage or arbitrary repository compatibility is made.

Owned synthetic acceptance covers empty repository, supported Pytest/Page Object/
fixture structure, unsupported configuration, duplicate names, blocked oversized
source and missing root. Source hashing confirms the read-only supported audit;
a top-level raising statement is inspected without execution.
