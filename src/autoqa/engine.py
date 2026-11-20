"""Reusable generation and execution services over the local AutoQA adapters.

The services keep authorization and project identity below interface code. The
legacy functions in :mod:`autoqa.testing` remain the compatibility facade.
"""

from pathlib import Path

from autoqa import testing
from autoqa.authorization import AuthorizationContext
from autoqa.core import Project


class GenerationService:
    """Generate a reviewed suite through the trusted renderer and validators."""

    def __init__(self, project: Project, authorization: AuthorizationContext | None):
        self.project = project
        self.authorization = authorization

    def generate(self) -> list[str]:
        return testing.generate(self.project, authorization=self.authorization)


class ExecutionService:
    """Collect, execute and persist a run through the trusted local runner."""

    def __init__(self, project: Project, authorization: AuthorizationContext | None):
        self.project = project
        self.authorization = authorization

    def run(self) -> dict:
        return testing.run(self.project, authorization=self.authorization)


class JUnitIngestionService:
    """Parse JUnit without inventing missing test or step outcomes."""

    @staticmethod
    def ingest(path: Path) -> list[dict]:
        return testing.parse_junit(path)
