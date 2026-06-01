from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel

DEFAULT_MODEL = "mistral-small-latest"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_RETRIES = 1


class MistralClientError(Exception):
    """Raised when the Mistral client cannot complete a request."""


def create_chat_model(
    *,
    api_key: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
) -> BaseChatModel:
    """Create a Mistral chat model with timeout and retry configuration."""
    key = api_key or os.getenv("MISTRAL_API_KEY")
    if not key:
        raise MistralClientError("MISTRAL_API_KEY is not set.")

    from langchain_mistralai import ChatMistralAI

    return ChatMistralAI(
        api_key=key,
        model=model or os.getenv("MISTRAL_MODEL", DEFAULT_MODEL),
        temperature=temperature,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        max_retries=MAX_RETRIES,
    )
