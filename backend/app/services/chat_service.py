from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.execution import AgentStreamResult, _extract_response_text, iter_agent_sse
from app.api.errors import DuplicateMessageError
from app.api.schemas import CreateSessionResponse, DecisionLogDTO, DecisionLogsResponse
from app.domain.crm_repository import CRMRepository
from app.domain.policy_engine import PolicyEngine
from app.infrastructure.database import ChatSessionRow, DecisionLogRow, MessageRow, _utcnow
from app.services.trace_service import TraceService


class ChatService:
    def __init__(
        self,
        db_session: Session,
        crm: CRMRepository,
        policy: PolicyEngine,
        llm_factory: Callable[[], BaseChatModel | None],
    ) -> None:
        self._db = db_session
        self._crm = crm
        self._policy = policy
        self._llm_factory = llm_factory
        self._trace = TraceService(db_session)

    def create_session(self, customer_email: str | None = None) -> CreateSessionResponse:
        now = _utcnow()
        session = ChatSessionRow(
            id=str(uuid4()),
            customer_email=customer_email.lower().strip() if customer_email else None,
            created_at=now,
            updated_at=now,
            last_action=None,
        )
        self._db.add(session)
        self._db.flush()
        return CreateSessionResponse(
            session_id=session.id,
            customer_email=session.customer_email,
            created_at=session.created_at,
        )

    def get_session_or_raise(self, session_id: str) -> ChatSessionRow:
        return self._trace.get_session_or_raise(session_id)

    def _get_llm(self) -> BaseChatModel:
        llm = self._llm_factory()
        if llm is None:
            from app.api.errors import LLMUnavailableError

            raise LLMUnavailableError()
        return llm

    def _find_existing_user_message(
        self,
        session_id: str,
        client_message_id: str,
    ) -> MessageRow | None:
        stmt = select(MessageRow).where(
            MessageRow.session_id == session_id,
            MessageRow.client_message_id == client_message_id,
            MessageRow.role == "user",
        )
        return self._db.scalars(stmt).first()

    def _message_history(self, session_id: str) -> list[BaseMessage]:
        stmt = (
            select(MessageRow)
            .where(MessageRow.session_id == session_id)
            .order_by(MessageRow.created_at, MessageRow.id)
        )
        history: list[BaseMessage] = []
        for row in self._db.scalars(stmt):
            content = row.content.strip()
            if not content:
                continue
            if row.role == "user":
                history.append(HumanMessage(content=content))
            elif row.role == "assistant":
                history.append(AIMessage(content=content))
        return history

    def list_decision_logs(self) -> DecisionLogsResponse:
        stmt = select(DecisionLogRow).order_by(DecisionLogRow.updated_at.desc())
        decisions = [
            self._decision_row_to_dto(row)
            for row in self._db.scalars(stmt)
        ]
        return DecisionLogsResponse(decisions=decisions)

    def _persist_decision_log(
        self,
        session_id: str,
        recommendation,
    ) -> None:
        now = _utcnow()
        stmt = select(DecisionLogRow).where(
            DecisionLogRow.session_id == session_id,
            DecisionLogRow.order_id == recommendation.order_id,
        )
        row = self._db.scalars(stmt).first()
        if row is None:
            row = DecisionLogRow(
                id=str(uuid4()),
                session_id=session_id,
                order_id=recommendation.order_id,
                action=recommendation.action.value,
                amount_cents=recommendation.amount_cents,
                reason=recommendation.reason,
                rule_ids_json=json.dumps(recommendation.rule_ids),
                created_at=now,
                updated_at=now,
            )
            self._db.add(row)
            return

        row.action = recommendation.action.value
        row.amount_cents = recommendation.amount_cents
        row.reason = recommendation.reason
        row.rule_ids_json = json.dumps(recommendation.rule_ids)
        row.updated_at = now

    @staticmethod
    def _decision_row_to_dto(row: DecisionLogRow) -> DecisionLogDTO:
        return DecisionLogDTO(
            id=row.id,
            session_id=row.session_id,
            order_id=row.order_id,
            action=row.action,
            amount_cents=row.amount_cents,
            reason=row.reason,
            rule_ids=json.loads(row.rule_ids_json),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def iter_message_sse(
        self,
        session_id: str,
        content: str,
        client_message_id: str | None = None,
    ) -> Iterator[str]:
        session = self.get_session_or_raise(session_id)

        if client_message_id and self._find_existing_user_message(session_id, client_message_id):
            raise DuplicateMessageError(client_message_id)

        user_message_id = str(uuid4())
        user_row = MessageRow(
            id=user_message_id,
            session_id=session_id,
            role="user",
            content=content.strip(),
            client_message_id=client_message_id,
            created_at=_utcnow(),
        )
        self._db.add(user_row)
        self._db.flush()
        message_history = self._message_history(session_id)

        stream_result = AgentStreamResult()
        yield from iter_agent_sse(
            crm=self._crm,
            policy=self._policy,
            llm=self._get_llm(),
            user_message=content.strip(),
            message_history=message_history,
            result=stream_result,
        )

        final_state = stream_result.final_state
        assistant_text = _extract_response_text(final_state)

        for trace in final_state.get("trace_events", []):
            self._trace.append_from_model(session_id, trace, message_id=user_message_id)

        recommendation = final_state.get("latest_recommendation")
        if recommendation is not None:
            session.last_action = recommendation.action.value
            if final_state.get("validation_passed"):
                self._persist_decision_log(session_id, recommendation)
        session.updated_at = _utcnow()

        assistant_row = MessageRow(
            id=str(uuid4()),
            session_id=session_id,
            role="assistant",
            content=assistant_text,
            client_message_id=None,
            created_at=_utcnow(),
        )
        self._db.add(assistant_row)
        self._db.flush()
