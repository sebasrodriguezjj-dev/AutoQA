"""Deterministic Page Object framework export from independently approved scenarios."""

import ast
import hashlib
import json
import re
import shutil
import tempfile
import textwrap
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from autoqa import __version__
from autoqa.authorization import AuthorizationContext, require_authorization
from autoqa.core import Project
from autoqa.framework_runtime.api import ui_auth
from autoqa.framework_runtime.contracts import APIScenario
from autoqa.framework_runtime.integrity import validate
from autoqa.functional import render_functional
from autoqa.planning import approval_receipt, case_signature, verify_approval_binding
from autoqa.security import Scope
from autoqa.testing import validate_python


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method: str = Field(pattern=r"^[a-z][a-z0-9_]+$")
    kind: Literal["navigation", "action", "assertion"]
    description: str
    # Produced only by the trusted compiler, never accepted from a CLI/model payload.
    source: str


class PageBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    module: str = Field(pattern=r"^page_[a-f0-9]{12}$")
    url: str
    locators: dict[str, str]
    operations: list[Operation]


class ScenarioBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")
    page: str
    methods: list[str] = Field(min_length=2)


class FrameworkBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.4", "0.5"] = "0.4"
    api_scenarios: list[APIScenario] = Field(default_factory=list)
    pages: list[PageBlueprint]
    scenarios: list[ScenarioBlueprint]
    unsupported: dict[str, str]

    @model_validator(mode="after")
    def relationships(self):
        pages = {page.module: page for page in self.pages}
        if len(pages) != len(self.pages):
            raise ValueError("Duplicate blueprint page modules")
        ids = [scenario.id.replace("-", "_") for scenario in [*self.scenarios, *self.api_scenarios]]
        if len(ids) != len(set(ids)) or not ids:
            raise ValueError("Blueprint requires unique executable scenarios")
        instances = [s.id for s in self.scenarios] + [
            f"{s.id}--row-{i}" for s in self.api_scenarios for i in range(len(s.data.rows))
        ]
        if len(instances) != len(set(instances)):
            raise ValueError("Scenario parameter identities collide")
        for scenario in self.scenarios:
            page = pages.get(scenario.page)
            if page is None or not set(scenario.methods) <= {op.method for op in page.operations}:
                raise ValueError("Scenario references unknown page operations")
        return self


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def checked_destination(project, destination):
    raw = Path(destination).absolute()
    if ".." in raw.parts:
        raise ValueError("Destination traversal is forbidden")
    for path in [raw, *raw.parents]:
        if path.is_symlink() or path.is_junction():
            raise ValueError("Destination cannot traverse links/junctions")
    target = raw.resolve()
    if target.is_relative_to(project.root) or project.root.is_relative_to(target):
        raise ValueError("Destination cannot overlap the source project")
    if target.exists():
        raise ValueError("Destination already exists; choose a new export directory")
    if not target.parent.is_dir():
        raise ValueError("Destination parent must already exist")
    return target


def _operations(case, discovery, scope):
    observed = next((p for p in discovery.pages if p.url == case.url), None)
    if observed is None:
        raise ValueError("Scenario has no matching browser evidence")
    scope.validate(case.url)
    operations = [
        (
            "navigation",
            "Open observed page",
            f"self.page.goto(self.resolve({case.url!r}), wait_until='domcontentloaded')",
        )
    ]
    if case.kind == "functional":
        local = scope.config.allow_localhost and urlsplit(scope.base).hostname in {
            "localhost",
            "127.0.0.1",
            "::1",
        }
        nodes = ast.parse(textwrap.dedent(render_functional(case, discovery, local=local))).body
        count = len(case.contract["steps"])
        for index, action in enumerate(case.contract["steps"]):
            operations.append(("action", "Perform " + action["action"], ast.unparse(nodes[index])))
        cursor = count
        for assertion in case.contract["assertions"]:
            size = (
                4
                if assertion["check"] == "ordered"
                else 2
                if assertion["check"] == "validity"
                else 1
            )
            operations.append(
                (
                    "assertion",
                    "Verify " + assertion["check"],
                    "\n".join(ast.unparse(n) for n in nodes[cursor : cursor + size]),
                )
            )
            cursor += size
        if cursor != len(nodes):
            raise ValueError("Functional template statement mapping changed")
    elif case.kind == "heading":
        if case.target not in observed.headings:
            raise ValueError("Heading lacks evidence")
        if case.expected != f"Heading {case.target!r} is visible":
            raise ValueError("Heading expectation is not representable by the trusted template")
        operations.append(
            (
                "assertion",
                "Verify observed heading",
                f"expect(page.get_by_role('heading', name={case.target!r}, exact=True).first).to_be_visible()",
            )
        )
    elif case.kind == "link":
        scope.validate(case.destination)
        if not any(
            e.kind == "a" and e.name == case.target and e.href == case.destination
            for e in observed.elements
        ):
            raise ValueError("Link lacks evidence")
        target = next((p for p in discovery.pages if p.url == case.destination), None)
        if not target or not target.headings:
            raise ValueError("Destination heading lacks evidence")
        if case.expected != f"Destination heading {target.headings[0]!r} is visible":
            raise ValueError("Destination expectation differs from its reviewed baseline")
        operations += [
            (
                "action",
                "Follow observed link",
                f"page.get_by_role('link', name={case.target!r}, exact=True).first.click()",
            ),
            (
                "assertion",
                "Verify destination URL",
                f"expect(page).to_have_url(self.resolve({case.destination!r}))",
            ),
            (
                "assertion",
                "Verify destination heading",
                f"expect(page.get_by_role('heading', name={target.headings[0]!r}, exact=True).first).to_be_visible()",
            ),
        ]
    else:
        raise ValueError("Scenario kind requires manual implementation")
    return operations


class _PageLocators(ast.NodeTransformer):
    def __init__(self, properties):
        self.properties = properties

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "page"
            and node.func.attr.startswith("get_by_")
        ):
            expression = ast.unparse(node)
            fallback = (
                node.args[0].value
                if node.args and isinstance(node.args[0], ast.Constant)
                else node.func.attr[7:]
            )
            label = next(
                (
                    kw.value.value
                    for kw in node.keywords
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant)
                ),
                fallback,
            )
            slug = re.sub(r"[^a-z0-9]+", "_", str(label).lower()).strip("_")[:32] or "element"
            name = "locator_" + slug + "_" + sha(expression)[:8]
            self.properties[name] = expression.replace("page.", "self.page.", 1)
            return ast.Attribute(
                value=ast.Name(id="self", ctx=ast.Load()), attr=name, ctx=ast.Load()
            )
        return self.generic_visit(node)

    def visit_Name(self, node):
        if node.id == "page":
            return ast.Attribute(
                value=ast.Name(id="self", ctx=ast.Load()), attr="page", ctx=ast.Load()
            )
        return node


def compile_blueprint(project):
    cases = [c for c in project.cases() if c.review_status == "approved"]
    if not cases:
        raise ValueError("No approved scenarios; review and approve before building")
    has_ui = any(c.kind != "api" for c in cases)
    scope = Scope(project.config.application_url, project.config) if has_ui else None
    discovery = project.discovery() if has_ui else None
    pages, scenarios, unsupported, selected, api_scenarios = {}, [], {}, [], []
    for case in cases:
        verify_approval_binding(project, case)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", case.id):
            raise ValueError("Unsafe scenario ID")
        try:
            if not case.feasible:
                raise ValueError("Approved scenario is not automatable")
            if case.kind == "api":
                api = APIScenario.model_validate(case.contract)
                if api.id != case.id:
                    raise ValueError("API contract identity differs from reviewed case")
                api_scenarios.append(api)
                selected.append(case)
                continue
            operations = _operations(case, discovery, scope)
        except ValueError as error:
            unsupported[case.id] = str(error)
            continue
        module = "page_" + sha(case.url)[:12]
        page = pages.setdefault(
            module, PageBlueprint(module=module, url=case.url, locators={}, operations=[])
        )
        methods = []
        for kind, description, source in operations:
            tree = _PageLocators(page.locators).visit(ast.parse(source))
            source = ast.unparse(ast.fix_missing_locations(tree))
            readable = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")
            method = kind + "_" + readable + "_" + sha(source)[:12]
            methods.append(method)
            if not any(op.method == method for op in page.operations):
                page.operations.append(
                    Operation(method=method, kind=kind, description=description, source=source)
                )
        scenarios.append(ScenarioBlueprint(id=case.id, page=module, methods=methods))
        selected.append(case)
    if not scenarios and not api_scenarios:
        raise ValueError("No supported approved scenarios: " + encoded(unsupported))
    if len({c.id.replace("-", "_") for c in selected}) != len(selected):
        raise ValueError("Scenario IDs collide after normalization")
    return FrameworkBlueprint(
        pages=list(pages.values()),
        scenarios=scenarios,
        unsupported=unsupported,
        api_scenarios=api_scenarios,
        schema_version="0.5" if api_scenarios else "0.4",
    ), selected


def _runtime_sources():
    package = Path(__file__).parent
    runtime = package / "framework_runtime"
    files = {"qa_runtime/" + p.name: p.read_text(encoding="utf-8") for p in runtime.glob("*.py")}
    core_tree = ast.parse((package / "core.py").read_text(encoding="utf-8"))
    nodes = [
        n
        for n in core_tree.body
        if isinstance(n, ast.ClassDef) and n.name in {"Config", "APIResourceRule"}
    ]
    files["qa_runtime/config.py"] = (
        "import re\nfrom typing import Literal\nfrom urllib.parse import urlsplit\nfrom pydantic import BaseModel, ConfigDict, Field, field_validator\n\n"
        + "\n\n".join(ast.unparse(n) for n in nodes)
    )
    files["qa_runtime/security.py"] = (
        (package / "security.py")
        .read_text(encoding="utf-8")
        .replace("from autoqa.core import Config", "from .config import Config")
    )
    return files


def _render(blueprint):
    files = _runtime_sources()
    files.update(
        {
            "pages/__init__.py": "",
            "tests/conftest.py": "from qa_runtime.fixture import qa_session as qa_session\nfrom qa_runtime.api_fixture import qa_api as qa_api\nfrom qa_runtime.privacy import pytest_runtest_makereport as pytest_runtest_makereport\n",
        }
    )
    imports, tests = [], []
    for page in blueprint.pages:
        source = '"""Reviewed page locators and reusable actions/assertions."""\nimport re\nfrom playwright.sync_api import expect\n\nclass PageObject:\n    def __init__(self, session):\n        self.page, self.resolve, self.evidence = session\n'
        # Only ordering assertions need re; keep generated code lint-clean.
        if not any("re.sub" in op.source for op in page.operations):
            source = source.replace("import re\n", "")
        for name, expression in page.locators.items():
            source += f"\n    @property\n    def {name}(self):\n        return {expression}\n"
        if not any("expect(" in op.source for op in page.operations):
            source = source.replace("from playwright.sync_api import expect\n", "")
        for op in page.operations:
            body = "\n".join("            " + line for line in op.source.splitlines())
            source += f"\n    def {op.method}(self):\n        with self.evidence.step({op.kind!r}, {op.description!r}):\n{body}\n"
        files[f"pages/{page.module}.py"] = source
        imports.append(f"from pages.{page.module} import PageObject as {page.module}")
    for scenario in blueprint.scenarios:
        body = "\n".join("    model." + method + "()" for method in scenario.methods)
        tests.append(
            f"def test_{scenario.id.replace('-', '_')}(qa_session):\n    model = {scenario.page}(qa_session)\n{body}\n"
        )
    if blueprint.api_scenarios:
        files["services/__init__.py"] = ""
        files[
            "services/api_service.py"
        ] = '''"""Reusable reviewed API service; no embedded credentials or untrusted code."""
import json
from pathlib import Path

class ReviewedAPI:
    def __init__(self, client):
        self.client = client

    def run(self, case_id, row):
        root = Path(__file__).resolve().parents[1]
        cases = json.loads((root / "review/cases.json").read_text(encoding="utf-8"))
        contract = next(c["contract"] for c in cases if c["id"] == case_id)
        self.client.execute(contract, row)
'''
        imports += ["import pytest", "from services.api_service import ReviewedAPI"]
        for api in blueprint.api_scenarios:
            tests.append(
                f"@pytest.mark.parametrize('row', {list(range(len(api.data.rows)))!r})\ndef test_{api.id.replace('-', '_')}(qa_api, row):\n    ReviewedAPI(qa_api).run({api.id!r}, row)\n"
            )
    files["tests/test_approved.py"] = "\n".join(imports) + "\n\n" + "\n".join(tests)
    return files


def _requirements():
    # Pin the builder's resolved runtime distributions, never executables found on PATH.
    import importlib.metadata

    names = ["playwright", "pytest", "pydantic", "pyyaml"]
    return [f"{name}=={importlib.metadata.version(name)}" for name in names]


class FrameworkService:
    def __init__(self, project: Project, authorization: AuthorizationContext | None):
        self.project, self.authorization = project, authorization

    def build(self, destination: Path):
        require_authorization(self.authorization, self.project.root, "generate")
        destination = checked_destination(self.project, destination)
        blueprint, cases = compile_blueprint(self.project)
        files = _render(blueprint)
        from autoqa.management import export_inventory

        inventory = export_inventory(self.project, cases, blueprint.unsupported)
        files["review/management.json"] = encoded(inventory.model_dump())
        requirements = _requirements()
        config = self.project.config.model_dump(
            exclude={"repository", "ai_provider", "ai_model", "auth_reference"}
        )
        config["name"] = "Reviewed automation framework"
        authentication = ui_auth(self.project.config.auth_reference)
        protected = bool(blueprint.api_scenarios) or authentication.strategy != "none"
        if protected:
            config["screenshot_policy"] = "disabled"
            config["trace_enabled"] = False
        files["config/authentication.json"] = encoded(authentication.model_dump())
        files.update(
            {
                "config/environment.json": encoded(config),
                "review/cases.json": encoded([case.model_dump() for case in cases]),
                "review/receipts.json": encoded(
                    {case.id: approval_receipt(self.project, case) for case in cases}
                ),
                "blueprint.json": encoded(blueprint.model_dump()),
                "requirements.txt": "\n".join(requirements) + "\n",
                "pyproject.toml": f'[project]\nname = "reviewed-qa-framework"\nversion = "{__version__}"\nrequires-python = ">=3.14,<3.15"\ndependencies = '
                + json.dumps(requirements)
                + "\n\n[tool.uv]\npackage = false\n",
                "pytest.ini": "[pytest]\ntestpaths = tests\naddopts =\npythonpath = .\n",
                ".gitignore": ".venv/\n__pycache__/\n.pytest_cache/\nartifacts/\n.env\n",
                "README.md": _README,
            }
        )
        for name, text in list(files.items()):
            if name.endswith(".py"):
                files[name] = validate_python(text, name)
        # Never silently export conventional credential material from reviewed inputs/config.
        secret = re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9]{30,}|sk-proj-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}"
        )
        if any(secret.search(value) for value in files.values()):
            raise ValueError("Potential credential material in export; review source inputs")
        manifest = {
            "schema": "autoqa.framework.v1",
            "version": __version__,
            "files": {name: sha(text) for name, text in files.items()},
            "cases": {case.id: case_signature(case) for case in cases},
            "operation_counts": {
                **{s.id: len(s.methods) for s in blueprint.scenarios},
                **{s.id: 2 for s in blueprint.api_scenarios},
            },
        }
        if protected:
            manifest["privacy"] = "summary_only"
            manifest["parameters"] = {a.id: len(a.data.rows) for a in blueprint.api_scenarios}
        files["framework.json"] = encoded(manifest)
        staging = Path(tempfile.mkdtemp(prefix=".autoqa-export-", dir=destination.parent))
        try:
            for name, content in files.items():
                path = staging / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="")
            validate(staging)
            if destination.exists():
                raise ValueError("Destination appeared during export; refusing overwrite")
            staging.rename(destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        self.project.audit(
            f"Exported {len(cases)} reviewed scenarios; {len(blueprint.unsupported)} unsupported"
        )
        return {
            "destination": str(destination),
            "cases": [case.id for case in cases],
            "unsupported": blueprint.unsupported,
        }

    def run(self, destination: Path, selection=None):
        require_authorization(self.authorization, self.project.root, "execute")
        manifest = validate(destination)
        current = {case.id: case for case in self.project.cases()}
        for case_id, signature in manifest["cases"].items():
            case = current.get(case_id)
            if not case or case.review_status != "approved" or case_signature(case) != signature:
                raise ValueError("Project approvals changed; review and build a new framework")
            verify_approval_binding(self.project, case)
        from autoqa.framework_runtime.management import TestSelection, load_inventory, select

        plan = select(load_inventory(destination, manifest), selection or TestSelection())
        from autoqa.management import export_inventory

        current_suite = export_inventory(self.project, [current[i] for i in manifest["cases"]], {})
        if self.project.storage.path("test-cases/management.json").exists():
            from autoqa.framework_runtime.management import digest

            if digest(current_suite) != digest(load_inventory(destination, manifest)):
                raise ValueError("Current suite membership changed; export again")
        self.project.audit("Framework selection " + plan.model_dump_json())
        arguments = []
        if "review/management.json" not in manifest["files"]:
            if plan.selection.mode != "all":
                raise ValueError(
                    "Historical export has no selective runner; re-export after review"
                )
        elif plan.selection.mode == "all":
            arguments = ["--all"]
        else:
            for value in plan.selection.values:
                arguments += ["--" + plan.selection.mode, value]
        import os
        import subprocess
        import sys

        environment = {
            k: v
            for k, v in os.environ.items()
            if k.upper() not in {"PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"}
        }
        completed = subprocess.run(
            [sys.executable, "-m", "qa_runtime.runner", "run", *arguments],
            cwd=destination,
            env=environment,
            timeout=self.project.config.overall_timeout_seconds + 60,
        )
        return completed.returncode


_README = """# Reviewed Playwright/Pytest framework

Standalone Python 3.14 project; AutoQA is not required or imported. Only selected
approved supported scenarios become tests. See blueprint.json for unsupported cases.
pages/ contains checked locator properties and reusable action/assertion methods;
tests/ composes these methods. review/ retains only exported cases and their receipts.

## Setup and execution

```
uv sync
uv run playwright install chromium
uv run python -m qa_runtime.runner validate
uv run python -m qa_runtime.runner collect
uv run python -m qa_runtime.runner run
uv run python -m qa_runtime.runner run --case TC-EXAMPLE
uv run python -m qa_runtime.runner run --pack SMOKE
uv run python -m qa_runtime.runner run --all
```

Alternatively create a Python 3.14 virtual environment and pip install -r requirements.txt,
then run the same python -m commands. Run from this directory. Dependency versions are
pinned to the builder environment; uv resolves transitive dependencies into its own lock.
V0.6 adds --case, --pack, --suite, --tag and --all (one mode per invocation).
Repeat --case/--pack/--tag within a mode; overlapping membership executes once.
Use source suite-propose and suite-approve before export to review membership.
No selection flag preserves default approved-enabled regression selection. Unknown,
disabled, unapproved or empty selections fail without falling back to all tests.
Reports distinguish logical cases from parameter row invocations and selected scope
from full regression. Unsupported approved-enabled cases make regression incomplete.
A suite snapshot/digest and timestamps are retained in every run's results.json.
The runner collects before executing; collection and test failures return nonzero.
Use the runner rather than direct pytest to retain unique runs and integrity checks.

config/environment.json is a reviewed snapshot. Headed/headless, slow_mo_ms,
screenshot_policy (every_step/failures_only/disabled) and trace_enabled are preserved.
To change these, update the source project's config and export a new directory.
AUTOQA_BASE_URL can point to a separately authorized environment on the same allowed
hostname; exact origin/path restrictions still apply. The application must be running.
V0.5 API tests use exact reviewed contract origins/methods/paths and explicit mutation
review. Redirects are rejected, DNS addresses are validated and pinned, and remote API
requests require HTTPS. API-only runs do not require an installed browser. Select only
a declared environment using AUTOQA_ENVIRONMENT; AUTOQA_BASE_URL applies to UI only.
Credentials use AUTOQA_SECRET_* environment references. Missing credentials fail.
For reviewed UI cookies, source auth_reference is cookie:AUTOQA_SECRET_NAME:cookie_name;
no login form, storage-state import or automatic session acquisition is implemented.
API/credential-bearing exports use summary_only retention: no raw HTTP bodies, header
values, console logs, JUnit errors, screenshots or traces are persisted. Structured
status/duration/operation evidence and sanitized JUnit remain. Summaries are retained
until the operator removes them; automatic time-based deletion is not implemented.
Unauthenticated UI-only exports retain V0.4 capture behavior and privacy limitations.

Every run writes artifacts/RUN_ID/{results.json,diagnosis.json,report.html,junit.xml,
pytest.log,collection.log} plus actual step screenshots/traces. Open report.html locally.
Steps represent entered actions/assertions, not invented outcomes for missing operations.
Reports do not establish defect root cause. Capture errors remain separate from failures.

Unsigned manifests/receipts detect accidental changes and require trusted local writers.
This is not an OS sandbox or authenticated approval service. Do not edit generated files
and refresh hashes to bypass review; reapprove in the source project and export again.
Standalone snapshots do not observe later source-project revocation. AutoQA run-framework
also checks current project approvals. Windows timeout cleanup of descendants is limited.
No credentials, browser state, raw discovery images or prior run evidence are exported.
Review approved input values and all resulting artifacts before distribution: JUnit,
logs, screenshots and traces can contain sensitive application data. Disabling standalone
screenshots does not disable trace images. No redaction guarantee is made.
"""
