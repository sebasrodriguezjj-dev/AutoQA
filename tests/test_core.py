import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from autoqa.cli import app
from autoqa.core import Config, Project, initialize, select_project
from autoqa.security import Scope, canonical


@pytest.mark.parametrize("name", ["../escape", "", "a/b", "a\\b", "CON", "NUL", "LPT1", "x" * 65])
def test_invalid_project_names(tmp_path, name):
    with pytest.raises(ValueError):
        initialize(name, tmp_path)
    assert not (tmp_path.parent / "escape").exists()


def test_isolation_and_existing_project(project):
    second = initialize("client-b", project.root.parent)
    (project.root / "artifacts/evidence.txt").write_text("client A")
    assert not (second.root / "artifacts/evidence.txt").exists()
    with pytest.raises(FileExistsError):
        initialize("client-a", project.root.parent)
    assert Project(project.root).config.name == "client-a"


def test_config_constraints_and_roundtrip(project):
    with pytest.raises(ValidationError):
        Config(name="x", max_pages=0)
    with pytest.raises(ValidationError):
        Config(name="x", unknown=True)
    project.config.max_depth = 1
    project.save_config()
    assert Project(project.root).config.max_depth == 1


def test_project_selection(project, monkeypatch):
    monkeypatch.chdir(project.root)
    assert select_project(None).root == project.root
    monkeypatch.chdir(project.root.parent.parent)
    assert select_project(None).root == project.root


def test_no_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="No active"):
        select_project(None)
    result = CliRunner().invoke(app, ["plan"])
    assert result.exit_code == 1


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com",
        "http://u:p@localhost",
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://169.254.169.254",
        "http://[::1]",
        "http://localhost/?token=secret",
    ],
)
def test_unsafe_urls(url):
    with pytest.raises(ValueError):
        Scope(url, Config(name="x"))


def test_local_scope_and_origin():
    scope = Scope("http://127.0.0.1:8000", Config(name="x", allow_localhost=True))
    assert scope.allows("http://127.0.0.1:8000/products")
    assert not scope.allows("http://127.0.0.1:8001/products")
    assert not scope.allows("http://10.0.0.1/")
    assert not scope.allows("https://example.com/")
    assert not scope.allows("http://127.0.0.1:8000/logout")
    assert not scope.allows("http://127.0.0.1:8000/%256cogout")
    assert not scope.allows("http://127.0.0.1:8000/?q=x")
    assert canonical("http://localhost#section") == "http://localhost/"


def test_explicit_scope_path_exclusions():
    scope = Scope(
        "http://127.0.0.1:8000",
        Config(name="x", allow_localhost=True, excluded_paths=["/account", "/auth"]),
    )
    assert not scope.allows("http://127.0.0.1:8000/account/profile")
    assert not scope.allows("http://127.0.0.1:8000/%61uth/login")
    assert scope.allows("http://127.0.0.1:8000/products")


def test_dns_private_rebinding_rejected(monkeypatch):
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("10.0.0.1", 80))])
    with pytest.raises(ValueError, match="Non-public"):
        Scope("https://example.com", Config(name="x"))


def test_authorization_required(project):
    result = CliRunner().invoke(
        app, ["explore", "--project", str(project.root), "--url", "http://127.0.0.1"]
    )
    assert result.exit_code == 1
    assert "--authorized" in result.output


def test_cli_help():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "explore" in result.output
