"""`conversations` collection (SPEC section 6.2)."""

from datetime import datetime, timedelta
from enum import StrEnum
from typing import ClassVar
from uuid import UUID, uuid4

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel

from bright_smile.core.clock import utc_now
from bright_smile.domain.flags import Flag

ANONYMOUS_RETENTION = timedelta(days=90)


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class Conversation(Document):
    """A chat session. Anonymous sessions expire via a TTL index; sessions with a lead are kept."""

    id: UUID = Field(default_factory=uuid4)  # type: ignore[assignment]  # UUID ids instead of ObjectId
    messages: list[ChatMessage] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)
    lead_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = Field(default_factory=lambda: utc_now() + ANONYMOUS_RETENTION)
    schema_version: int = 1

    class Settings:
        name = "conversations"
        indexes: ClassVar[list[IndexModel]] = [
            IndexModel([("expires_at", pymongo.ASCENDING)], expireAfterSeconds=0),
            IndexModel([("lead_id", pymongo.ASCENDING)]),
        ]

    @property
    def user_turns(self) -> int:
        return sum(1 for m in self.messages if m.role is MessageRole.USER)

    def add_flags(self, flags: list[Flag]) -> None:
        merged = set(self.flags) | set(flags)
        self.flags = [flag for flag in Flag if flag in merged]

    def append(self, role: MessageRole, content: str) -> None:
        now = utc_now()
        self.messages.append(ChatMessage(role=role, content=content, created_at=now))
        self.updated_at = now
