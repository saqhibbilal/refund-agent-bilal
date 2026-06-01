from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import (
    AppResources,
    get_chat_service,
    get_resources,
    get_trace_service,
    make_chat_service,
)
from app.api.errors import LLMUnavailableError
from app.api.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    DecisionLogsResponse,
    HealthResponse,
    SendMessageRequest,
    SessionTraceResponse,
)
from app.config import Settings
from app.services.chat_service import ChatService
from app.services.trace_service import TraceService

health_router = APIRouter()
chat_router = APIRouter()
sessions_router = APIRouter()


@health_router.get("/health", response_model=HealthResponse)
def health_check(resources: AppResources = Depends(get_resources)) -> HealthResponse:
    settings: Settings = resources.settings
    data_loaded = resources.loaded_data is not None
    llm_configured = bool(settings.mistral_api_key)
    database_ok = resources.database is not None

    if not data_loaded:
        return HealthResponse(
            status="unavailable",
            data_loaded=False,
            llm_configured=llm_configured,
            database=database_ok,
        )

    status = "ok" if llm_configured else "degraded"
    return HealthResponse(
        status=status,
        data_loaded=data_loaded,
        llm_configured=llm_configured,
        database=database_ok,
    )


@chat_router.post("/sessions", response_model=CreateSessionResponse)
def create_session(
    body: CreateSessionRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> CreateSessionResponse:
    return chat_service.create_session(customer_email=body.customer_email)


@chat_router.post("/sessions/{session_id}/messages")
def send_message(
    session_id: str,
    body: SendMessageRequest,
    request: Request,
) -> StreamingResponse:
    resources: AppResources = request.app.state.resources
    if not resources.settings.mistral_api_key:
        raise LLMUnavailableError()

    def event_stream():
        with resources.database.session() as db:
            chat_service = make_chat_service(db, resources)
            yield from chat_service.iter_message_sse(
                session_id=session_id,
                content=body.content,
                client_message_id=body.client_message_id,
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@chat_router.get("/decisions", response_model=DecisionLogsResponse)
def list_decisions(
    chat_service: ChatService = Depends(get_chat_service),
) -> DecisionLogsResponse:
    return chat_service.list_decision_logs()


@sessions_router.get("/sessions/{session_id}/trace", response_model=SessionTraceResponse)
def get_session_trace(
    session_id: str,
    trace_service: TraceService = Depends(get_trace_service),
) -> SessionTraceResponse:
    return trace_service.get_session_trace(session_id)
