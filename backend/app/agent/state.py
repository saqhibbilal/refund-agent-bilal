from __future__ import annotations

import re
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from app.agent.models import AgentRecommendation, TraceEvent
from app.domain.models import EligibilityResult


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trace_events: list[TraceEvent]
    as_of_date: str
    latest_eligibility: EligibilityResult | None
    latest_eligibility_order_id: str | None
    latest_recommendation: AgentRecommendation | None
    validation_passed: bool
    validation_errors: list[str]
    injection_detected: bool
    validation_attempts: int


INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"disregard\s+(the\s+)?policy",
        r"you\s+are\s+now\s+(in\s+)?(debug|admin|developer)\s+mode",
        r"pretend\s+you\s+are",
        r"system\s+prompt",
        r"approve\s+(this|the)\s+refund\s+anyway",
        r"bypass\s+(the\s+)?(rules|policy|validation)",
    )
)


def detect_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in INJECTION_PATTERNS)


def initial_state(
    user_message: str,
    as_of_date: str,
    messages: list[BaseMessage] | None = None,
) -> AgentState:
    from langchain_core.messages import HumanMessage

    return {
        "messages": messages or [HumanMessage(content=user_message)],
        "trace_events": [],
        "as_of_date": as_of_date,
        "latest_eligibility": None,
        "latest_eligibility_order_id": None,
        "latest_recommendation": None,
        "validation_passed": False,
        "validation_errors": [],
        "injection_detected": detect_injection(user_message),
        "validation_attempts": 0,
    }
