from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agent.models import TraceEvent
from app.api.errors import SessionNotFoundError
from app.api.schemas import MessageDTO, SessionTraceResponse, TraceEventDTO
from app.infrastructure.database import (
    ChatSessionRow,
    TraceEventRow,
    _utcnow,
    row_to_trace_payload,
    serialize_payload,
)


class TraceService:
    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def get_session_or_raise(self, session_id: str) -> ChatSessionRow:
        session = self._db.get(ChatSessionRow, session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    def append_event(
        self,
        session_id: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        message_id: str | None = None,
        created_at: datetime | None = None,
    ) -> TraceEventRow:
        row = TraceEventRow(
            id=str(uuid4()),
            session_id=session_id,
            message_id=message_id,
            event_type=event_type,
            payload_json=serialize_payload(payload),
            created_at=created_at or _utcnow(),
        )
        self._db.add(row)
        return row

    def append_from_model(
        self,
        session_id: str,
        event: TraceEvent,
        *,
        message_id: str | None = None,
    ) -> TraceEventRow:
        return self.append_event(
            session_id=session_id,
            event_type=event.type.value,
            payload=event.payload,
            message_id=message_id,
            created_at=event.timestamp,
        )

    def get_session_trace(self, session_id: str) -> SessionTraceResponse:
        session = self.get_session_or_raise(session_id)
        messages = sorted(session.messages, key=lambda row: row.created_at)
        events = sorted(session.trace_events, key=lambda row: row.created_at)
        return SessionTraceResponse(
            session_id=session.id,
            customer_email=session.customer_email,
            last_action=session.last_action,
            messages=[
                MessageDTO(
                    id=message.id,
                    role=message.role,
                    content=message.content,
                    created_at=message.created_at,
                    client_message_id=message.client_message_id,
                )
                for message in messages
            ],
            trace_events=[
                TraceEventDTO(
                    id=event.id,
                    type=event.event_type,
                    payload=row_to_trace_payload(event),
                    created_at=event.created_at,
                    message_id=event.message_id,
                )
                for event in events
            ],
        )
