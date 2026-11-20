"""Authorized orchestration of existing browser and repository adapters."""

from dataclasses import dataclass
from pathlib import Path

from autoqa import exploration, repository
from autoqa.authorization import AuthorizationContext, require_authorization
from autoqa.core import Discovery, Project


@dataclass
class DiscoveryResult:
    findings: dict | None = None
    discovery: Discovery | None = None
    correlation: dict | None = None


class DiscoveryService:
    def __init__(self, project: Project, authorization: AuthorizationContext | None):
        self.project = project
        self.authorization = authorization

    def discover(
        self, *, url: str | None = None, repo: Path | None = None, allow_localhost: bool = False
    ) -> DiscoveryResult:
        require_authorization(self.authorization, self.project.root, "discover")
        if not url and not repo:
            raise ValueError("Provide --url and/or --repo.")
        if self.project.config.auth_reference:
            raise ValueError("Authenticated exploration is not implemented in v0.1.")
        if allow_localhost:
            self.project.config.allow_localhost = True
        self.project.config.mode = "hybrid" if url and repo else "ui" if url else "repository"
        result = DiscoveryResult()
        if repo:
            result.findings = repository.analyze(
                self.project, repo, authorization=self.authorization
            )
            if not url:
                repository.source_discovery(
                    self.project, result.findings, authorization=self.authorization
                )
        if url:
            result.discovery = exploration.explore(
                self.project, url, authorization=self.authorization
            )
            if not result.discovery.pages:
                return result
            if repo:
                result.correlation = repository.correlate(
                    self.project, result.discovery, authorization=self.authorization
                )
        self.project.save_config()
        return result
