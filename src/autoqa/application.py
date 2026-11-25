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

    def diagnose_run(self, run_file: Path):
        from autoqa.v08_diagnosis import DiagnosisService

        return DiagnosisService(self.project).analyze(run_file)

    def impact_review(self, before: Path, after: Path):
        from autoqa.v08_impact import ImpactService

        return ImpactService(self.project).compare(before, after)

    def inspect_test_data(self, input_path: Path | None = None):
        from autoqa.v08_data import TestDataService

        return TestDataService(self.project, self.authorization).inspect(input_path)

    def import_test_data(self, path: Path, authorized_roots=()):
        from autoqa.v08_data import TestDataService

        return TestDataService(self.project, self.authorization).import_inventory(
            path, authorized_roots
        )

    def validate_test_data(self, alias: str, environment: str):
        from autoqa.v08_data import TestDataService

        return TestDataService(self.project, self.authorization).validate_alias(alias, environment)

    def bind_test_data(self, alias: str, case_id: str, environment: str):
        from autoqa.v08_data import TestDataService

        return TestDataService(self.project, self.authorization).bind_case(
            alias, case_id, environment
        )

    def propose_maintenance(
        self, source: Path, case_id: str, element_id: str, locator, manual_source=None
    ):
        from autoqa.v08_maintenance import MaintenanceService

        return MaintenanceService(self.project, self.authorization).propose(
            source, case_id, element_id, locator, manual_source
        )

    def review_maintenance(self, source: Path, proposal, decision: str, manual_source=None):
        from autoqa.v08_maintenance import MaintenanceService

        return MaintenanceService(self.project, self.authorization).review(
            source, proposal, decision, manual_source
        )

    def apply_maintenance(self, source: Path, proposal, manual_source=None):
        from autoqa.v08_maintenance import MaintenanceService

        return MaintenanceService(self.project, self.authorization).apply(
            source, proposal, manual_source
        )

    def reconcile_source(self, baseline: Path, current: Path):
        from autoqa.v08_reconciliation import ReconciliationService

        return ReconciliationService(self.project).inspect(baseline, current)


class InProcessAdapter:
    """Test adapter exposing the same operations as an interface adapter."""

    def __init__(self, engine: ApplicationEngine):
        self.engine = engine

    def __getattr__(self, name: str):
        return getattr(self.engine, name)
