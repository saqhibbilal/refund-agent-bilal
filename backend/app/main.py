from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import AppResources
from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.config import get_settings
from app.domain.crm_repository import CRMRepository
from app.domain.policy_engine import PolicyEngine
from app.infrastructure.data_loader import DataLoader
from app.infrastructure.database import Database, create_engine_and_session_factory, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    loader = DataLoader(settings.data_dir)
    loaded_data = loader.load()
    crm = CRMRepository(loaded_data)
    policy = PolicyEngine(loaded_data.policy_text)
    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    init_database(engine)
    database = Database(session_factory)

    app.state.resources = AppResources(
        settings=settings,
        loaded_data=loaded_data,
        crm=crm,
        policy=policy,
        database=database,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Worknoon Refund Agent API",
        version="0.1.0",
        lifespan=lifespan,
    )

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
