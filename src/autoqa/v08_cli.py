"""JSON-only V0.8 adapters; errors never echo inspected source or sensitive payloads."""

from functools import wraps
from pathlib import Path
from typing import Annotated

import typer

from autoqa.application import ApplicationEngine
from autoqa.authorization import AuthorizationContext
from autoqa.core import select_project
from autoqa.v08_contracts import LocatorSpec, MaintenanceProposal, canonical
from autoqa.v08_io import read_json


def bounded_command(function):
    @wraps(function)
    def invoke(*args, **kwargs):
        try:
            value = function(*args, **kwargs)
            output = canonical(value)
            if len(output.encode("utf-8")) > 2_000_000:
                raise ValueError("Output exceeds bounds")
            typer.echo(output)
        except ValueError, OSError, TypeError, KeyError, RecursionError, OverflowError:
            typer.echo(
                '{"error":"Invalid or unavailable V0.8 input, authorization or current binding"}'
            )
            raise typer.Exit(1) from None

    return invoke


def engine(project, *operations):
    selected = select_project(project)
    context = AuthorizationContext(selected.root, frozenset(operations)) if operations else None
    return ApplicationEngine(selected, context)


def register(app):
    data = typer.Typer(
        no_args_is_help=True, help="Bounded synthetic test data and environment references."
    )
    maintenance = typer.Typer(
        no_args_is_help=True, help="Reviewed declarative repairs; never execute edited source."
    )
    app.add_typer(data, name="test-data")
    app.add_typer(maintenance, name="maintenance")

    @app.command("diagnose-run")
    @bounded_command
    def diagnose_run(run_file: Path, project: Path | None = None):
        """Read recorded scope and historical evidence; no root-cause guarantee."""
        return engine(project).diagnose_run(run_file)

    @app.command("impact-review")
    @bounded_command
    def impact_review(before_file: Path, after_file: Path, project: Path | None = None):
        """Compare supplied static inventory snapshots; potential impact only."""
        return engine(project).impact_review(before_file, after_file)

    @app.command("reconcile-source")
    @bounded_command
    def reconcile_source(baseline: Path, current: Path, project: Path | None = None):
        """Read-only managed/manual revision comparison, without collection/import."""
        return engine(project).reconcile_source(baseline, current)

    @data.command("inspect")
    @bounded_command
    def inspect_data(input: Path | None = None, project: Path | None = None):
        """Inspect bounded data definitions; never resolve credential values."""
        return engine(project).inspect_test_data(input)

    @data.command("import")
    @bounded_command
    def import_data(
        file: Path,
        root: Annotated[list[Path] | None, typer.Option("--root")] = None,
        project: Path | None = None,
    ):
        """Explicitly import definitions and bind authorized local file roots."""
        return engine(project, "plan").import_test_data(file, tuple(root or []))

    @data.command("validate")
    @bounded_command
    def validate_data(
        alias: str,
        environment: Annotated[str, typer.Option("--environment")],
        project: Path | None = None,
    ):
        """Validate a current alias/reference without secret resolution."""
        return engine(project).validate_test_data(alias, environment)

    @data.command("bind")
    @bounded_command
    def bind_data(
        alias: str,
        case_id: str,
        environment: Annotated[str, typer.Option("--environment")],
        authorized: bool = False,
        project: Path | None = None,
    ):
        """Create a pending case revision; existing scenario review remains required."""
        if not authorized:
            raise ValueError("Explicit maintenance authorization required")
        return engine(project, "maintain", "review").bind_test_data(alias, case_id, environment)

    @maintenance.command("propose")
    @bounded_command
    def propose(
        source: Path,
        case_id: str,
        element_id: str,
        locator_json: Path,
        manual_source: Path | None = None,
        project: Path | None = None,
    ):
        """Propose an observed unique locator change; no source writes or approval."""
        locator = LocatorSpec.model_validate(read_json(locator_json))
        return engine(project).propose_maintenance(
            source, case_id, element_id, locator, manual_source
        )

    @maintenance.command("review")
    @bounded_command
    def review(
        source: Path,
        proposal_json: Path,
        decision: Annotated[str, typer.Option("--decision")],
        manual_source: Path | None = None,
        project: Path | None = None,
    ):
        """Record only exact-proposal disposition; acceptance cannot apply a repair."""
        proposal = MaintenanceProposal.model_validate(read_json(proposal_json))
        return engine(project, "review").review_maintenance(
            source, proposal, decision, manual_source
        )

    @maintenance.command("apply")
    @bounded_command
    def apply(
        source: Path,
        proposal_json: Path,
        authorized: bool = False,
        manual_source: Path | None = None,
        project: Path | None = None,
    ):
        """Apply an accepted current declarative revision as pending, never Python."""
        if not authorized:
            raise ValueError("Explicit maintenance authorization required")
        proposal = MaintenanceProposal.model_validate(read_json(proposal_json))
        return engine(project, "maintain", "review").apply_maintenance(
            source, proposal, manual_source
        )
