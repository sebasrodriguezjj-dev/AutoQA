"""Reusable local/CI release gates. Every failed command raises and exits nonzero."""

import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, timeout=600):
    print("GATE:", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, check=True, timeout=timeout)


def metadata():
    from autoqa import __version__

    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    assert next(p["version"] for p in lock["package"] if p["name"] == "autoqa-agent") == version
    assert __version__ == importlib.metadata.version("autoqa-agent") == version
    print("Package/import/lock/installed version:", version, flush=True)
    return version


def package():
    version = metadata()
    work = ROOT / ".test-work"
    work.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="release-gate-", dir=work))
    dist = output / "dist"
    run("uv", "build", "--out-dir", dist)
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1 and len(list(dist.glob("*.tar.gz"))) == 1
    for archive in dist.iterdir():
        if archive.suffix == ".whl":
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
        elif archive.name.endswith(".tar.gz"):
            with tarfile.open(archive) as bundle:
                names = bundle.getnames()
        else:
            continue
        assert not any(
            set(name.split("/")) & {"projects", ".test-work", ".venv", ".env", "artifacts"}
            for name in names
        )
    env = output / "installed"
    run("uv", "venv", env, "--python", sys.executable)
    python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    requirements = output / "runtime.txt"
    run(
        "uv",
        "export",
        "--locked",
        "--no-dev",
        "--no-emit-project",
        "--no-hashes",
        "--output-file",
        requirements,
    )
    run(
        "uv",
        "pip",
        "install",
        "--python",
        python,
        "-r",
        requirements,
        wheels[0],
        "ruff==" + importlib.metadata.version("ruff"),
    )
    run(
        python,
        "-c",
        f"import autoqa, importlib.metadata; assert autoqa.__version__ == importlib.metadata.version('autoqa-agent') == {version!r}; assert 'site-packages' in autoqa.__file__; print(autoqa.__version__)",
        cwd=output,
    )
    run(python, "-m", "autoqa", "--help", cwd=output)
    # No target request: this synthetic declared loopback endpoint is collection-only.
    payload = [
        {
            "id": "TC-API-PACKAGE",
            "title": "Synthetic package smoke",
            "request": {"path": "/health"},
            "expect": {"status": 200},
            "environments": [
                {"name": "local", "origin": "http://127.0.0.1:8000", "allow_localhost": True}
            ],
            "environment": "local",
        }
    ]
    spec = output / "api.json"
    spec.write_text(json.dumps(payload), encoding="utf-8")
    parent = output / "sources"
    run(python, "-m", "autoqa", "init", "synthetic", "--parent", parent, cwd=output)
    project = parent / "synthetic"
    run(python, "-m", "autoqa", "plan-api", spec, "--project", project, cwd=output)
    run(
        python,
        "-m",
        "autoqa",
        "plan",
        "--approve",
        "TC-API-PACKAGE",
        "--project",
        project,
        cwd=output,
    )
    export = output / "framework"
    run(
        python,
        "-m",
        "autoqa",
        "build-framework",
        export,
        "--approved",
        "--project",
        project,
        cwd=output,
    )
    run(python, "-m", "autoqa", "validate-framework", export, cwd=output)
    manifest = json.loads((export / "framework.json").read_text())
    assert (
        manifest["version"]
        == tomllib.loads((export / "pyproject.toml").read_text())["project"]["version"]
        == version
    )
    run("uv", "sync", cwd=export)
    independent = export / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(
        independent,
        "-c",
        "import importlib.util; assert importlib.util.find_spec('autoqa') is None",
        cwd=export,
    )
    run(independent, "-m", "qa_runtime.runner", "validate", cwd=export)
    run(independent, "-m", "qa_runtime.runner", "collect", cwd=export)
    print("Package/install/approved export/standalone gates passed:", output, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["all", "checks", "package"], default="all")
    args = parser.parse_args()
    if args.phase in {"all", "checks"}:
        metadata()
        run(sys.executable, "-m", "ruff", "check", "src", "tests", "scripts")
        run(sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "scripts")
        run("uv", "lock", "--check")
        run(
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-m",
            "not browser",
            "--ignore=tests/test_live_ai.py",
            "-q",
        )
    if args.phase in {"all", "package"}:
        package()


if __name__ == "__main__":
    main()
