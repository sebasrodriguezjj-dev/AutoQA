"""Unsigned local integrity checks; not a hostile-filesystem security boundary."""

import hashlib
import json
import os
from pathlib import Path, PureWindowsPath


def safe_path(root, reference):
    if (
        not isinstance(reference, str)
        or not reference
        or "\\" in reference
        or ":" in reference
        or PureWindowsPath(reference).drive
        or any(p in {"", ".", ".."} for p in reference.split("/"))
    ):
        raise ValueError("Unsafe framework path")
    path = root
    for part in reference.split("/"):
        path = path / part
        if path.is_symlink() or path.is_junction():
            raise ValueError("Framework links are forbidden")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Framework path escapes root")
    return path


def signature(case):
    data = {key: value for key, value in case.items() if key != "review_status"}
    if case["kind"] not in {"functional", "api"}:
        for key in ("test_data", "evidence_refs", "workflow_id", "contract"):
            data.pop(key, None)
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def validate(root):
    root = Path(root).absolute()
    # Check every root ancestor too, before following a root link.
    if any(p.is_symlink() or p.is_junction() for p in [root, *root.parents]):
        raise ValueError("Framework root cannot traverse links")
    manifest = json.loads(safe_path(root, "framework.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "autoqa.framework.v1" or not manifest.get("cases"):
        raise ValueError("Invalid framework manifest")
    for reference, expected in manifest["files"].items():
        path = safe_path(root, reference)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Framework file changed: {reference}")
    required = {
        "review/cases.json",
        "review/receipts.json",
        "config/environment.json",
        "blueprint.json",
        "tests/test_approved.py",
        "tests/conftest.py",
        "qa_runtime/integrity.py",
        "qa_runtime/runner.py",
        "qa_runtime/fixture.py",
        "qa_runtime/evidence.py",
        "qa_runtime/security.py",
        "qa_runtime/config.py",
        "pytest.ini",
        "requirements.txt",
        "pyproject.toml",
    }
    if not required <= manifest["files"].keys():
        raise ValueError("Framework manifest lacks required files")
    ignored = {".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "artifacts"}
    for directory, folders, names in os.walk(root):
        parent = Path(directory)
        for name in [*folders, *names]:
            path = parent / name
            relative = path.relative_to(root).as_posix()
            # Check top-level ignored folders for links, but never traverse a venv/cache.
            safe_path(root, relative)
            if path.is_file() and path.suffix in {".py", ".pth", ".ini", ".toml"}:
                if relative not in manifest["files"]:
                    raise ValueError(f"Unmanaged executable/config file: {relative}")
        folders[:] = [name for name in folders if name not in ignored]
    cases = json.loads(safe_path(root, "review/cases.json").read_text(encoding="utf-8"))
    receipts = json.loads(safe_path(root, "review/receipts.json").read_text(encoding="utf-8"))
    if len({c["id"] for c in cases}) != len(cases) or {c["id"] for c in cases} != set(
        manifest["cases"]
    ):
        raise ValueError("Reviewed snapshot does not match manifest")
    for case in cases:
        receipt = receipts.get(case["id"], {})
        expected = signature(case)
        if (
            case["review_status"] != "approved"
            or not case["feasible"]
            or manifest["cases"][case["id"]] != expected
            or receipt.get("schema") != "autoqa.approval-receipt.v1"
            or receipt.get("case_id") != case["id"]
            or receipt.get("status") != "approved"
            or receipt.get("scenario_signature") != expected
            or receipt.get("case_revision") != expected
            or not isinstance(receipt.get("approved_at"), str)
        ):
            raise ValueError("Exported approval binding invalid")
    api_cases = [case for case in cases if case["kind"] == "api"]
    if api_cases:
        from .contracts import APIScenario

        contracts = [APIScenario.model_validate(case["contract"]) for case in api_cases]
        if any(
            contract.id != case["id"] for contract, case in zip(contracts, api_cases, strict=True)
        ):
            raise ValueError("API contract identity differs from reviewed case")
        if manifest.get("privacy") != "summary_only" or manifest.get("parameters") != {
            contract.id: len(contract.data.rows) for contract in contracts
        }:
            raise ValueError("API privacy/parameter metadata differs from approved contracts")
        api_required = {
            "qa_runtime/api.py",
            "qa_runtime/api_fixture.py",
            "qa_runtime/contracts.py",
            "qa_runtime/privacy.py",
            "services/api_service.py",
            "config/authentication.json",
        }
        if not api_required <= manifest["files"].keys():
            raise ValueError("Missing API runtime files")
    auth_path = root / "config/authentication.json"
    if auth_path.exists():
        from .contracts import Authentication

        auth = Authentication.model_validate(json.loads(auth_path.read_text(encoding="utf-8")))
        if auth.strategy != "none" and manifest.get("privacy") != "summary_only":
            raise ValueError("Authenticated UI requires protected evidence policy")
    if manifest.get("privacy") == "summary_only":
        config = json.loads((root / "config/environment.json").read_text(encoding="utf-8"))
        if config["trace_enabled"] or config["screenshot_policy"] != "disabled":
            raise ValueError("Protected frameworks must disable unsafe browser capture")
    if "review/management.json" in manifest["files"]:
        from .management import load_inventory

        load_inventory(root, manifest)
        blueprint = json.loads((root / "blueprint.json").read_text(encoding="utf-8"))
        expected_operations = {
            **{s["id"]: len(s["methods"]) for s in blueprint["scenarios"]},
            **{s["id"]: 2 for s in blueprint.get("api_scenarios", [])},
        }
        if manifest.get("operation_counts") != expected_operations:
            raise ValueError("Operation accounting differs from reviewed blueprint")
    return manifest
