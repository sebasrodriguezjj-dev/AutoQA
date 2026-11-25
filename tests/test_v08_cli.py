"""V0.8 CLI preserves intent, bounded output and payload suppression."""

import json
from types import SimpleNamespace

from typer.testing import CliRunner

from autoqa import v08_cli
from autoqa.cli import app


def test_missing_apply_intent_does_not_read_or_select_source(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Unauthorized command performed IO")

    monkeypatch.setattr(v08_cli, "engine", forbidden)
    monkeypatch.setattr(v08_cli, "read_json", forbidden)
    result = CliRunner().invoke(app, ["maintenance", "apply", "PRIVATE-PATH", "PRIVATE-INPUT"])
    assert result.exit_code == 1
    assert "PRIVATE" not in result.stdout
    assert json.loads(result.stdout).keys() == {"error"}


def test_data_binding_intent_is_explicit_and_never_execution(monkeypatch):
    calls = []

    def selected(project, *operations):
        calls.append(operations)
        return SimpleNamespace(bind_test_data=lambda *args: {"arguments": args})

    monkeypatch.setattr(v08_cli, "engine", selected)
    runner = CliRunner()
    args = ["test-data", "bind", "datasets.synthetic", "TC-OWNED", "--environment", "local"]
    refused = runner.invoke(app, args)
    assert refused.exit_code == 1 and calls == []
    bound = runner.invoke(app, [*args, "--authorized"])
    assert bound.exit_code == 0
    assert calls == [("maintain", "review")]
    assert json.loads(bound.stdout)["arguments"] == ["datasets.synthetic", "TC-OWNED", "local"]


def test_invalid_source_error_never_echoes_payload(monkeypatch):
    def unavailable(*args, **kwargs):
        raise ValueError("private-source-and-sensitive-output-sentinel")

    monkeypatch.setattr(v08_cli, "engine", unavailable)
    result = CliRunner().invoke(app, ["diagnose-run", "private-run.json"])
    assert result.exit_code == 1
    assert "sentinel" not in result.stdout
    assert "private-run" not in result.stdout
    assert "error" in json.loads(result.stdout)


def test_excessive_output_is_refused_without_partial_payload(monkeypatch):
    monkeypatch.setattr(
        v08_cli,
        "engine",
        lambda *args: SimpleNamespace(diagnose_run=lambda _: {"payload": "x" * 2_000_000}),
    )
    result = CliRunner().invoke(app, ["diagnose-run", "synthetic.json"])
    assert result.exit_code == 1
    assert len(result.stdout) < 200
    assert "payload" not in result.stdout
