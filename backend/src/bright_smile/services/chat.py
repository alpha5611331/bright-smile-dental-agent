"""Chat use case: conversation lifecycle and streaming a reply from the agent (SPEC section 7.2)."""

import time
from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import UUID

from langchain_core.messages import AIMessage, AIMessageChunk, AnyMessage, HumanMessage, ToolMessage
from loguru import logger
from openai import OpenAIError
from pymongo.errors import PyMongoError

from bright_smile.agent.graph import Agent, AgentState, Node
from bright_smile.agent.kb import KB
from bright_smile.agent.tools import CapturedLead, conversation_config
from bright_smile.core.errors import AppError, ErrorCode
from bright_smile.db.documents.conversation import ChatMessage, Conversation, MessageRole
from bright_smile.domain.flags import Flag
from bright_smile.schemas.chat import (
    ChatEvent,
    ConversationEvent,
    DoneEvent,
    ErrorEvent,
    FlagEvent,
    LeadCapturedEvent,
    TokenEvent,
)

MAX_USER_TURNS = 30

_UPSTREAM_MESSAGE = (
    f"The assistant is temporarily unavailable. Please try again or call {KB.phone}."
)
_INTERNAL_MESSAGE = f"Something went wrong. Please try again or call {KB.phone}."


async def open_conversation(conversation_id: UUID | None) -> Conversation:
    """Load an existing conversation or start a new (not yet persisted) one."""
    if conversation_id is None:
        return Conversation()
    conversation = await Conversation.get(conversation_id)
    if conversation is None:
        raise AppError(
            ErrorCode.NOT_FOUND, "Conversation not found or expired. Please start a new chat."
        )
    if conversation.user_turns >= MAX_USER_TURNS:
        raise AppError(
            ErrorCode.CONVERSATION_LIMIT,
            f"This conversation has reached its message limit. Please call us at {KB.phone}.",
        )
    return conversation


def _to_langchain(messages: list[ChatMessage]) -> list[AnyMessage]:
    return [
        HumanMessage(m.content) if m.role is MessageRole.USER else AIMessage(m.content)
        for m in messages
    ]


def _events_from_update(
    update: dict[str, dict[str, Any]], conversation: Conversation
) -> list[ChatEvent]:
    """Translate graph node updates into client events (guard flags, captured leads)."""
    events: list[ChatEvent] = []
    if guard := update.get(Node.GUARD):
        flags: list[Flag] = guard.get("flags", [])
        conversation.add_flags(flags)
        events += [FlagEvent(flag=flag) for flag in flags]
    if tools := update.get(Node.TOOLS):
        for message in tools.get("messages", []):
            if isinstance(message, ToolMessage) and isinstance(message.artifact, CapturedLead):
                events.append(
                    LeadCapturedEvent(
                        lead_id=message.artifact.lead_id, priority=message.artifact.priority
                    )
                )
    return events


async def stream_reply(
    agent: Agent, conversation: Conversation, text: str
) -> AsyncIterator[ChatEvent]:
    """Run one chat turn and yield SSE events: conversation, flag*, token*, then done or error."""
    started = time.perf_counter()
    yield ConversationEvent(conversation_id=conversation.id)

    history = _to_langchain(conversation.messages)
    conversation.append(MessageRole.USER, text)
    reply_parts: list[str] = []
    separate_next_run = False
    state: AgentState = {"messages": [*history, HumanMessage(text)], "flags": []}

    try:
        await conversation.save()
        async for chunk in agent.astream(
            state,
            conversation_config(conversation),
            stream_mode=["updates", "messages"],
            version="v2",
        ):
            if chunk["type"] == "updates":
                update = cast("dict[str, dict[str, Any]]", chunk["data"])
                for event in _events_from_update(update, conversation):
                    yield event
                separate_next_run = separate_next_run or (
                    Node.TOOLS in update and bool(reply_parts)
                )
            elif chunk["type"] == "messages":
                message, metadata = chunk["data"]
                if metadata.get("langgraph_node") == Node.AGENT and isinstance(
                    message, AIMessageChunk
                ):
                    token = str(message.text)
                    if token:
                        if separate_next_run:  # text from a new agent run after a tool call
                            token, separate_next_run = "\n\n" + token, False
                        reply_parts.append(token)
                        yield TokenEvent(text=token)
        conversation.append(MessageRole.ASSISTANT, "".join(reply_parts).strip())
        await conversation.save()
    except (OpenAIError, PyMongoError) as exc:
        logger.warning(
            "chat_turn_failed",
            conversation_id=str(conversation.id),
            error_type=type(exc).__name__,
        )
        yield ErrorEvent(code=ErrorCode.UPSTREAM_UNAVAILABLE, message=_UPSTREAM_MESSAGE)
        return
    except Exception as exc:  # noqa: BLE001  # reported to the client as an SSE error event
        logger.opt(exception=exc).error(
            "chat_turn_crashed",
            conversation_id=str(conversation.id),
            error_type=type(exc).__name__,
        )
        yield ErrorEvent(code=ErrorCode.INTERNAL_ERROR, message=_INTERNAL_MESSAGE)
        return

    logger.info(
        "chat_turn_completed",
        conversation_id=str(conversation.id),
        user_turns=conversation.user_turns,
        flags=conversation.flags,
        reply_chars=sum(len(p) for p in reply_parts),
        duration_ms=round((time.perf_counter() - started) * 1000),
    )
    yield DoneEvent()
