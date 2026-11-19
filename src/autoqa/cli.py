"""Thin CLI; business logic lives in focused modules."""

from functools import wraps
from pathlib import Path

import typer
from playwright.sync_api import Error as BrowserError
from rich.console import Console
from rich.table import Table

from autoqa import __version__
from autoqa.authorization import AuthorizationContext
from autoqa.core import initialize, select_project

app = typer.Typer(
    no_args_is_help=True, help=f"AutoQA Agent {__version__}: evidence-driven QA automation."
)
console = Console()


def handled(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except KeyboardInterrupt:
            console.print("Interrupted. Completed artifacts remain available.", style="yellow")
            raise typer.Exit(130) from None
        except (ValueError, OSError, BrowserError) as error:
            console.print(str(error), style="red", markup=False)
            raise typer.Exit(1) from None

    return wrapper


@app.command()
@handled
def init(name: str, parent: Path = Path("projects")):
    """Create an isolated project without overwriting existing work."""
    project = initialize(name, parent)
    console.print(f"Created {project.root}\nNext: autoqa explore --url URL --authorized")


@app.command()
@handled
def demo(host: str = "127.0.0.1", port: int = 8000, variant: str = "original"):
    """Start the included owned demonstration application."""
    from autoqa.demo import serve

    console.print(f"Demo: http://{host}:{port} (Ctrl+C to stop)")
    if variant == "independent":
        from autoqa.independent_demo import serve as independent_serve

        independent_serve(host, port)
    elif variant == "original":
        serve(host, port)
    else:
        raise ValueError("Demo variant must be original or independent.")


@app.command()
@handled
def explore(
    url: str | None = None,
    repo: Path | None = None,
    project: Path | None = None,
    authorized: bool = False,
    allow_localhost: bool = False,
):
    """Explore an authorized URL and/or statically inspect a local repository."""
    from autoqa.discovery_service import DiscoveryService

    selected = select_project(project)
    if not url and not repo:
        raise ValueError("Provide --url and/or --repo.")
    if not authorized:
        raise ValueError("Confirm your testing authorization using --authorized.")
    service = DiscoveryService(
        selected, AuthorizationContext(selected.root, frozenset({"discover"}))
    )
    result = service.discover(url=url, repo=repo, allow_localhost=allow_localhost)
    if result.findings is not None:
        findings = result.findings
        console.print(
            f"Inspected {findings['files_scanned']} files; {len(findings['routes'])} route candidates (SOURCE evidence)."
        )
    if result.discovery is not None:
        discovery = result.discovery
        console.print(
            f"Pages: {len(discovery.pages)}; workflows: {len(discovery.workflows)}; elements: {sum(len(p.elements) for p in discovery.pages)}; errors: {len(discovery.errors)}"
        )
    if result.discovery is not None and not result.discovery.pages:
        raise ValueError("No pages were observed. Inspect discovery/summary.md.")
    if result.correlation is not None:
        console.print(
            f"Matched {len(result.correlation['matches'])} browser paths to source route candidates."
        )
    console.print(
        "Evidence saved in discovery/. Next: autoqa plan (offline deterministic planning)."
    )


@app.command()
@handled
def plan(
    project: Path | None = None,
    approve: list[str] = typer.Option(None, "--approve"),
    reject: list[str] = typer.Option(None, "--reject"),
    requirements: Path | None = typer.Option(
        None, help="Import reviewed declarative behavior contracts; no executable code."
    ),
    ai: bool = typer.Option(
        False, help="Send reduced workflow evidence to cloud AI for review-only recommendations."
    ),
):
    """Build a test matrix or approve selected IDs after reviewing it."""
    from autoqa.planning_service import PlanningService

    selected = select_project(project)
    if sum(bool(x) for x in (approve, reject, requirements)) > 1:
        raise ValueError("Import requirements, approve, or reject in separate commands.")
    if ai and (approve or reject):
        raise ValueError("Request AI suggestions separately from approving scenarios.")
    service = PlanningService(
        selected, AuthorizationContext(selected.root, frozenset({"plan", "review"}))
    )
    cases = (
        service.approve(approve)
        if approve
        else service.reject(reject)
        if reject
        else service.plan(requirements)
    )
    table = Table("ID", "Scenario", "Automatable", "Review")
    for case in cases:
        table.add_row(case.id, case.title, str(case.feasible), case.review_status)
    console.print(table)
    console.print("Matrix: test-cases/test-matrix.md. Deterministic planning complete.")
    if ai:
        from autoqa.llm import recommend

        result = recommend(selected)
        console.print(f"Saved {len(result.suggestions)} review-only AI recommendations.")
    else:
        console.print("No AI provider contacted. Optional cloud recommendations: plan --ai.")


@app.command()
@handled
def generate(project: Path | None = None, approved: bool = False):
    """Generate executable tests exclusively from approved observations."""
    from autoqa.testing import generate as generate_tests

    if not approved:
        raise ValueError("Use --approved; only reviewed scenarios can become tests.")
    selected = select_project(project)
    ids = generate_tests(
        selected, authorization=AuthorizationContext(selected.root, frozenset({"generate"}))
    )
    console.print(f"Generated {len(ids)} tests in automation/.")


@app.command()
@handled
def run(project: Path | None = None):
    """Execute the approved template suite and retain real results."""
    from autoqa.engine import ExecutionService

    with console.status("Running approved Playwright tests..."):
        selected = select_project(project)
        result = ExecutionService(
            selected, AuthorizationContext(selected.root, frozenset({"execute"}))
        ).run()
    console.print(
        f"Run {result['run_id']}: exit {result['exit_code']}. Results: reports/latest-run.json"
    )
    if result["exit_code"]:
        raise typer.Exit(result["exit_code"])


@app.command()
@handled
def diagnose(project: Path | None = None):
    """Classify actual failures with explicit uncertainty."""
    from autoqa.reporting import diagnose as analyze

    findings = analyze(select_project(project))
    console.print(f"Recorded {len(findings)} failure diagnoses in reports/diagnosis.json.")


@app.command()
@handled
def report(project: Path | None = None, format: str = "html"):
    """Render an escaped HTML or JSON report from actual project records."""
    from autoqa.reporting import report as render

    console.print(render(select_project(project), format))


@app.command()
@handled
def integrate(project: Path | None = None, provider: str = "github"):
    """Generate a reviewable GitHub workflow locally; never push it."""
    from autoqa.integration import integrate as create

    if provider != "github":
        raise ValueError("Only the github provider is implemented.")
    console.print(create(select_project(project)))
