from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.api.deps import AppResources
from app.config import get_settings
from app.domain.crm_repository import CRMRepository
from app.domain.policy_engine import PolicyEngine
from app.infrastructure.data_loader import DataLoader
from app.infrastructure.database import Database, create_engine_and_session_factory, init_database
from app.main import create_app
from tests.fakes import ScriptingChatModel

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _parse_sse_events(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    blocks = body.strip().split("\n\n")
    for block in blocks:
        if not block.strip():
            continue
        event_name = "message"
        data_payload: dict = {}
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ")
            elif line.startswith("data: "):
                data_payload = json.loads(line.removeprefix("data: "))
        events.append((event_name, data_payload))
    return events


def _scripted_llm():
    tool_call_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "check_refund_eligibility",
                "args": {"order_id": "VG-10003"},
                "id": "call-1",
                "type": "tool_call",
            },
            {
                "name": "record_agent_recommendation",
                "args": {
                    "action": "deny",
                    "order_id": "VG-10003",
                    "amount_cents": 0,
                    "reason": "Final sale item.",
                    "rule_ids": ["RULE-FINAL-SALE"],
                },
                "id": "call-2",
                "type": "tool_call",
            },
        ],
    )
    final_message = AIMessage(content="Order VG-10003 is final sale and cannot be refunded.")
    return ScriptingChatModel(scripted_responses=[tool_call_message, final_message])


def _init_app_resources(app, monkeypatch, db_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    get_settings.cache_clear()
    settings = get_settings()

    loaded = DataLoader(DATA_DIR).load()
    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    init_database(engine)

    def mock_build_llm_factory(_settings):
        def factory():
            return _scripted_llm()

        return factory

    monkeypatch.setattr("app.api.deps.build_llm_factory", mock_build_llm_factory)

    app.state.resources = AppResources(
        settings=settings,
        loaded_data=loaded,
        crm=CRMRepository(loaded),
        policy=PolicyEngine(loaded.policy_text),
        database=Database(session_factory),
    )


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    app = create_app()
    _init_app_resources(app, monkeypatch, tmp_path / "test.db")

    with TestClient(app) as client:
        yield client

    get_settings.cache_clear()


class TestHealthAPI:
    def test_health_ok(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["data_loaded"] is True
        assert body["llm_configured"] is True
        assert body["database"] is True


class TestChatAPI:
    def test_create_session(self, api_client):
        response = api_client.post(
            "/api/chat/sessions",
            json={"customer_email": "alex.rivera@example.com"},
        )
        assert response.status_code == 200
        assert "session_id" in response.json()

    def test_send_message_sse_and_trace(self, api_client):
        session_id = api_client.post("/api/chat/sessions", json={}).json()["session_id"]

        with api_client.stream(
            "POST",
            f"/api/chat/sessions/{session_id}/messages",
            json={
                "content": "Refund order VG-10003 for sam.patel@example.com",
                "client_message_id": "msg-1",
            },
        ) as response:
            assert response.status_code == 200
            body = "".join(response.iter_text())

        events = _parse_sse_events(body)
        event_names = [name for name, _ in events]
        assert "tool_end" in event_names or "tool_start" in event_names
        assert "done" in event_names

        trace = api_client.get(f"/api/chat/sessions/{session_id}/trace")
        assert trace.status_code == 200
        trace_body = trace.json()
        assert len(trace_body["messages"]) == 2
        assert len(trace_body["trace_events"]) >= 1

    def test_send_message_without_api_key_returns_503(self, tmp_path, monkeypatch):
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        app = create_app()
        _init_app_resources(app, monkeypatch, tmp_path / "test2.db")
        app.state.resources.settings.mistral_api_key = None

        with TestClient(app) as client:
            session_id = client.post("/api/chat/sessions", json={}).json()["session_id"]
            response = client.post(
                f"/api/chat/sessions/{session_id}/messages",
                json={"content": "hello"},
            )
            assert response.status_code == 503
            assert response.json()["code"] == "LLM_UNAVAILABLE"

        get_settings.cache_clear()
