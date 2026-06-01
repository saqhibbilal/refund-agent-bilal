from __future__ import annotations

import os

import pytest

from app.agent.execution import AgentRunner
from app.infrastructure.mistral_client import MistralClientError, create_chat_model


@pytest.mark.integration
def test_live_mistral_refund_conversation(crm, policy):
    if not os.getenv("MISTRAL_API_KEY"):
        pytest.skip("MISTRAL_API_KEY not set")

    llm = create_chat_model()
    runner = AgentRunner(crm=crm, policy=policy, llm=llm)

    result = runner.run(
        "Hello, my email is alex.rivera@example.com. "
        "I'd like a refund for order VG-10001. The buds don't fit well."
    )

    assert result.response_text
    assert len(result.trace_events) > 0
    assert result.latest_eligibility is not None


def test_create_chat_model_without_key_raises():
    with pytest.raises(MistralClientError):
        create_chat_model(api_key="")
