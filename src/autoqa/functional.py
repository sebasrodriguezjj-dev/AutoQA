"""Validated declarative behavior contracts; never accept executable user/model code."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from autoqa.core import Discovery, Element, LocatorCandidate, TestCase


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["fill", "select", "check", "uncheck", "click"]
    element_id: str
    value: str = Field(default="", max_length=500)


class Assertion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check: Literal["texts", "count", "visible", "hidden", "text", "validity", "ordered"]
    element_id: str
    expected: str | int | bool | list[str]
    property: Literal[
        "valid",
        "valueMissing",
        "typeMismatch",
        "tooShort",
        "tooLong",
        "rangeUnderflow",
        "rangeOverflow",
        "patternMismatch",
    ] = "valid"
    descending: bool = False


class BehaviorContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,60}$")
    title: str = Field(min_length=1, max_length=300)
    page_url: str
    workflow: Literal["search", "filter", "sorting", "form", "product"]
    test_type: Literal["Positive", "Negative", "Boundary", "Regression", "End-to-End"]
    basis: Literal["VERIFIED_REQUIREMENT", "OBSERVED"]
    source: str = Field(min_length=5, max_length=2000)
    evidence_ids: list[str] = Field(min_length=1)
    steps: list[Action] = Field(min_length=1, max_length=20)
    assertions: list[Assertion] = Field(min_length=1, max_length=20)
    test_data: dict[str, str] = Field(default_factory=dict)
    allow_submit: bool = False


def locator_expression(candidate: LocatorCandidate) -> str:
    if candidate.strategy == "role":
        name = f", name={candidate.name!r}, exact=True" if candidate.name else ""
        return f"page.get_by_role({candidate.value!r}{name})"
    return (
        f"page.get_by_{candidate.strategy}({candidate.value!r}, exact=True)"
        if candidate.strategy != "test_id"
        else f"page.get_by_test_id({candidate.value!r})"
    )


def candidate_for(element: Element, *, collection: bool = False) -> LocatorCandidate:
    candidates = [c for c in element.locators if c.count > 0 and (collection or c.count == 1)]
    if collection:
        candidates.sort(key=lambda c: c.count == 1)
    if not candidates:
        raise ValueError(
            f"No checked {'collection' if collection else 'unique'} locator for {element.id}."
        )
    return candidates[0]


def validate_contract(
    contract: BehaviorContract, discovery: Discovery, *, local: bool
) -> dict[str, Element]:
    page = next((p for p in discovery.pages if p.url == contract.page_url), None)
    if page is None:
        raise ValueError("Functional contract page has no browser evidence.")
    known = {e.id for e in discovery.evidence_records}
    if not set(contract.evidence_ids) <= known:
        raise ValueError("Contract references unknown evidence IDs.")
    elements = {e.id: e for e in page.elements}
    for step in contract.steps:
        if step.element_id not in elements:
            raise ValueError("Action references an element outside the observed starting page.")
        element = elements[step.element_id]
        if any(
            word in element.name.lower()
            for word in ("password", "api key", "token", "secret", "credential")
        ):
            raise ValueError(
                "Sensitive credential controls are excluded from functional templates."
            )
        candidate_for(element)
        if step.action == "fill" and (
            element.kind not in {"input", "textarea"}
            or element.input_type in {"password", "file", "hidden"}
        ):
            raise ValueError("Unsupported or sensitive field interaction.")
        if step.action == "select" and (
            element.kind != "select" or step.value not in {o["value"] for o in element.options}
        ):
            raise ValueError("Selection value lacks observed option evidence.")
        if step.action in {"check", "uncheck"} and element.input_type not in {"checkbox", "radio"}:
            raise ValueError("Check action requires an observed checkbox or radio.")
        if step.action == "click":
            if element.kind == "a":
                raise ValueError(
                    "Use evidence-based navigation cases for links; functional click is limited to safe controls."
                )
            name = element.name.lower()
            safe_search = "search" in name
            if element.kind != "button" or not (safe_search or (contract.allow_submit and local)):
                raise ValueError(
                    "Button click requires an observed search control or explicit controlled-local submission permission."
                )
        if any(
            word in element.name.lower()
            for word in ("checkout", "purchase", "delete", "sign up", "add to cart")
        ):
            raise ValueError("Potentially dangerous action is excluded.")
    for assertion in contract.assertions:
        if assertion.element_id not in elements:
            raise ValueError("Assertion references an unknown element.")
        candidate_for(
            elements[assertion.element_id],
            collection=assertion.check in {"texts", "count", "ordered"},
        )
        if assertion.check == "texts" and not isinstance(assertion.expected, list):
            raise ValueError("texts requires a list of exact expected strings.")
        if assertion.check == "count" and (
            type(assertion.expected) is not int or assertion.expected < 0
        ):
            raise ValueError("count requires a non-negative integer.")
        if assertion.check == "validity" and (
            type(assertion.expected) is not bool
            or elements[assertion.element_id].kind not in {"input", "select", "textarea"}
        ):
            raise ValueError("Native validity assertions require a field and boolean expectation.")
        if assertion.check == "ordered" and (
            type(assertion.expected) is not int or assertion.expected < 2
        ):
            raise ValueError("Ordering requires an explicit minimum item count of at least two.")
        if assertion.check in {"text", "visible", "hidden"} and not isinstance(
            assertion.expected, str
        ):
            raise ValueError("Text/visibility assertions require an explicit string expectation.")
    if contract.workflow in {"search", "filter", "sorting"} and not any(
        a.check in {"texts", "count", "ordered", "text"} for a in contract.assertions
    ):
        raise ValueError("Functional result scenarios require a behavioral result assertion.")
    return elements


def functional_case(contract: BehaviorContract, discovery: Discovery, *, local: bool) -> TestCase:
    validate_contract(contract, discovery, local=local)
    workflow = next(
        (
            w
            for w in discovery.workflows
            if w.page_url == contract.page_url and w.kind == contract.workflow
        ),
        None,
    )
    return TestCase(
        id="TC-F-" + contract.id,
        feature=contract.workflow.title(),
        title=contract.title,
        description=f"{contract.basis}: {contract.source}",
        preconditions=[
            "Authorized environment available",
            "Behavior contract reviewed and approved",
        ],
        steps=[f"{s.action} {s.element_id}: {s.value}" for s in contract.steps],
        expected="; ".join(
            f"{a.check} {a.element_id} = {a.expected!r}" for a in contract.assertions
        ),
        priority="High" if contract.workflow == "form" else "Medium",
        test_type=contract.test_type,
        evidence=contract.evidence_ids,
        evidence_refs=contract.evidence_ids,
        workflow_id=workflow.id if workflow else None,
        feasible=True,
        kind="functional",
        url=contract.page_url,
        test_data=contract.test_data,
        contract=contract.model_dump(),
    )


def render_functional(case: TestCase, discovery: Discovery, *, local: bool) -> str:
    contract = BehaviorContract.model_validate(case.contract)
    elements = validate_contract(contract, discovery, local=local)
    canonical = functional_case(contract, discovery, local=local)
    if any(
        getattr(case, field) != getattr(canonical, field)
        for field in ("id", "url", "steps", "expected")
    ):
        raise ValueError(
            "Scenario differs from its approved behavior contract; reimport requirements."
        )
    lines = []
    for step in contract.steps:
        locator = locator_expression(candidate_for(elements[step.element_id]))
        method = {"select": "select_option"}.get(step.action, step.action)
        value = repr(step.value) if step.action in {"fill", "select"} else ""
        lines.append(f"    {locator}.{method}({value})")
    for index, assertion in enumerate(contract.assertions):
        locator = locator_expression(
            candidate_for(
                elements[assertion.element_id],
                collection=assertion.check in {"texts", "count", "ordered"},
            )
        )
        message = f"{contract.workflow} result mismatch: {assertion.check} {assertion.element_id}"
        prefix = f"    expect({locator}, {message!r})"
        if assertion.check == "texts":
            lines.append(f"{prefix}.to_have_text({assertion.expected!r})")
        elif assertion.check == "count":
            lines.append(f"{prefix}.to_have_count({assertion.expected!r})")
        elif assertion.check in {"visible", "hidden"}:
            lines.append(f"{prefix}.to_be_{assertion.check}()")
        elif assertion.check == "text":
            lines.append(f"{prefix}.to_have_text({assertion.expected!r})")
        elif assertion.check == "validity":
            lines.append(f"{prefix}.to_be_visible()")
            lines.append(
                f"    assert {locator}.evaluate('(e) => e.validity.{assertion.property}') is {assertion.expected!r}, {message!r}"
            )
        elif assertion.check == "ordered":
            # Wait for the approved size before reading values; then verify numeric order.
            lines += [
                f"{prefix}.to_have_count({assertion.expected!r})",
                f"    values_{index} = {locator}.all_text_contents()",
                f"    numbers_{index} = [float(re.sub(r'[^0-9.-]', '', value)) for value in values_{index}]",
                f"    assert numbers_{index} == sorted(numbers_{index}, reverse={assertion.descending!r}), {message!r}",
            ]
    return "\n".join(lines) + "\n"
