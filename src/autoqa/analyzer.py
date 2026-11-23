"""Bounded static inspection. Never imports or executes inspected project code."""

import ast
import os
from pathlib import Path


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
                if name in {
                    "package.json",
                    "pom.xml",
                    "build.gradle",
                    "playwright.config.ts",
                    "cypress.config.js",
                }:
                    unsupported = True
                    report["configuration"].append(relative)
                if name in {"pytest.ini", "pyproject.toml", "conftest.py", "setup.cfg", "tox.ini"}:
                    report["configuration"].append(relative)
                if path.suffix in {".robot", ".feature"} or name.endswith(
                    (".spec.ts", ".test.js", ".spec.js")
                ):
                    unsupported = True
                    report["configuration"].append(relative)
                if path.suffix != ".py":
                    continue
                size = path.stat().st_size
                total += size
                if size > 512000 or total > 5000000:
                    raise ValueError("Inspection source budget exceeded")
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
                seen = set()
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith("test_"):
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
