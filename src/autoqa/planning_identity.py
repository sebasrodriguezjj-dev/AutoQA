"""Versioned semantic hashes for bounded, already-validated discovery snapshots.

Only hashes leave this adapter. Legacy IDs, artifacts and receipts are untouched.
Collections are unordered except workflow steps, whose sequence carries meaning.
"""

import hashlib
import json


def _encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _unordered(values):
    return sorted(values, key=_encode)


def _hash(kind, value):
    return hashlib.sha256(
        _encode(["autoqa-planning-identity-v1", kind, value]).encode()
    ).hexdigest()


def _insert(index, identity, value):
    if identity in index and index[identity] != value:
        raise ValueError("Conflicting semantic identity")
    index[identity] = value


def discovery_identity(discovery):
    """Return workflow/evidence hash maps; reject ambiguous identities before use.

    Source bytes and inventory sizes are bounded by the caller. No timestamps,
    screenshot/artifact paths, traversal depth or readiness telemetry are hashed.
    """
    pages, elements, records = {}, {}, {}
    for page in discovery.pages:
        page_elements = []
        for element in page.elements:
            data = element.model_dump(exclude={"discovered_at", "evidence"})
            for key in ("locators", "options", "components"):
                data[key] = _unordered(data[key])
            digest = _hash("element", {"page_url": page.url, "element": data})
            if element.id:
                _insert(elements, element.id, (page.url, digest))
            page_elements.append(digest)
        _insert(
            pages,
            page.url,
            _hash(
                "page",
                {
                    "url": page.url,
                    "title": page.title,
                    "status": page.status,
                    "headings": _unordered(page.headings),
                    "elements": sorted(set(page_elements)),
                },
            ),
        )
    for record in discovery.evidence_records:
        if not record.id:
            continue
        _insert(records, record.id, record.model_dump(exclude={"timestamp", "artifact"}))
    evidence, provenance = {}, {}
    for identity in sorted(records.keys() | elements.keys()):
        record = records.get(identity)
        element = elements.get(identity)
        if (
            record
            and element
            and (
                record["category"] != "OBSERVED"
                or (record["page_url"] and record["page_url"] != element[0])
            )
        ):
            raise ValueError("Conflicting observation association")
        provenance[identity] = record["category"] if record else "OBSERVED"
        evidence[identity] = _hash(
            "evidence",
            {
                "record": record,
                "page": pages.get(record["page_url"]) if record else None,
                "element": element[1] if element else None,
            },
        )
    workflows = {}
    for workflow in discovery.workflows:
        data = workflow.model_dump(exclude={"evidence"})
        for key in ("elements", "element_ids", "preconditions"):
            data[key] = _unordered(data[key])
        data["page_fingerprint"] = pages.get(workflow.page_url)
        data["element_fingerprints"] = {
            identity: elements[identity][1]
            for identity in sorted(set(workflow.element_ids))
            if identity in elements
        }
        _insert(workflows, workflow.id, _hash("workflow", data))
    return workflows, evidence, provenance
