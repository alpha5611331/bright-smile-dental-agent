"""Test doubles for the LLM layer."""

import re
from collections.abc import AsyncIterator, Iterator
from typing import Any, override

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field


class ScriptedChatModel(BaseChatModel):
    """Replies with scripted texts in order, streaming word by word, and records every prompt."""

    replies: list[str] = Field(default_factory=list)
    error: Exception | None = None
    calls: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    @override
    def _llm_type(self) -> str:
        return "scripted"

    def _next_reply(self, messages: list[BaseMessage]) -> str:
        self.calls.append(list(messages))
        if self.error is not None:
            raise self.error
        return self.replies.pop(0)

    @override
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,  # mirrors the BaseChatModel signature
    ) -> ChatResult:
        reply = self._next_reply(messages)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(reply))])

    @override
    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,  # mirrors the BaseChatModel signature
    ) -> Iterator[ChatGenerationChunk]:
        for piece in re.split(r"(\s+)", self._next_reply(messages)):
            if piece:
                yield ChatGenerationChunk(message=AIMessageChunk(content=piece))

    @override
    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,  # mirrors the BaseChatModel signature
    ) -> AsyncIterator[ChatGenerationChunk]:
        for piece in re.split(r"(\s+)", self._next_reply(messages)):
            if piece:
                chunk = ChatGenerationChunk(message=AIMessageChunk(content=piece))
                if run_manager is not None:
                    await run_manager.on_llm_new_token(piece, chunk=chunk)
                yield chunk
