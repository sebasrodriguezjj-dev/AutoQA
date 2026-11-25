"""Read-only reconciliation of bounded source; edited Python is never executed."""

import ast
from pathlib import Path

from autoqa.framework_runtime.integrity import validate
from autoqa.v08_contracts import ReconciliationFinding, ReconciliationReport, digest
from autoqa.v08_io import checked_root, read_bytes, read_json, source_revision


def _tree(raw):
    return ast.parse(raw.decode("utf-8"))


def _locator(node):
    """Recognize only a literal trusted locator expression, without evaluating it."""
    from autoqa.v08_contracts import LocatorSpec

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None
    owner = node.func.value
    if not (
        isinstance(owner, ast.Attribute)
        and owner.attr == "page"
        and isinstance(owner.value, ast.Name)
        and owner.value.id == "self"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and type(node.args[0].value) is str
    ):
        return None
    strategy = node.func.attr.removeprefix("get_by_")
    if node.func.attr != "get_by_" + strategy or strategy not in {
        "role",
        "label",
        "placeholder",
        "test_id",
    }:
        return None
    keywords = {}
    for keyword in node.keywords:
        if keyword.arg in keywords or not isinstance(keyword.value, ast.Constant):
            return None
        keywords[keyword.arg] = keyword.value.value
    if strategy == "role":
        if set(keywords) not in (set(), {"name", "exact"}):
            return None
        if keywords and (keywords["exact"] is not True or type(keywords["name"]) is not str):
            return None
    elif strategy == "test_id":
        if keywords:
            return None
    elif keywords != {"exact": True}:
        return None
    return LocatorSpec(strategy=strategy, value=node.args[0].value, name=keywords.get("name", ""))


def locator_edit(before, after):
    """Return one property locator edit iff the entire remaining AST is identical.

    This classifies a supported declarative change, not a sandbox or trust grant.
    """
    old, new = _tree(before), _tree(after)
    old_properties, new_properties = {}, {}
    for tree, properties in [(old, old_properties), (new, new_properties)]:
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("locator_")
                and len(node.decorator_list) == 1
                and isinstance(node.decorator_list[0], ast.Name)
                and node.decorator_list[0].id == "property"
                and len(node.body) == 1
                and isinstance(node.body[0], ast.Return)
            ):
                if node.name in properties:
                    return None
                properties[node.name] = node
    if old_properties.keys() != new_properties.keys():
        return None
    changes = []
    for name, left in old_properties.items():
        right = new_properties[name]
        a, b = left.body[0].value, right.body[0].value
        if ast.dump(a) == ast.dump(b):
            continue
        old_locator, new_locator = _locator(a), _locator(b)
        if old_locator is None or new_locator is None:
            return None
        changes.append((name, old_locator, new_locator))
        left.body[0].value = ast.Constant(value="reviewed-locator-placeholder")
        right.body[0].value = ast.Constant(value="reviewed-locator-placeholder")
    if len(changes) != 1 or ast.dump(old) != ast.dump(new):
        return None
    return changes[0]


def _case_mapping(blueprint, path, property_name=None):
    module = Path(path).stem
    page = next((p for p in blueprint.get("pages", []) if p.get("module") == module), None)
    if page is None:
        return []
    methods = {o["method"] for o in page.get("operations", [])}
    if property_name:
        methods = set()
        for operation in page.get("operations", []):
            tree = ast.parse(operation["source"])
            if any(
                isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id == "self"
                and n.attr == property_name
                for n in ast.walk(tree)
            ):
                methods.add(operation["method"])
    return sorted(
        scenario["id"]
        for scenario in blueprint.get("scenarios", [])
        if scenario.get("page") == module and methods.intersection(scenario.get("methods", []))
    )


def _assertions(raw):
    return [
        ast.dump(node)
        for node in ast.walk(_tree(raw))
        if isinstance(node, ast.Assert)
        or (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr.startswith(("to_", "not_to_"))
        )
    ]


def _imports(raw):
    return [
        ast.dump(node)
        for node in ast.walk(_tree(raw))
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]


def managed_baseline(source):
    """Bound before invoking the existing static managed-integrity validator."""
    root = checked_root(source)
    revision = source_revision(root)
    validate(root)
    return root, revision, read_json(root / "framework.json"), read_json(root / "blueprint.json")


class ReconciliationService:
    def __init__(self, project):
        self.project = project

    def inspect(self, baseline, current):
        try:
            return self._inspect(baseline, current)
        except ValueError, OSError, TypeError, KeyError, RecursionError, OverflowError, SyntaxError:
            raise ValueError("Invalid bounded reconciliation input") from None

    def _inspect(self, baseline, current):
        root, old_revision, manifest, blueprint = managed_baseline(baseline)
        changed_root = checked_root(current)
        current_revision = source_revision(changed_root)
        old = {f.path: f.fingerprint for f in old_revision.files}
        new = {f.path: f.fingerprint for f in current_revision.files}
        findings = []
        removed = {path: value for path, value in old.items() if path not in new}
        for path in sorted(old.keys() | new.keys()):
            state, supported, reason = "UNCHANGED_MANAGED", False, "Managed content is unchanged."
            cases = _case_mapping(blueprint, path)
            if path not in new:
                state, reason = (
                    "REMOVED",
                    "Managed source was removed; no passing or executable replacement is inferred.",
                )
            elif path not in old:
                matches = [candidate for candidate, value in removed.items() if value == new[path]]
                if len(matches) == 1:
                    state, reason = (
                        "MOVED_CANDIDATE",
                        "Exact prior content occurs at a new path; source identity still requires explicit review.",
                    )
                    cases = _case_mapping(blueprint, matches[0])
                elif path.endswith(".py") and (
                    path.startswith("tests/") or Path(path).name.startswith("test_")
                ):
                    state, reason = (
                        "MANUAL_CANDIDATE",
                        "New static Python test candidate; never imported, collected or trusted by name.",
                    )
                else:
                    state, reason = (
                        "UNSUPPORTED",
                        "New unmanaged content is outside the supported reconciliation subset.",
                    )
            elif old[path] != new[path]:
                state, reason = (
                    "MODIFIED_MANAGED",
                    "Managed content changed; it is not trusted by updating its fingerprint.",
                )
                before, after = read_bytes(root / path), read_bytes(changed_root / path)
                if (
                    path == "framework.json"
                    or path.startswith(("review/", "config/", "qa_runtime/"))
                    or path
                    in {
                        "blueprint.json",
                        "pytest.ini",
                        "pyproject.toml",
                        "requirements.txt",
                        "tests/conftest.py",
                    }
                ):
                    state, reason = (
                        "INTEGRITY_VIOLATION",
                        "Managed approval, runtime, configuration or integrity content was modified.",
                    )
                elif path.startswith("pages/") and path.endswith(".py"):
                    edit = locator_edit(before, after)
                    if edit:
                        cases = _case_mapping(blueprint, path, edit[0])
                        supported = len(cases) == 1
                        state, reason = (
                            "PAGE_OBJECT_CHANGED",
                            "Only one literal locator expression changed; the remaining AST is identical.",
                        )
                        if not supported:
                            reason = "Locator change affects ambiguous or unmapped cases; manual review is required."
                    elif _assertions(before) != _assertions(after):
                        state, reason = (
                            "ASSERTION_CHANGED",
                            "Assertion or expected-outcome source changed; automatic reconciliation is forbidden.",
                        )
                    elif _imports(before) != _imports(after):
                        state, reason = (
                            "PAGE_OBJECT_CHANGED",
                            "Page Object dependencies changed; this is outside declarative locator reconciliation.",
                        )
                    else:
                        state, reason = (
                            "UNSUPPORTED",
                            "Page Object contains changes beyond one supported locator expression.",
                        )
                elif path.endswith(".py"):
                    if _assertions(before) != _assertions(after):
                        state, reason = (
                            "ASSERTION_CHANGED",
                            "Assertion source changed; original behavior cannot be silently replaced.",
                        )
                    else:
                        state, reason = (
                            "UNSUPPORTED",
                            "Modified executable source is not a supported declarative reconciliation.",
                        )
                elif "data" in path.casefold():
                    state, reason = (
                        "DATA_REFERENCE_CHANGED",
                        "Data content or references changed; independent data and scenario review is required.",
                    )
            elif path not in manifest["files"] and path != "framework.json":
                state, reason = "UNSUPPORTED", "Content is not a manifest-managed executable input."
            findings.append(
                ReconciliationFinding(
                    path=path, state=state, case_ids=cases, rationale=reason, supported=supported
                )
            )
        payload = {
            "project_id": self.project.root.name,
            "baseline": old_revision,
            "current": current_revision,
            "findings": findings,
            "limitations": [
                "Static inspection never imports, collects, installs or executes inspected source.",
                "Only an unambiguous single Page Object locator edit can feed a separately reviewed declarative repair.",
                "Source revisions are trusted-local integrity bindings, not authenticated identity or a sandbox.",
            ],
        }
        candidate = ReconciliationReport(id="REC-PENDING", **payload)
        data = candidate.model_dump(mode="json")
        data["id"] = "REC-" + digest(
            {
                "domain": "v08-reconciliation",
                **{key: value for key, value in data.items() if key != "id"},
            }
        )
        return ReconciliationReport.model_validate(data)


def supported_manual_edit(
    project, baseline, current, case_id, expected_locator, expected_property, expected_methods
):
    """Require the entire edited repository to contain exactly one supported change."""
    report = ReconciliationService(project).inspect(baseline, current)
    before = {f.path: f.fingerprint for f in report.baseline.files}
    after = {f.path: f.fingerprint for f in report.current.files}
    # Unchanged non-executable metadata (for example a generated dependency lock) is
    # still disclosed as unsupported, but it is not a newly authored source change.
    changed = [f for f in report.findings if before.get(f.path) != after.get(f.path)]
    if len(changed) != 1 or not changed[0].supported or changed[0].case_ids != [case_id]:
        raise ValueError("Unsupported manual reconciliation")
    edit = locator_edit(
        read_bytes(Path(baseline) / changed[0].path), read_bytes(Path(current) / changed[0].path)
    )
    if edit is None or edit[2] != expected_locator or edit[0] != expected_property:
        raise ValueError("Manual locator does not match observed proposal")
    blueprint = read_json(Path(baseline) / "blueprint.json")
    page = next(p for p in blueprint["pages"] if p["module"] == Path(changed[0].path).stem)
    methods = set()
    for operation in page["operations"]:
        if any(
            isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Name)
            and n.value.id == "self"
            and n.attr == edit[0]
            for n in ast.walk(ast.parse(operation["source"]))
        ):
            methods.add(operation["method"])
    if not methods or not methods <= expected_methods:
        raise ValueError("Manual change affects unrelated operations")
    return report.current
