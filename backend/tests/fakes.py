"""Test doubles for the LLM layer."""

import json
import re
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from typing import Any, override
from uuid import uuid4

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from pydantic import Field

type Reply = str | AIMessage


def tool_call(tool_name: str, /, **args: Any) -> AIMessage:  # noqa: ANN401  # arbitrary tool arguments
    """A scripted assistant turn that calls a tool instead of answering."""
    return AIMessage(
        content="", tool_calls=[{"name": tool_name, "args": args, "id": f"call_{uuid4().hex}"}]
    )


class ScriptedChatModel(BaseChatModel):
    """Replies with scripted turns in order (text streamed word by word, or tool calls) and records
    every prompt it receives."""

    replies: list[Reply] = Field(default_factory=list)
    error: Exception | None = None
    calls: list[list[BaseMessage]] = Field(default_factory=list)
    bound_tools: list[str] = Field(default_factory=list)

    @property
    @override
    def _llm_type(self) -> str:
        return "scripted"

    @override
    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        self.bound_tools = [t.name for t in tools if isinstance(t, BaseTool)]
        return self

    def _next_reply(self, messages: list[BaseMessage]) -> AIMessage:
        self.calls.append(list(messages))
        if self.error is not None:
            raise self.error
        reply = self.replies.pop(0)
        return AIMessage(reply) if isinstance(reply, str) else reply

    def _chunks(self, reply: AIMessage) -> Iterator[AIMessageChunk]:
        if reply.tool_calls:
            yield AIMessageChunk(
                content="",
                tool_call_chunks=[
                    {"name": c["name"], "args": json.dumps(c["args"]), "id": c["id"], "index": i}
                    for i, c in enumerate(reply.tool_calls)
                ],
            )
            return
        for piece in re.split(r"(\s+)", reply.text):
            if piece:
                yield AIMessageChunk(content=piece)

    @override
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._next_reply(messages))])

    @override
    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        for chunk in self._chunks(self._next_reply(messages)):
            yield ChatGenerationChunk(message=chunk)

    @override
    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        for chunk in self._chunks(self._next_reply(messages)):
            generation = ChatGenerationChunk(message=chunk)
            if run_manager is not None:
                await run_manager.on_llm_new_token(chunk.text, chunk=generation)
            yield generation
