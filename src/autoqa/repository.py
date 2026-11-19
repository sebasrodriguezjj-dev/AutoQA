"""Bounded static heuristics: source evidence is never a verified requirement."""

import json
import os
import re
from collections import Counter
from pathlib import Path

from autoqa.core import Discovery, Project, Workflow, load_json, save_json

SKIP = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".next",
    "projects",
    ".autoqa",
    "artifacts",
    ".pytest_cache",
    ".ruff_cache",
}
LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".html": "HTML",
    ".css": "CSS",
    ".go": "Go",
    ".java": "Java",
}
ROUTES = re.compile(
    r"""(?:(?:@\w+\.(?:route|get|post|put|delete|patch)|(?:app|router)\.(?:get|post|put|delete|patch)|path)\s*\(\s*|(?:path|pathname)\s*==\s*)["']([^"']+)["']"""
)


def analyze(project: Project, repository: Path) -> dict:
    root = repository.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(
            "--repo must be an existing local directory; remote cloning is unsupported."
        )
    counts: Counter = Counter()
    manifests, routes, components, models, tests, structure, frameworks = (
        [],
        [],
        [],
        [],
        [],
        [],
        set(),
    )
    scanned, read_bytes, truncated = 0, 0, False
    for current, dirs, files in os.walk(root, followlinks=False):
        directory = Path(current)
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in SKIP
            and not d.startswith(".")
            and not (directory / d).is_symlink()
            and not (directory / d).is_junction()
        )
        if len(directory.relative_to(root).parts) >= 12:
            dirs.clear()
        for name in sorted(files):
            path = directory / name
            if (
                path.is_symlink()
                or path.is_junction()
                or name.startswith(".")
                or any(
                    s in name.lower()
                    for s in ("secret", "credential", "storage-state", "auth-state")
                )
            ):
                continue
            if scanned >= 3000 or read_bytes >= 20_000_000:
                truncated = True
                break
            relative = path.relative_to(root).as_posix()
            scanned += 1
            counts[LANGUAGES.get(path.suffix, "Other")] += 1
            if len(structure) < 150:
                structure.append(relative)
            if (
                name.startswith("test_")
                or name.endswith((".test.ts", ".spec.ts", ".test.js", ".spec.js"))
                or name == "conftest.py"
            ):
                tests.append(relative)
            if path.suffix in {".tsx", ".jsx"}:
                components.append(relative)
            if name in {
                "package.json",
                "pyproject.toml",
                "requirements.txt",
                "pytest.ini",
                "playwright.config.ts",
                "vitest.config.ts",
            }:
                manifests.append(relative)
            if (
                path.suffix not in {".py", ".js", ".ts", ".tsx", ".jsx", ".toml", ".json", ".txt"}
                or path.stat().st_size > 256_000
            ):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            read_bytes += len(text.encode())
            if name == "package.json":
                try:
                    package = json.loads(text)
                    dependencies = {
                        **package.get("dependencies", {}),
                        **package.get("devDependencies", {}),
                    }
                    frameworks.update(
                        key
                        for key in dependencies
                        if key
                        in {
                            "react",
                            "next",
                            "vue",
                            "express",
                            "vite",
                            "vitest",
                            "jest",
                            "@playwright/test",
                        }
                    )
                except ValueError, TypeError:
                    pass
            if path.suffix == ".py":
                for framework in ("fastapi", "flask", "django", "pytest"):
                    if re.search(rf"\b(?:from|import)\s+{framework}\b", text):
                        frameworks.add(framework)
                for match in re.finditer(
                    r"class\s+(\w+)\([^)]*(?:BaseModel|models.Model|Base)[^)]*\)", text
                ):
                    models.append({"name": match[1], "file": relative, "status": "SOURCE"})
            for match in ROUTES.finditer(text):
                routes.append(
                    {
                        "route": match[1],
                        "file": relative,
                        "line": text.count("\n", 0, match.start()) + 1,
                        "status": "SOURCE",
                    }
                )
            if (
                name in {"page.tsx", "page.jsx", "page.js", "page.ts"}
                and "app" in path.relative_to(root).parts
            ):
                parts = path.relative_to(root).parts
                route = "/" + "/".join(parts[parts.index("app") + 1 : -1])
                routes.append({"route": route, "file": relative, "status": "SOURCE"})
        if truncated:
            break
    findings = {
        "root": str(root),
        "status": "SOURCE",
        "files_scanned": scanned,
        "bytes_read": read_bytes,
        "truncated": truncated,
        "languages": dict(counts),
        "frameworks": sorted(frameworks),
        "manifests": manifests,
        "structure": structure,
        "routes": routes,
        "components": components,
        "models": models,
        "existing_tests": tests,
        "opportunities": [
            "Review source route candidates against browser evidence",
            "Review components lacking corresponding test files; coverage is not measured",
        ],
        "limitations": [
            "Heuristics can miss dynamic routes or produce false positives",
            "No repository scripts or dependencies were executed",
        ],
    }
    save_json(project.root / "discovery/repository.json", findings)
    project.config.repository = str(root)
    project.save_config()
    project.audit(f"Statically inspected {scanned} repository files")
    return findings


def source_discovery(project: Project, findings: dict) -> None:
    """Replace stale UI evidence when entering repository-only analysis mode."""
    workflows = [
        Workflow(
            id=f"WF-SOURCE-{i:03}",
            name=f"Review source route {route['route']}",
            page_url=route["route"],
            elements=[],
            evidence=[f"{route['file']}:{route.get('line', 1)}"],
            steps=["Verify source route against a running application"],
            status="SOURCE",
        )
        for i, route in enumerate(findings["routes"], 1)
    ]
    discovery = Discovery(workflows=workflows)
    save_json(project.root / "discovery/workflow-map.json", discovery.model_dump())
    (project.root / "discovery/summary.md").write_text(
        "# Repository discovery\n\n"
        + "\n".join(f"- [SOURCE] {w.name}: {', '.join(w.evidence)}" for w in workflows)
        + "\n\nNo browser behavior was observed. Routes are static candidates requiring review.",
        encoding="utf-8",
    )


def correlate(project: Project, discovery: Discovery) -> dict:
    from urllib.parse import urlsplit

    findings = load_json(project.root / "discovery/repository.json")
    routes = {"/" + r["route"].strip("/"): r for r in findings["routes"]}
    matches = [
        {
            "url": page.url,
            "source": routes[urlsplit(page.url).path],
            "status": "INFERRED",
            "reason": "Exact path match; runtime handler identity is unverified",
        }
        for page in discovery.pages
        if urlsplit(page.url).path in routes
    ]
    result = {
        "matches": matches,
        "unmatched_source_routes": [
            route
            for path, route in routes.items()
            if path not in {urlsplit(p.url).path for p in discovery.pages}
        ],
        "limitations": "Path correlation does not establish requirements or test coverage.",
    }
    save_json(project.root / "discovery/hybrid.json", result)
    return result
