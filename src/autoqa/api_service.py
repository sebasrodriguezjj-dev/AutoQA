"""Declarative API planning through the existing case/receipt workflow."""

import json
from pathlib import Path

from autoqa.authorization import require_authorization
from autoqa.core import TestCase
from autoqa.framework_runtime.contracts import APIScenario
from autoqa.planning import _save_cases, case_signature


def plan_api(project, requirements: Path, authorization):
    require_authorization(authorization, project.root, "plan")
    if requirements.stat().st_size > 1_000_000:
        raise ValueError("API requirements exceed size limit")
    values = json.loads(requirements.read_text(encoding="utf-8"))
    if not isinstance(values, list) or not 1 <= len(values) <= 100:
        raise ValueError("API requirements must contain 1-100 declarative scenarios")
    scenarios = [APIScenario.model_validate(v) for v in values]
    if len({s.id for s in scenarios}) != len(scenarios):
        raise ValueError("Duplicate API scenario IDs")
    old = project.cases() if (project.root / "test-cases/test-matrix.json").exists() else []
    previous = {c.id: c for c in old}
    incoming = []
    for scenario in scenarios:
        if scenario.id in previous and previous[scenario.id].kind != "api":
            raise ValueError("API scenario ID collides with an existing UI scenario")
        env = next(e for e in scenario.environments if e.name == scenario.environment)
        case = TestCase(
            id=scenario.id,
            feature="Reviewed API",
            title=scenario.title,
            description="Declarative API contract; explicit manual review required",
            preconditions=[
                "Authorized test API is available",
                "Reviewed mutation scope and synthetic data",
            ],
            steps=[scenario.request.method + " " + scenario.request.path],
            expected="Reviewed HTTP status, headers and JSON expectations",
            evidence=[],
            kind="api",
            url=env.origin + scenario.request.path,
            test_type=scenario.polarity,
            contract=scenario.model_dump(),
        )
        prior = previous.get(case.id)
        if prior and case_signature(prior) == case_signature(case):
            case.review_status = prior.review_status
        incoming.append(case)
    ids = {c.id for c in incoming}
    cases = [c for c in old if c.id not in ids] + incoming
    _save_cases(project, cases)
    project.audit(f"Planned {len(incoming)} API scenarios; no HTTP requests performed")
    return incoming
