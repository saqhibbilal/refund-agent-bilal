from fastapi import APIRouter

from app.api.routes import chat_router, health_router, sessions_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(chat_router, prefix="/api/chat", tags=["chat"])
api_router.include_router(sessions_router, prefix="/api/chat", tags=["sessions"])
