"""Owned synthetic setup for installed V0.8 CLI checks; no browser claim or source execution.

Call prepare(directory) using the isolated installed Python. Returned paths feed the
public maintenance/reconciliation CLI. Real Chromium behavior is tested separately.
"""

import json
import shutil
from pathlib import Path

from autoqa.authorization import AuthorizationContext
from autoqa.core import (
    Discovery,
    Element,
    EvidenceReference,
    LocatorCandidate,
    PageEvidence,
    initialize,
)
from autoqa.framework import FrameworkService
from autoqa.functional import BehaviorContract, functional_case
from autoqa.management import approve_suite, propose
from autoqa.planning import approve, save_cases


def prepare(directory, url="http://127.0.0.1:8123/"):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    project = initialize("synthetic-maintenance", root / "sources")
    intent = AuthorizationContext(project.root, frozenset({"review", "generate"}))
    project.config.application_url = url
    project.config.allow_localhost = True
    project.config.allowed_domains = ["127.0.0.1"]
    project.config.screenshot_policy = "disabled"
    project.config.trace_enabled = False
    project.save_config()
    discovery = Discovery(
        pages=[
            PageEvidence(
                url=url,
                title="Synthetic",
                headings=["Approved result"],
                elements=[
                    Element(
                        id="EL-AMOUNT",
                        kind="input",
                        name="Amount",
                        input_type="number",
                        locators=[
                            LocatorCandidate(strategy="test_id", value="amount-old", count=1)
                        ],
                    ),
                    Element(
                        id="EL-RESULT",
                        kind="h1",
                        name="Approved result",
                        role="heading",
                        locators=[LocatorCandidate(strategy="test_id", value="result", count=1)],
                    ),
                ],
                screenshot="synthetic.png",
                depth=0,
            )
        ],
        evidence_records=[
            EvidenceReference(
                id="EV-PAGE",
                category="OBSERVED",
                description="Synthetic fixture declaration",
                page_url=url,
            )
        ],
    )
    project.storage.write_json("discovery/workflow-map.json", discovery.model_dump())
    contract = BehaviorContract(
        id="AMOUNT",
        title="Synthetic maintained scenario",
        page_url=url,
        workflow="form",
        test_type="Regression",
        basis="OBSERVED",
        source="Owned synthetic fixture specification",
        evidence_ids=["EV-PAGE"],
        steps=[{"action": "fill", "element_id": "EL-AMOUNT", "value": "3"}],
        assertions=[{"check": "text", "element_id": "EL-RESULT", "expected": "Approved result"}],
    )
    case = functional_case(contract, discovery, local=True)
    save_cases(project, [case], authorization=intent)
    approve(project, [case.id], authorization=intent)
    approve_suite(project, propose(project), intent)
    source = root / "managed"
    FrameworkService(project, intent).build(source)
    discovery.pages[0].elements[0].locators = [
        LocatorCandidate(strategy="test_id", value="amount-new", count=1)
    ]
    project.storage.write_json("discovery/workflow-map.json", discovery.model_dump())
    manual = root / "manual"
    shutil.copytree(source, manual)
    page = next((manual / "pages").glob("page_*.py"))
    page.write_text(
        page.read_text(encoding="utf-8").replace("amount-old", "amount-new"), encoding="utf-8"
    )
    locator = root / "locator.json"
    locator.write_text(
        json.dumps({"strategy": "test_id", "value": "amount-new", "count": 1}), encoding="utf-8"
    )
    return {
        "project": str(project.root),
        "source": str(source),
        "manual_source": str(manual),
        "case_id": case.id,
        "element_id": "EL-AMOUNT",
        "locator": str(locator),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.directory)))
