"""Local persistence adapters; single writer, no implicit schema migrations."""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

import yaml

from autoqa.domain import artifact_reference


def atomic_text(path: Path, text: str) -> None:
    """Replace only after successful serialization/write; clean failed temporary files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def save_json(path: Path, value: object) -> None:
    atomic_text(path, json.dumps(value, indent=2, ensure_ascii=False))


def load_json(path: Path) -> object:
    if not path.is_file():
        raise ValueError(f"Missing {path.name}; run the preceding workflow command first.")
    return json.loads(path.read_text(encoding="utf-8"))


class LocalProjectStorage:
    """Confined paths, including link/junction checks on every operation.

    A completed run (results.json exists) is read-only through this adapter.
    The runner continues to own creation/finalization of new run directories.
    """

    def __init__(self, root: Path):
        self.root = root.resolve()

    def path(self, reference: str) -> Path:
        artifact_reference(reference)
        candidate = self.root
        for part in reference.split("/"):
            candidate = candidate / part
            if candidate.is_symlink() or candidate.is_junction():
                raise ValueError(f"Project artifact cannot be a link: {reference}")
        if not candidate.resolve().is_relative_to(self.root):
            raise ValueError("Artifact escapes project root.")
        return candidate

    def read_json(self, reference: str) -> object:
        return load_json(self.path(reference))

    def read_config(self) -> object:
        return yaml.safe_load(self.path("config.yaml").read_text(encoding="utf-8"))

    def write_text(self, reference: str, text: str) -> None:
        path = self.path(reference)
        parts = reference.split("/")
        if len(parts) >= 3 and parts[0] == "artifacts":
            if self.path(f"artifacts/{parts[1]}/results.json").exists():
                raise ValueError("Historical run directories are immutable.")
        atomic_text(path, text)

    def write_json(self, reference: str, value: object) -> None:
        self.write_text(reference, json.dumps(value, indent=2, ensure_ascii=False))

    def write_config(self, value: dict) -> None:
        self.write_text("config.yaml", yaml.safe_dump(value, sort_keys=False))

    def append_event(self, value: dict) -> None:
        with self.path("logs/events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value) + "\n")


def register_project(parent: Path, name: str, root: Path) -> None:
    metadata = parent.resolve() / ".autoqa"
    metadata.mkdir(exist_ok=True)
    with sqlite3.connect(metadata / "projects.db") as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS projects (name TEXT PRIMARY KEY, path TEXT NOT NULL)"
        )
        connection.execute("INSERT INTO projects VALUES (?, ?)", (name, str(root)))
    save_json(metadata / "active.json", {"path": str(root)})


def selected_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit
    if (Path.cwd() / "config.yaml").is_file():
        return Path.cwd()
    active = Path.cwd() / "projects/.autoqa/active.json"
    if active.is_file():
        return Path(load_json(active)["path"])
    raise ValueError("No active project. Run autoqa init NAME or pass --project PATH.")
