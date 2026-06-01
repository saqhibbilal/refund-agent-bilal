from __future__ import annotations

from datetime import date

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, StateGraph

from app.agent.models import TraceEvent, TraceEventType
from app.agent.nodes import (
    build_agent_node,
    build_tools_executor,
    build_validate_node,
    route_after_agent,
    route_after_validate,
)
from app.agent.state import AgentState
from app.agent.tools import AgentToolkit, ToolExecutionContext
from app.domain.crm_repository import CRMRepository
from app.domain.policy_engine import PolicyEngine


def build_agent_graph(
    crm: CRMRepository,
    policy: PolicyEngine,
    llm: BaseChatModel,
    as_of_date: date,
):
    context = ToolExecutionContext(trace_events=[])
    toolkit = AgentToolkit(crm=crm, policy=policy, context=context, as_of_date=as_of_date)

    graph = StateGraph(AgentState)
    graph.add_node("agent", build_agent_node(llm, toolkit.as_langchain_tools()))
    graph.add_node("tools", build_tools_executor(toolkit))
    graph.add_node("validate", build_validate_node())

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {"tools": "tools", "validate": "validate", "end": END},
    )
    graph.add_edge("tools", "agent")
    graph.add_conditional_edges(
        "validate",
        route_after_validate,
        {"agent": "agent", "end": END},
    )

    return graph.compile()


def append_injection_warning(state: AgentState) -> AgentState:
    if not state.get("injection_detected"):
        return state
    warning = TraceEvent(
        type=TraceEventType.INJECTION_WARNING,
        payload={"message": "Potential prompt injection detected in user input."},
    )
    return {**state, "trace_events": [*state["trace_events"], warning]}
