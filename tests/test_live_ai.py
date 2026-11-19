"""Live access is deliberately opt-in; normal tests never contact a model provider."""

import importlib.util
import os

import pytest

from autoqa.llm import OpenAIProvider


@pytest.mark.skipif(
    os.environ.get("AUTOQA_LIVE_AI") != "1",
    reason="Set AUTOQA_LIVE_AI=1 to opt in to the synthetic-evidence API smoke test",
)
def test_optional_live_structured_ai():
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("AUTOQA_AI_MODEL"):
        pytest.skip("Live key and explicit model are required; no credentials are printed")
    if importlib.util.find_spec("openai") is None:
        pytest.skip("Install optional SDK using uv sync --extra ai")
    result = OpenAIProvider(os.environ["AUTOQA_AI_MODEL"]).recommend(
        '{"untrusted_evidence":[{"id":"WF-001","status":"INFERRED","elements":["Synthetic search field"]}]}'
    )
    assert all(
        s.status == "REQUIRES_REVIEW" and set(s.evidence_ids) <= {"WF-001"}
        for s in result.suggestions
    )
