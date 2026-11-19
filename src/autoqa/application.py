"""Shared in-process application engine used by the CLI and future adapters."""

from pathlib import Path

from autoqa.authorization import AuthorizationContext
from autoqa.core import Project
from autoqa.discovery_service import DiscoveryResult, DiscoveryService
from autoqa.engine import ExecutionService, GenerationService
from autoqa.planning_service import PlanningService
from autoqa.reporting import diagnose, report


class ApplicationEngine:
    """Compose project-bound use cases without a web server or CLI dependency."""

    def __init__(self, project: Project, authorization: AuthorizationContext | None = None):
        self.project = project
        self.authorization = authorization

    def discovery(
        self, *, url: str | None = None, repo: Path | None = None, allow_localhost: bool = False
    ) -> DiscoveryResult:
        return DiscoveryService(self.project, self.authorization).discover(
            url=url, repo=repo, allow_localhost=allow_localhost
        )

    def plan(self, requirements: Path | None = None):
        return PlanningService(self.project, self.authorization).plan(requirements)

    planning = plan

    def approve(self, ids: list[str]):
        return PlanningService(self.project, self.authorization).approve(ids)

    def reject(self, ids: list[str]):
        return PlanningService(self.project, self.authorization).reject(ids)

    def generate(self) -> list[str]:
        return GenerationService(self.project, self.authorization).generate()

    generation = generate

    def run(self) -> dict:
        return ExecutionService(self.project, self.authorization).run()

    execution = run

    def diagnose(self) -> list[dict]:
        return diagnose(self.project)

    diagnostics = diagnose

    def report(self, format: str = "html") -> str:
        return report(self.project, format)

    reporting = report


class InProcessAdapter:
    """Test adapter exposing the same operations as an interface adapter."""

    def __init__(self, engine: ApplicationEngine):
        self.engine = engine

    def __getattr__(self, name: str):
        return getattr(self.engine, name)
