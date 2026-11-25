"""Potential impact over explicit static inventories; never inspect or execute source."""

from autoqa.v08_contracts import (
    ApplicationInventory,
    ImpactFinding,
    ImpactReport,
    digest,
)
from autoqa.v08_io import read_json


def _normalized(inventory):
    value = inventory.model_dump(mode="json")
    for item in value["objects"]:
        for field in ("case_ids", "requirement_ids", "page_objects"):
            if len(set(item[field])) != len(item[field]):
                raise ValueError("Duplicate impact relationship")
            item[field] = sorted(item[field])
    value["objects"].sort(key=lambda item: item["id"])
    return value


class ImpactService:
    """Supplied relationships are attributed hints, not reviewed executable coverage."""

    def __init__(self, project):
        self.project = project

    def compare(self, before, after):
        try:
            left = ApplicationInventory.model_validate(read_json(before))
            right = ApplicationInventory.model_validate(read_json(after))
            project_id = self.project.root.name
            if left.project_id != project_id or right.project_id != project_id:
                raise ValueError("Wrong impact project")
            old, new = _normalized(left), _normalized(right)
            old_by_id = {item["id"]: item for item in old["objects"]}
            new_by_id = {item["id"]: item for item in new["objects"]}
            findings, affected, unchanged = [], set(), set()
            for identity in sorted(old_by_id.keys() | new_by_id.keys()):
                prior, current = old_by_id.get(identity), new_by_id.get(identity)
                if prior == current:
                    unchanged.update(current["case_ids"])
                    continue
                items = [item for item in (prior, current) if item is not None]
                cases = sorted({case for item in items for case in item["case_ids"]})
                affected.update(cases)
                findings.append(
                    ImpactFinding(
                        object_id=identity,
                        kind=current["kind"] if current else prior["kind"],
                        change="ADDED"
                        if prior is None
                        else "REMOVED"
                        if current is None
                        else "CHANGED",
                        source_locations=sorted({item["source_location"] for item in items}),
                        potential_case_ids=cases,
                        requirement_ids=sorted(
                            {ref for item in items for ref in item["requirement_ids"]}
                        ),
                        page_objects=sorted(
                            {ref for item in items for ref in item["page_objects"]}
                        ),
                        rationale="Recorded object meaning or supplied relationships changed; listed impact is potential and requires independent review.",
                    )
                )
            payload = {
                "project_id": project_id,
                "before_digest": digest(["autoqa-impact-inventory-v1", old]),
                "after_digest": digest(["autoqa-impact-inventory-v1", new]),
                "findings": [finding.model_dump() for finding in findings],
                "unaffected_case_ids": sorted(unchanged - affected),
                "unknown_impact": [
                    "Inventory and relationships are explicitly supplied; unlisted objects and cases have unknown impact.",
                    "Static meaning does not prove runtime behavior, complete impact coverage or current reviewed V0.7 mapping validity.",
                    "No scenario, requirement relationship or execution was approved or updated by impact analysis.",
                ],
            }
            return ImpactReport(id="IMP-" + digest(["autoqa-impact-report-v1", payload]), **payload)
        except ValueError, TypeError, KeyError, OSError, RecursionError, OverflowError:
            raise ValueError("Invalid bounded application impact input") from None
