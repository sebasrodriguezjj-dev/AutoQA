"""Bounded local V0.8 IO. Never import, collect or execute inspected source."""

import json
import os
from pathlib import Path

from autoqa.domain import artifact_reference
from autoqa.v08_contracts import AutomationRevision, SourceFile, digest

MAX_BYTES = 1_000_000
MAX_TOTAL = 5_000_000


def checked_root(path):
    root = Path(path).absolute()
    if ".." in root.parts or any(p.is_symlink() or p.is_junction() for p in [root, *root.parents]):
        raise ValueError("Invalid local source root")
    if not root.is_dir():
        raise ValueError("Invalid local source root")
    return root


def read_bytes(path, limit=MAX_BYTES):
    candidate = Path(path).absolute()
    if ".." in candidate.parts or any(
        p.is_symlink() or p.is_junction() for p in [candidate, *candidate.parents]
    ):
        raise ValueError("Invalid local source file")
    if not candidate.is_file() or candidate.stat().st_size > limit:
        raise ValueError("Invalid or oversized local source file")
    with candidate.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("Oversized local source file")
    return raw


def read_json(path, limit=MAX_BYTES):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("Duplicate input key")
            value[key] = item
        return value

    def constant(_):
        raise ValueError("Nonfinite input")

    try:
        return json.loads(
            read_bytes(path, limit).decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=constant,
        )
    except ValueError, TypeError, RecursionError, OSError:
        raise ValueError("Invalid bounded JSON input") from None


def source_revision(path):
    import hashlib

    root = checked_root(path)
    files, total = [], 0
    ignored = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "artifacts"}
    for directory, folders, names in os.walk(root, followlinks=False):
        for name in sorted([*folders, *names]):
            candidate = Path(directory) / name
            if candidate.is_symlink() or candidate.is_junction():
                raise ValueError("Linked source entry")
        folders[:] = sorted(name for name in folders if name not in ignored)
        for name in sorted(names):
            candidate = Path(directory) / name
            reference = candidate.relative_to(root).as_posix()
            artifact_reference(reference)
            raw = read_bytes(candidate)
            total += len(raw)
            if len(files) >= 1000 or total > MAX_TOTAL:
                raise ValueError("Source inventory exceeds bounds")
            files.append(
                SourceFile(
                    path=reference, fingerprint=hashlib.sha256(raw).hexdigest(), size=len(raw)
                )
            )
    files.sort(key=lambda item: item.path)
    root_binding = digest(
        str(root.resolve()).casefold() if os.name == "nt" else str(root.resolve())
    )
    return AutomationRevision(
        root_binding=root_binding,
        digest=digest({"root": root_binding, "files": [f.model_dump() for f in files]}),
        files=files,
    )
