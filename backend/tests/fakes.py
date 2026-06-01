from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr


class ScriptingChatModel(BaseChatModel):
    """Deterministic chat model for unit tests — returns scripted AIMessages in order."""

    scripted_responses: list[AIMessage]
    model_name: str = "scripting-chat-model"
    _call_index: int = PrivateAttr(default=0)

    def model_post_init(self, __context: Any) -> None:
        self._call_index = 0

    @property
    def _llm_type(self) -> str:
        return "scripting-chat-model"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        index = min(self._call_index, len(self.scripted_responses) - 1)
        message = self.scripted_responses[index]
        self._call_index += 1
        return ChatResult(generations=[ChatGeneration(message=message)])

    def bind_tools(self, tools, **kwargs):
        return self
