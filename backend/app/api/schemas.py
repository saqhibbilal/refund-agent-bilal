from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    customer_email: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str
    customer_email: str | None = None
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    client_message_id: str | None = Field(default=None, max_length=64)


class MessageDTO(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    client_message_id: str | None = None


class TraceEventDTO(BaseModel):
    id: str
    type: str
    payload: dict[str, Any]
    created_at: datetime
    message_id: str | None = None


class SessionTraceResponse(BaseModel):
    session_id: str
    customer_email: str | None = None
    last_action: str | None = None
    messages: list[MessageDTO]
    trace_events: list[TraceEventDTO]


class DecisionLogDTO(BaseModel):
    id: str
    session_id: str
    order_id: str
    action: str
    amount_cents: int
    reason: str
    rule_ids: list[str]
    created_at: datetime
    updated_at: datetime


class DecisionLogsResponse(BaseModel):
    decisions: list[DecisionLogDTO]


class HealthResponse(BaseModel):
    status: str
    data_loaded: bool
    llm_configured: bool
    database: bool
