"""Independent V0.8 boundary tests using synthetic source and data only."""

import json
import os
from pathlib import Path

import pytest

from autoqa.v08_contracts import (
    ApplicationInventory,
    AutomationRevision,
    DiagnosticFinding,
    ImpactFinding,
    LocatorSpec,
)
from autoqa.v08_contracts import (
    TestDataInventory as DataInventory,
)
from autoqa.v08_io import checked_root, read_bytes, read_json, source_revision


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize("payload", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b"\xff"])
def test_bounded_json_rejects_ambiguous_input_without_echo(tmp_path, payload):
    path = tmp_path / "private-input-sentinel.json"
    path.write_bytes(payload)
    before = snapshot(tmp_path)
    with pytest.raises(ValueError) as caught:
        read_json(path)
    assert str(caught.value) == "Invalid bounded JSON input"
    assert snapshot(tmp_path) == before


def test_oversized_source_is_refused_without_read_or_mutation(tmp_path, monkeypatch):
    path = tmp_path / "large.py"
    path.write_bytes(b"x" * 1_000_001)
    before = snapshot(tmp_path)

    def forbidden_open(*args, **kwargs):
        pytest.fail("Oversized input was opened")

    monkeypatch.setattr(Path, "open", forbidden_open)
    with pytest.raises(ValueError):
        read_bytes(path)
    monkeypatch.undo()
    assert snapshot(tmp_path) == before


def test_inspection_never_imports_or_executes_source(tmp_path, monkeypatch):
    root = tmp_path / "untrusted"
    root.mkdir()
    marker = tmp_path / "MUST-NOT-EXIST"
    payload = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
    for filename in ["conftest.py", "test_malicious.py", "setup.py"]:
        (root / filename).write_text(payload, encoding="utf-8")
    (root / "pyproject.toml").write_text(
        "[build-system]\nrequires=['never-install-this-fixture']\n"
    )
    before = snapshot(root)
    import subprocess

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("Inspection ran a process"))
    revision = source_revision(root)
    assert len(revision.files) == 4
    assert not marker.exists()
    assert snapshot(root) == before
    assert str(root) not in revision.model_dump_json()


def test_root_substitution_changes_binding_even_for_identical_files(tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    left.mkdir()
    right.mkdir()
    for root in [left, right]:
        (root / "test_owned.py").write_text("def test_owned():\n    assert True\n")
    first, second = source_revision(left), source_revision(right)
    assert first.files == second.files
    assert first.root_binding != second.root_binding
    assert first.digest != second.digest


def test_source_timestamp_and_directory_iteration_do_not_manufacture_revision(
    tmp_path, monkeypatch
):
    root = tmp_path / "owned"
    root.mkdir()
    (root / "a.py").write_text("a = 1\n")
    (root / "b.py").write_text("b = 2\n")
    first = source_revision(root)
    stamp = (root / "a.py").stat().st_mtime_ns + 1_000_000
    os.utime(root / "a.py", ns=(stamp, stamp))
    walk = os.walk

    def reverse_walk(*args, **kwargs):
        for directory, folders, names in walk(*args, **kwargs):
            yield directory, folders, list(reversed(names))

    monkeypatch.setattr(os, "walk", reverse_walk)
    assert source_revision(root) == first


def test_unreadable_source_subtree_cannot_produce_complete_revision(tmp_path, monkeypatch):
    root = tmp_path / "owned"
    hidden = root / "unreadable"
    hidden.mkdir(parents=True)
    (hidden / "test_hidden.py").write_text("def test_hidden():\n    assert False\n")
    scandir = os.scandir

    def denied(path):
        if Path(path) == hidden:
            raise PermissionError("private-path-sentinel")
        return scandir(path)

    monkeypatch.setattr(os, "scandir", denied)
    with pytest.raises(ValueError) as caught:
        source_revision(root)
    assert "private-path-sentinel" not in str(caught.value)


@pytest.mark.parametrize("count", [True, False, "1", 0, 2])
def test_locator_cardinality_is_an_actual_unique_integer(count):
    with pytest.raises(ValueError):
        LocatorSpec(strategy="test_id", value="owned", count=count)


@pytest.mark.parametrize("value", [0, 0.0, "false", True])
def test_unconfirmed_diagnostic_and_impact_flags_require_literal_false(value):
    with pytest.raises(ValueError):
        DiagnosticFinding(
            id="DIA-1",
            category="INSUFFICIENT_EVIDENCE",
            facts=["Owned record"],
            next_check="Review evidence",
            root_cause_confirmed=value,
        )
    with pytest.raises(ValueError):
        ImpactFinding(
            object_id="OBJ-1",
            kind="route",
            change="CHANGED",
            source_locations=["app.py"],
            rationale="Potential static impact",
            verified_runtime_impact=value,
        )


@pytest.mark.parametrize(
    "filename", ["../outside.py", "/absolute.py", "C:/outside.py", "a\\b.py", "a/../b.py"]
)
def test_source_revision_paths_are_confined(filename):
    with pytest.raises(ValueError):
        AutomationRevision.model_validate(
            {
                "root_binding": "a" * 64,
                "digest": "b" * 64,
                "files": [{"path": filename, "fingerprint": "c" * 64, "size": 1}],
            }
        )


def test_casefold_collisions_cannot_hide_conflicting_sources():
    with pytest.raises(ValueError):
        AutomationRevision.model_validate(
            {
                "root_binding": "a" * 64,
                "digest": "b" * 64,
                "files": [
                    {"path": p, "fingerprint": "c" * 64, "size": 1} for p in ["a.py", "A.py"]
                ],
            }
        )


def test_conflicting_application_identity_is_not_deduplicated():
    value = {
        "id": "OBJ-1",
        "kind": "route",
        "source_location": "app/routes.py",
        "semantics": {"path": "/a"},
    }
    with pytest.raises(ValueError):
        ApplicationInventory(
            project_id="owned", objects=[value, value | {"semantics": {"path": "/b"}}]
        )


@pytest.mark.parametrize(
    "mutation", ["inline-value", "remote-reference", "sensitivity", "missing-reference"]
)
def test_credential_alias_is_reference_only_at_contract_boundary(mutation):
    definition = {
        "alias": "users.standard",
        "kind": "credential",
        "environments": ["local"],
        "sensitivity": "SECRET_REFERENCE",
        "reference": "AUTOQA_SECRET_OWNED",
    }
    if mutation == "inline-value":
        definition["values"] = [{"password": "synthetic-private-sentinel"}]
    elif mutation == "remote-reference":
        definition["reference"] = "https://not-allowed.test/credential"
    elif mutation == "sensitivity":
        definition["sensitivity"] = "SYNTHETIC"
    else:
        definition["reference"] = None
    with pytest.raises(ValueError):
        DataInventory(project_id="owned", definitions=[definition])


def test_input_link_and_linked_ancestor_are_refused(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "input.json").write_text(json.dumps({"owned": True}))
    linked = tmp_path / "linked"
    if os.name == "nt":
        import subprocess

        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(linked), str(target)], capture_output=True, text=True
        )
        assert result.returncode == 0, "Owned test junction creation must succeed on Windows"
    else:
        linked.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError):
        checked_root(linked)
    with pytest.raises(ValueError):
        read_json(linked / "input.json")
    assert json.loads((target / "input.json").read_text()) == {"owned": True}


@pytest.mark.parametrize(
    "mutation", ["sensitive-key", "oversized-cell", "nested", "duplicate-environment"]
)
def test_synthetic_aliases_are_bounded_and_cannot_smuggle_sensitive_cells(mutation):
    definition = {
        "alias": "datasets.owned",
        "kind": "value",
        "environments": ["local"],
        "sensitivity": "SYNTHETIC",
        "values": [{"query": "owned"}],
    }
    if mutation == "sensitive-key":
        definition["values"] = [{"AUTHORIZATION": "synthetic-private-sentinel"}]
    elif mutation == "oversized-cell":
        definition["values"] = [{"query": "x" * 501}]
    elif mutation == "nested":
        definition["values"] = [{"query": {"a": {"b": {"c": {"d": {"e": 1}}}}}}]
    else:
        definition["environments"] = ["local", "local"]
    with pytest.raises(ValueError):
        DataInventory(project_id="owned", definitions=[definition])


def test_source_file_count_limit_is_real_and_fail_closed(tmp_path):
    root = tmp_path / "owned"
    root.mkdir()
    for index in range(1001):
        (root / f"file-{index:04}.py").write_bytes(b"# owned\n")
    with pytest.raises(ValueError):
        source_revision(root)
    assert len(list(root.iterdir())) == 1001
