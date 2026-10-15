"""Chat request and Server-Sent Event payloads (SPEC sections 7.1, 7.2)."""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from bright_smile.core.errors import ErrorCode
from bright_smile.domain.flags import Flag
from bright_smile.domain.leads import Priority

MAX_MESSAGE_CHARS = 1000

MessageText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE_CHARS)
]


class ChatRequest(BaseModel):
    conversation_id: UUID | None = Field(
        default=None,
        description="Omit to start a new conversation; reuse the id from `conversation`.",
    )
    message: MessageText


class ChatEventType(StrEnum):
    """SSE `event:` names, in the order they can appear in a stream."""

    CONVERSATION = "conversation"
    FLAG = "flag"
    TOKEN = "token"  # noqa: S105  # SSE event name, not a credential
    LEAD_CAPTURED = "lead_captured"
    ERROR = "error"
    DONE = "done"


class ConversationEvent(BaseModel):
    type: Literal[ChatEventType.CONVERSATION] = ChatEventType.CONVERSATION
    conversation_id: UUID


class FlagEvent(BaseModel):
    type: Literal[ChatEventType.FLAG] = ChatEventType.FLAG
    flag: Flag


class TokenEvent(BaseModel):
    type: Literal[ChatEventType.TOKEN] = ChatEventType.TOKEN
    text: str


class LeadCapturedEvent(BaseModel):
    type: Literal[ChatEventType.LEAD_CAPTURED] = ChatEventType.LEAD_CAPTURED
    lead_id: str
    priority: Priority


class ErrorEvent(BaseModel):
    type: Literal[ChatEventType.ERROR] = ChatEventType.ERROR
    code: ErrorCode
    message: str


class DoneEvent(BaseModel):
    type: Literal[ChatEventType.DONE] = ChatEventType.DONE


type ChatEvent = (
    ConversationEvent | FlagEvent | TokenEvent | LeadCapturedEvent | ErrorEvent | DoneEvent
)

ChatStreamEvent = Annotated[ChatEvent, Field(discriminator="type")]
"""One SSE `data` payload. Documented in OpenAPI so clients get generated types."""
