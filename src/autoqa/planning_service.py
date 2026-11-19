"""In-process planning, review and generation use cases."""

from pathlib import Path

from autoqa import planning, testing
from autoqa.authorization import AuthorizationContext
from autoqa.core import Project, TestCase


class PlanningService:
    def __init__(self, project: Project, authorization: AuthorizationContext | None):
        self.project = project
        self.authorization = authorization

    def plan(self, requirements: Path | None = None) -> list[TestCase]:
        return planning.plan(self.project, requirements, authorization=self.authorization)

    def approve(self, ids: list[str]) -> list[TestCase]:
        return planning.approve(self.project, ids, authorization=self.authorization)

    def reject(self, ids: list[str]) -> list[TestCase]:
        return planning.reject(self.project, ids, authorization=self.authorization)

    @staticmethod
    def verify_signature(case: TestCase, signature: str) -> bool:
        return planning.case_signature(case) == signature

    def generate(self) -> list[str]:
        return testing.generate(self.project, authorization=self.authorization)
