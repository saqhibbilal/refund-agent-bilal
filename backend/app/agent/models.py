from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.domain.models import EligibilityResult, RequiredAction


class TraceEventType(str, Enum):
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    DECISION = "decision"
    INJECTION_WARNING = "injection_warning"
    VALIDATION = "validation"


class AgentRecommendation(BaseModel):
    action: RequiredAction
    order_id: str
    amount_cents: int = Field(ge=0)
    reason: str
    rule_ids: list[str] = Field(default_factory=list)


class TraceEvent(BaseModel):
    type: TraceEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentRunResult(BaseModel):
    response_text: str
    trace_events: list[TraceEvent]
    validation_passed: bool
    recommendation: AgentRecommendation | None = None
    latest_eligibility: EligibilityResult | None = None
    injection_detected: bool = False
