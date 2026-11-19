"""Owned demo requirements, resolved against real discovery; never imported by the generator."""

from autoqa.core import Discovery


def reviewed_contracts(discovery: Discovery) -> list[dict]:
    inventory = next(p for p in discovery.pages if p.url.endswith("/inventory"))
    form = next(p for p in discovery.pages if p.url.endswith("/request"))

    def element(page, name=None, test_id=None):
        return next(
            e.id
            for e in page.elements
            if (name is None or e.name == name)
            and (test_id is None or e.attributes.get("data-testid") == test_id)
        )

    query = element(inventory, "Find supplies")
    names = element(inventory, test_id="stock-name")
    prices = element(inventory, test_id="stock-price")
    empty = element(inventory, test_id="stock-empty")
    category = element(inventory, "Category filter")
    ordering = element(inventory, "Sort by price")
    email = element(form, "Work email")
    person = element(form, "Contact name")
    quantity = element(form, "Sample quantity")
    submit = element(form, "Validate sample request")
    status = element(form, test_id="request-status")

    def contract(id, title, workflow, test_type, page, steps, assertions, **kwargs):
        refs = sorted({s["element_id"] for s in steps + assertions})
        return {
            "id": id,
            "title": title,
            "workflow": workflow,
            "test_type": test_type,
            "page_url": page.url,
            "basis": "VERIFIED_REQUIREMENT",
            "source": "Owned Supply Lab fixture requirements, independently reviewed against deterministic SUPPLIES and native HTML constraints; not inferred from public content.",
            "evidence_ids": refs,
            "steps": steps,
            "assertions": assertions,
            **kwargs,
        }

    def fill(id, value):
        return {"action": "fill", "element_id": id, "value": value}

    def select(id, value):
        return {"action": "select", "element_id": id, "value": value}

    def texts(values):
        return {"check": "texts", "element_id": names, "expected": values}

    def validity(id, property, expected):
        return {
            "check": "validity",
            "element_id": id,
            "property": property,
            "expected": expected,
        }

    return [
        contract(
            "search-found",
            "Search returns the approved matching supply",
            "search",
            "Positive",
            inventory,
            [fill(query, "Moss")],
            [texts(["Moss Journal"])],
        ),
        contract(
            "search-empty",
            "Unknown supply query produces the approved empty state",
            "search",
            "Negative",
            inventory,
            [fill(query, "unlisted-fixture-904")],
            [
                {"check": "count", "element_id": names, "expected": 0},
                {"check": "visible", "element_id": empty, "expected": "No supplies match"},
                {"check": "text", "element_id": empty, "expected": "No supplies match"},
            ],
        ),
        contract(
            "filter-writing",
            "Writing category contains exactly the two fixture supplies",
            "filter",
            "Positive",
            inventory,
            [select(category, "Writing")],
            [texts(["Cedar Pencil", "Slate Marker"])],
        ),
        contract(
            "sort-low",
            "Price ordering is ascending across all approved supplies",
            "sorting",
            "Positive",
            inventory,
            [select(ordering, "low")],
            [
                {"check": "ordered", "element_id": prices, "expected": 3},
                texts(["Cedar Pencil", "Slate Marker", "Moss Journal"]),
            ],
        ),
        contract(
            "email-missing",
            "Empty required email has native valueMissing",
            "form",
            "Negative",
            form,
            [fill(email, "")],
            [validity(email, "valueMissing", True)],
        ),
        contract(
            "email-invalid",
            "Malformed email has native typeMismatch",
            "form",
            "Negative",
            form,
            [fill(email, "not-an-email")],
            [validity(email, "typeMismatch", True)],
        ),
        contract(
            "quantity-boundary",
            "Quantity below the published minimum is invalid",
            "form",
            "Boundary",
            form,
            [fill(quantity, "0")],
            [validity(quantity, "rangeUnderflow", True)],
        ),
        contract(
            "form-valid",
            "Valid local sample data produces the fixture success response",
            "form",
            "Positive",
            form,
            [
                fill(person, "Sample QA"),
                fill(email, "qa@example.test"),
                fill(quantity, "2"),
                {"action": "click", "element_id": submit},
            ],
            [{"check": "text", "element_id": status, "expected": "Sample request validated"}],
            allow_submit=True,
            test_data={"person": "Sample QA", "email": "qa@example.test", "quantity": "2"},
        ),
    ]
