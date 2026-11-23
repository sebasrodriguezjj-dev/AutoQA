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
Python source or inspected build/config metadata and 5 MB total inspected content. VCS, environments, node_modules, caches and run
artifacts are excluded. Linked inspected paths/junctions and unreadable traversal
block analysis; no hostile filesystem mutation/TOCTOU protection is claimed.
Ordinary package.json, pom.xml and Gradle application manifests are configuration
facts, not proof of a test framework. Bounded declaration inspection recognizes
known Node test dependencies (including Cypress and @playwright/test), literal
Java test dependency coordinates, explicit Cypress/Playwright/Jest/Vitest config
filenames, Robot/feature files and Python unittest/Selenium integration concerns.
Plain application build metadata with no recognized test tooling can therefore
return NO_FRAMEWORK. Invalid metadata is uncertain/PARTIALLY_SUPPORTED; oversized
or unreadable inspected content blocks analysis. No dependency is installed.

Python test candidates must match default test_*.py or *_test.py module names and
be top-level test_* functions or direct test_* methods of Test* classes without
constructors. Files under default excluded directories (including build, dist,
hidden directories and *.egg) are not collected test facts. Nested helpers, ordinary helper modules and non-test classes do not
become collected test facts. Test-like helpers outside these conventions, custom
collection configuration and mixed tooling produce conservative partial analysis.
These remain static candidates, not actual Pytest collection. Plugins, aliases,
Gradle execution/version catalogs, Maven inheritance/profiles and arbitrary custom
configuration semantics are not resolved. Detection is not a complete framework parser.

No recognized structure is not proof that a repository has no tests. Imports,
plugins, dependencies, dynamic collection, custom runners, configuration semantics,
actual coverage and runtime behavior remain unverified. No claim of complete
coverage or arbitrary repository compatibility is made.

Owned synthetic acceptance covers empty repository, supported Pytest/Page Object/
fixture structure, unsupported configuration, duplicate names, blocked oversized
source and missing root. Source hashing confirms the read-only supported audit;
a top-level raising statement is inspected without execution.


## Independent audit H01 remediation

Before repair, new reproductions confirmed plain Node/Maven/Gradle applications
were mislabeled UNSUPPORTED and helper test_* functions were mislabeled supported.
The repaired analyzer distinguishes build metadata from declared test tooling and
conventional collection candidates, preserving real Cypress/Pytest/mixed indicators.
Owned read-only tests cover those applications, Cypress TypeScript config, Java
test declarations, helpers, valid Pytest, mixed tooling, empty/unreadable repositories
and oversized metadata. Top-level raising Python/JavaScript is never executed.

Default collection exclusions were checked against the installed Pytest declaration,
not inferred from filenames alone. Explicit custom norecursedirs/testpaths/naming
configuration is reported as requiring review; it is not evaluated as client code.
