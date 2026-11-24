"""Bounded static inspection. Never imports or executes inspected project code."""

import ast
import json
import os
import re
import xml.etree.ElementTree as ET
from fnmatch import fnmatchcase
from pathlib import Path

BUILD_METADATA = {"package.json", "pom.xml", "build.gradle", "build.gradle.kts"}
UNSUPPORTED_CONFIG = {
    f"{tool}.config.{suffix}"
    for tool in ["cypress", "playwright", "jest", "vitest"]
    for suffix in ["js", "ts", "mjs", "cjs", "mts", "cts"]
}


def metadata_tooling(name, text):
    """Read declarations, not mere manifest existence. No dependency resolution."""
    if name == "package.json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Invalid package metadata")
        dependencies = set()
        for field in [
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
        ]:
            section = data.get(field, {})
            if not isinstance(section, dict):
                raise ValueError("Unknown dependency declaration")
            dependencies.update(section)
        return bool(
            dependencies
            & {
                "cypress",
                "@playwright/test",
                "jest",
                "mocha",
                "vitest",
                "jasmine",
                "ava",
                "tape",
                "webdriverio",
                "testcafe",
                "nightwatch",
            }
        )
    if name == "pom.xml":
        tree = ET.fromstring(text)
        for node in tree.iter():
            if node.tag.rsplit("}", 1)[-1] != "dependency":
                continue
            fields = {n.tag.rsplit("}", 1)[-1]: (n.text or "").strip() for n in node}
            group, artifact = fields.get("groupId", ""), fields.get("artifactId", "")
            if group.startswith(("org.junit", "io.cucumber", "org.seleniumhq.selenium")) or (
                group,
                artifact,
            ) in {("junit", "junit"), ("org.testng", "testng")}:
                return True
        return False
    # Only literal test dependency coordinates are interpreted; Gradle code is never evaluated.
    clean = re.sub(r"/\*.*?\*/|(?m:^\s*//[^\r\n]*$)", "", text, flags=re.S)
    return bool(
        re.search(
            r"(?:testImplementation|testRuntimeOnly|testCompileOnly|testCompile)\s*\(?\s*['\"]"
            r"(?:org\.junit[^:'\"]*|junit|org\.testng|io\.cucumber[^:'\"]*|org\.seleniumhq\.selenium):",
            clean,
        )
    )


def collected_candidates(tree, filename):
    """Default Pytest file/function/class conventions, not arbitrary AST descendants."""
    parts = Path(filename).parts
    filename = parts[-1]
    ignored = ["*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}"]
    if any(fnmatchcase(part, pattern) for part in parts[:-1] for pattern in ignored):
        return set()
    if not (filename.startswith("test_") or filename.endswith("_test.py")):
        return set()
    functions = (ast.FunctionDef, ast.AsyncFunctionDef)
    candidates = set()
    for node in tree.body:
        if isinstance(node, functions) and node.name.startswith("test_"):
            candidates.add(id(node))
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            methods = [n for n in node.body if isinstance(n, functions)]
            if not any(n.name in {"__init__", "__new__"} for n in methods):
                candidates.update(id(n) for n in methods if n.name.startswith("test_"))
    return candidates


def analyze_framework(destination: Path):
    root = Path(destination).absolute()
    report = {
        "classification": "ANALYSIS_BLOCKED",
        "files": [],
        "tests": [],
        "page_objects": [],
        "fixtures": [],
        "configuration": [],
        "concerns": [],
        "limits": [
            "Static Python inspection only; runtime behavior and complete coverage unverified",
            "VCS, virtual environments, vendor dependencies, caches and artifacts excluded; no dependency resolution",
        ],
        "decision": "Do not modify or execute inspected source",
    }
    try:
        if (
            ".." in root.parts
            or not root.is_dir()
            or any(p.is_symlink() or p.is_junction() for p in [root, *root.parents])
        ):
            raise ValueError("Inspection root must be a real directory without links")
        count, total, python, unsupported = 0, 0, False, False

        def unreadable(error):
            raise error

        for parent, dirs, files in os.walk(root, followlinks=False, onerror=unreadable):
            count += 1
            if count > 2000 or len(Path(parent).relative_to(root).parts) > 20:
                raise ValueError("Inspection directory budget exceeded")
            dirs[:] = sorted(
                d
                for d in dirs
                if d
                not in {
                    ".git",
                    ".venv",
                    "node_modules",
                    "__pycache__",
                    ".pytest_cache",
                    "artifacts",
                }
            )
            for name in sorted([*dirs, *files]):
                path = Path(parent) / name
                if path.is_symlink() or path.is_junction():
                    raise ValueError("Links/junctions prevent complete safe inspection")
            for name in sorted(files):
                count += 1
                if count > 2000:
                    raise ValueError("Inspection file budget exceeded")
                path = Path(parent) / name
                relative = path.relative_to(root).as_posix()
                is_metadata = name in BUILD_METADATA or name in {
                    "pytest.ini",
                    "pyproject.toml",
                    "conftest.py",
                    "setup.cfg",
                    "tox.ini",
                }
                if is_metadata or name in UNSUPPORTED_CONFIG:
                    report["configuration"].append(relative)
                if name in UNSUPPORTED_CONFIG:
                    unsupported = True
                if path.suffix == ".py" or is_metadata:
                    size = path.stat().st_size
                    total += size
                    if size > 512000 or total > 5000000:
                        raise ValueError("Inspection source/metadata budget exceeded")
                if name in BUILD_METADATA:
                    try:
                        unsupported |= metadata_tooling(name, path.read_text(encoding="utf-8-sig"))
                    except ValueError, UnicodeError, ET.ParseError:
                        report["concerns"].append(
                            relative + ": metadata tooling could not be established"
                        )
                if is_metadata and name not in BUILD_METADATA and name != "conftest.py":
                    text = path.read_text(encoding="utf-8-sig")
                    if re.search(
                        r"(?m)^\s*(python_files|python_functions|python_classes|testpaths|norecursedirs)\s*=",
                        text,
                    ):
                        report["concerns"].append(
                            relative + ": custom collection configuration requires review"
                        )
                if path.suffix in {".robot", ".feature"} or name.endswith(
                    (".spec.ts", ".test.js", ".spec.js")
                ):
                    unsupported = True
                    report["configuration"].append(relative)
                if path.suffix != ".py":
                    continue
                report["files"].append(relative)
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                except SyntaxError, UnicodeError:
                    report["concerns"].append(relative + ": unsupported syntax/encoding")
                    continue
                python = True
                imports = [
                    ast.unparse(n)
                    for n in ast.walk(tree)
                    if isinstance(n, (ast.Import, ast.ImportFrom))
                ]
                if any("unittest" in value or "selenium" in value for value in imports):
                    unsupported = True
                    report["concerns"].append(
                        relative
                        + ": Python test integration outside initial Pytest/Playwright support"
                    )
                if (
                    any("pytest" in value for value in imports)
                    and not any(
                        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and n.name.startswith("test_")
                        for n in ast.walk(tree)
                    )
                    and name != "conftest.py"
                ):
                    report["concerns"].append(
                        relative + ": test generation/collection may be dynamic"
                    )
                candidates = collected_candidates(tree, relative)
                seen = set()
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith("test_") and id(node) not in candidates:
                            report["concerns"].append(
                                relative + ": test-like helper outside default collection structure"
                            )
                        if id(node) in candidates:
                            # Source identity includes location; no claim this equals a collected Pytest node ID.
                            report["tests"].append(
                                {
                                    "source_id": f"{relative}:{node.lineno}:{node.name}",
                                    "name": node.name,
                                }
                            )
                            if node.name in seen:
                                report["concerns"].append(
                                    relative + ": repeated test name requires review"
                                )
                            seen.add(node.name)
                        if any(
                            ast.unparse(d).startswith(("pytest.fixture", "fixture"))
                            for d in node.decorator_list
                        ):
                            report["fixtures"].append(f"{relative}:{node.name}")
                    if isinstance(node, ast.ClassDef) and (
                        "page" in node.name.lower() or "pages" in path.parts
                    ):
                        report["page_objects"].append(f"{relative}:{node.name}")
        if report["tests"] and python:
            report["classification"] = (
                "PARTIALLY_SUPPORTED"
                if unsupported or report["concerns"]
                else "SUPPORTED_FRAMEWORK"
            )
            report["decision"] = (
                "Audit and recommend compatible improvements; preserve implementation"
            )
            if not report["fixtures"]:
                report["concerns"].append(
                    "No statically recognized fixture; review setup isolation"
                )
            if not report["page_objects"]:
                report["concerns"].append(
                    "No statically recognized Page Objects; review UI structure if applicable"
                )
        elif unsupported:
            report["classification"] = "UNSUPPORTED"
            report["decision"] = "Report detected configuration; do not replace framework"
        elif report["concerns"]:
            report["classification"] = "PARTIALLY_SUPPORTED"
        else:
            report["classification"] = "NO_FRAMEWORK"
            report["decision"] = (
                "Offer build-framework --approved after scenario review; no generation performed"
            )
    except (OSError, ValueError, RecursionError) as error:
        report["classification"] = "ANALYSIS_BLOCKED"
        report["concerns"].append(type(error).__name__ + ": inspection incomplete")
    return report
