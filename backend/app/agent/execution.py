from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage

from app.agent.graph import append_injection_warning, build_agent_graph
from app.agent.models import AgentRunResult, TraceEvent, TraceEventType
from app.agent.state import initial_state
from app.domain.crm_repository import CRMRepository
from app.domain.policy_engine import PolicyEngine

SAFE_VALIDATION_FAILURE_RESPONSE = (
    "I couldn't safely verify this refund automatically. "
    "Please share the customer email and order ID, or choose one of the sample scenarios, "
    "and I can check the policy-backed result step by step."
)


def _extract_response_text(final_state: dict) -> str:
    if final_state.get("validation_errors") and final_state.get("latest_recommendation") is None:
        return SAFE_VALIDATION_FAILURE_RESPONSE

    messages = final_state.get("messages", [])
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content and not message.tool_calls:
            content = message.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [block.get("text", "") for block in content if isinstance(block, dict)]
                return "".join(parts).strip()
    if final_state.get("latest_recommendation") is not None:
        rec = final_state["latest_recommendation"]
        return rec.reason
    return "I was unable to complete your refund request."


class AgentRunner:
    """Orchestrates a single agent conversation through the LangGraph loop."""

    def __init__(
        self,
        crm: CRMRepository,
        policy: PolicyEngine,
        llm: BaseChatModel,
    ) -> None:
        self._crm = crm
        self._policy = policy
        self._llm = llm

    def run(
        self,
        user_message: str,
        *,
        as_of_date: date | None = None,
        message_history: list[BaseMessage] | None = None,
    ) -> AgentRunResult:
        effective_date = as_of_date or datetime.now(UTC).date()
        graph = build_agent_graph(
            crm=self._crm,
            policy=self._policy,
            llm=self._llm,
            as_of_date=effective_date,
        )

        state = initial_state(
            user_message,
            effective_date.isoformat(),
            messages=message_history,
        )
        state = append_injection_warning(state)

        final_state = graph.invoke(state)
        response_text = _extract_response_text(final_state)

        return AgentRunResult(
            response_text=response_text,
            trace_events=final_state.get("trace_events", []),
            validation_passed=bool(final_state.get("validation_passed")),
            recommendation=final_state.get("latest_recommendation"),
            latest_eligibility=final_state.get("latest_eligibility"),
            injection_detected=bool(final_state.get("injection_detected")),
        )


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def trace_event_to_sse(trace: TraceEvent) -> str:
    mapping = {
        TraceEventType.TOOL_START: "tool_start",
        TraceEventType.TOOL_END: "tool_end",
        TraceEventType.INJECTION_WARNING: "injection_warning",
        TraceEventType.VALIDATION: "validation",
        TraceEventType.DECISION: "decision",
    }
    event_name = mapping.get(trace.type, trace.type.value)
    return _sse_event(event_name, trace.payload)


@dataclass
class AgentStreamResult:
    final_state: dict[str, Any] = field(default_factory=dict)


def iter_agent_sse(
    *,
    crm: CRMRepository,
    policy: PolicyEngine,
    llm: BaseChatModel,
    user_message: str,
    as_of_date: date | None = None,
    message_history: list[BaseMessage] | None = None,
    result: AgentStreamResult | None = None,
) -> Iterator[str]:
    """Yield SSE lines for one agent turn using a single graph execution."""
    effective_date = as_of_date or datetime.now(UTC).date()
    graph = build_agent_graph(crm=crm, policy=policy, llm=llm, as_of_date=effective_date)

    state = initial_state(
        user_message,
        effective_date.isoformat(),
        messages=message_history,
    )
    state = append_injection_warning(state)

    seen_trace_count = len(state.get("trace_events", []))
    for trace in state.get("trace_events", []):
        yield trace_event_to_sse(trace)

    final_state: dict[str, Any] = state
    for snapshot in graph.stream(state, stream_mode="values"):
        final_state = snapshot
        traces = snapshot.get("trace_events", [])
        for trace in traces[seen_trace_count:]:
            if trace.type in (
                TraceEventType.TOOL_START,
                TraceEventType.TOOL_END,
                TraceEventType.INJECTION_WARNING,
                TraceEventType.VALIDATION,
            ):
                yield trace_event_to_sse(trace)
        seen_trace_count = len(traces)

    for trace in final_state.get("trace_events", [])[seen_trace_count:]:
        if trace.type == TraceEventType.DECISION:
            yield trace_event_to_sse(trace)

    response_text = _extract_response_text(final_state)
    if response_text:
        yield _sse_event("token", {"text": response_text})

    recommendation = final_state.get("latest_recommendation")
    yield _sse_event(
        "done",
        {
            "response_text": response_text,
            "validation_passed": bool(final_state.get("validation_passed")),
            "recommendation": recommendation.model_dump(mode="json") if recommendation else None,
        },
    )

    if result is not None:
        result.final_state = final_state
