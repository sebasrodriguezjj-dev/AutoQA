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

    def plan_api(self, requirements: Path):
        from autoqa.api_service import plan_api

        return plan_api(self.project, requirements, self.authorization)

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

    def build_framework(self, destination: Path):
        from autoqa.framework import FrameworkService

        return FrameworkService(self.project, self.authorization).build(destination)

    def run_framework(self, destination: Path, selection=None):
        from autoqa.framework import FrameworkService

        return FrameworkService(self.project, self.authorization).run(destination, selection)

    def intelligent_plan(self, requirements: Path | None = None):
        from autoqa.intelligent_planning_service import IntelligentPlanningService

        return IntelligentPlanningService(self.project, self.authorization).analyze(requirements)

    def import_requirements(self, path: Path):
        from autoqa.intelligent_planning_service import IntelligentPlanningService

        return IntelligentPlanningService(self.project, self.authorization).import_requirements(
            path
        )

    def review_plan(self, plan_id: str, proposal_ids: list[str], decision: str):
        from autoqa.intelligent_planning_service import IntelligentPlanningService

        return IntelligentPlanningService(self.project, self.authorization).review(
            plan_id, proposal_ids, decision
        )

    def coverage_report(self, requirements: Path | None = None):
        snapshot = self.intelligent_plan(requirements)
        return snapshot.model_dump(
            mode="json",
            include={
                "schema_version",
                "id",
                "project_id",
                "input_digest",
                "coverage_scope",
                "execution_coverage",
                "summary",
                "findings",
                "context",
                "review_state",
                "limitations",
            },
        )


class InProcessAdapter:
    """Test adapter exposing the same operations as an interface adapter."""

    def __init__(self, engine: ApplicationEngine):
        self.engine = engine

    def __getattr__(self, name: str):
        return getattr(self.engine, name)
