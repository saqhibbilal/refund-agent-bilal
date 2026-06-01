from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain.models import (
    CustomerNotFoundError,
    DomainError,
    OrderNotFoundError,
    PolicyRuleNotFoundError,
)
from app.infrastructure.mistral_client import MistralClientError


class ErrorBody(BaseModel):
    code: str
    message: str


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class SessionNotFoundError(AppError):
    def __init__(self, session_id: str) -> None:
        super().__init__(
            code="SESSION_NOT_FOUND",
            message=f"Chat session not found: {session_id}",
            status_code=404,
        )


class DuplicateMessageError(AppError):
    def __init__(self, client_message_id: str) -> None:
        super().__init__(
            code="DUPLICATE_MESSAGE",
            message=f"Message already processed: {client_message_id}",
            status_code=409,
        )


class LLMUnavailableError(AppError):
    def __init__(self, message: str = "Mistral API is not configured or unavailable.") -> None:
        super().__init__(code="LLM_UNAVAILABLE", message=message, status_code=503)


class ValidationFailedError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code="VALIDATION_FAILED", message=message, status_code=422)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorBody(code=exc.code, message=exc.message).model_dump(),
        )

    @app.exception_handler(MistralClientError)
    async def mistral_error_handler(_request: Request, exc: MistralClientError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=ErrorBody(code="LLM_UNAVAILABLE", message=str(exc)).model_dump(),
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        code = "DOMAIN_ERROR"
        status_code = 404
        if isinstance(exc, (CustomerNotFoundError, OrderNotFoundError, PolicyRuleNotFoundError)):
            code = "NOT_FOUND"
        return JSONResponse(
            status_code=status_code,
            content=ErrorBody(code=code, message=str(exc)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorBody(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
            ).model_dump(),
        )
