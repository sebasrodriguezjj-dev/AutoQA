"""Pure diagnostic classification and evidence-aware projection."""

from dataclasses import dataclass

from autoqa.domain import artifact_reference


@dataclass(frozen=True)
class Classification:
    category: str
    advice: str
    failure_class: str


def classify_failure(record: dict, case: dict) -> Classification:
    category = "Unknown"
    advice = "Review the trace and application logs; reproduce manually."
    failure_class = "UNKNOWN"
    for fragment, label, recommendation in [
        (
            "net::",
            "Navigation failure",
            "Verify availability, DNS and authorized network scope.",
        ),
        (
            "strict mode violation",
            "Locator failure",
            "Inspect locator ambiguity against the recorded DOM.",
        ),
        (
            "timeout",
            "Timeout",
            "Review the trace for missing elements, slow UI or environment delays.",
        ),
        (
            "assert",
            "Assertion failure",
            "Compare the approved expectation with UI evidence; investigate a possible application defect or stale baseline.",
        ),
        (
            "no junit",
            "Environment issue",
            "Inspect pytest.log for collection errors or interrupted execution.",
        ),
    ]:
        if fragment in record["error"].lower():
            category, advice = label, recommendation
            break
    error = record["error"].lower()
    if "strict mode violation" in error:
        category, failure_class = "Locator ambiguity", "TEST AUTOMATION FAILURE"
    elif any(
        fragment in error
        for fragment in (
            "net::",
            "browser has been closed",
            "executable doesn't exist",
            "no junit",
        )
    ):
        failure_class = "ENVIRONMENT FAILURE"
    elif "to_have_url" in error:
        category = "Unexpected navigation"
    elif case.get("kind") == "functional" and "result mismatch" in error:
        workflow = case.get("contract", {}).get("workflow")
        category = {
            "search": "Search result mismatch",
            "filter": "Filter result mismatch",
            "sorting": "Sorting mismatch",
            "form": "Form validation failure",
        }.get(workflow, "Assertion mismatch")
        failure_class = "APPLICATION DEFECT CANDIDATE"
        advice = "Compare approved contract and captured results; reproduce manually before confirming a product defect."
    elif "waiting for locator" in error:
        category, failure_class = "Locator not found", "TEST AUTOMATION FAILURE"
    return Classification(category, advice, failure_class)


def diagnostic_evidence_references(result: dict, record: dict) -> list[str]:
    """Project legacy and recorded step evidence within this run and test only."""
    root = artifact_reference(result["artifact_dir"])
    references = [
        root + "/pytest.log",
        root + "/" + record["name"] + ".zip",
        root + "/" + record["name"] + ".png",
    ]
    for step in result.get("step_results", []):
        if (
            step.get("test_id") != record["id"]
            or step.get("run_id", result["run_id"]) != result["run_id"]
        ):
            continue
        for name in step.get("evidence", []):
            # Generated step references are run-local filenames, never project paths.
            if not isinstance(name, str) or "/" in name or not name.endswith((".png", ".zip")):
                continue
            try:
                artifact_reference(name)
            except ValueError:
                continue
            references.append(root + "/" + name)
    return list(dict.fromkeys(references))


def project_diagnostics(result: dict, cases: dict, available_artifacts: set[str]) -> list[dict]:
    findings = []
    for record in result["records"]:
        if record["status"] not in {"FAILED", "ERROR", "NOT_EXECUTED"}:
            continue
        classified = classify_failure(record, cases.get(record["id"], {}))
        category, advice, failure_class = (
            classified.category,
            classified.advice,
            classified.failure_class,
        )
        case = cases.get(record["id"], {})
        findings.append(
            {
                "test_id": record["id"],
                "category": category,
                "observed_error": record["error"],
                "evidence": [
                    path
                    for path in diagnostic_evidence_references(result, record)
                    if path in available_artifacts
                ],
                "possible_cause": category + "; root cause is not established",
                "confidence": "low",
                "recommendation": advice,
                "human_review_required": True,
                "failure_class": failure_class,
                "expected_behavior": case.get("expected", "Unknown; no matching scenario snapshot"),
                "observed_behavior": record["error"] or record["status"],
            }
        )
    return findings
