from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass

from fastapi import Depends, Request
from langchain_core.language_models.chat_models import BaseChatModel
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.crm_repository import CRMRepository
from app.domain.policy_engine import PolicyEngine
from app.infrastructure.data_loader import LoadedData
from app.infrastructure.database import Database
from app.infrastructure.mistral_client import create_chat_model
from app.services.chat_service import ChatService
from app.services.trace_service import TraceService


@dataclass
class AppResources:
    settings: Settings
    loaded_data: LoadedData
    crm: CRMRepository
    policy: PolicyEngine
    database: Database


def get_resources(request: Request) -> AppResources:
    return request.app.state.resources


def get_db_session(resources: AppResources = Depends(get_resources)) -> Generator[Session, None, None]:
    with resources.database.session() as session:
        yield session


def build_llm_factory(settings: Settings) -> Callable[[], BaseChatModel | None]:
    def factory() -> BaseChatModel | None:
        if not settings.mistral_api_key:
            return None
        return create_chat_model(api_key=settings.mistral_api_key, model=settings.mistral_model)

    return factory


def make_chat_service(db: Session, resources: AppResources) -> ChatService:
    return ChatService(
        db_session=db,
        crm=resources.crm,
        policy=resources.policy,
        llm_factory=build_llm_factory(resources.settings),
    )


def get_chat_service(
    db: Session = Depends(get_db_session),
    resources: AppResources = Depends(get_resources),
) -> ChatService:
    return make_chat_service(db, resources)


def get_trace_service(
    db: Session = Depends(get_db_session),
) -> TraceService:
    return TraceService(db)
