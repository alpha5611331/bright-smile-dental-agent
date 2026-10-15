import json
from collections.abc import Iterator
from typing import Any
from uuid import UUID, uuid4

import httpx
import openai
import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from bright_smile.agent.graph import build_agent
from bright_smile.api.deps import get_agent
from bright_smile.db.documents.conversation import Conversation, MessageRole
from bright_smile.services.chat import MAX_USER_TURNS
from tests.fakes import ScriptedChatModel

type Event = tuple[str, dict[str, Any]]


def parse_sse(body: str) -> list[Event]:
    """Parse a text/event-stream body into (event, data) pairs."""
    events: list[Event] = []
    for block in body.replace("\r\n", "\n").strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        if "event" in fields:
            events.append((fields["event"], json.loads(fields["data"])))
    return events


@pytest.fixture
def model(app: FastAPI) -> Iterator[ScriptedChatModel]:
    scripted = ScriptedChatModel()
    app.dependency_overrides[get_agent] = lambda: build_agent(scripted)
    yield scripted
    app.dependency_overrides.pop(get_agent, None)


async def chat(
    client: AsyncClient, message: str, conversation_id: UUID | None = None
) -> httpx.Response:
    payload: dict[str, str] = {"message": message}
    if conversation_id is not None:
        payload["conversation_id"] = str(conversation_id)
    return await client.post("/api/chat", json=payload)


async def test_new_conversation_streams_and_persists(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.replies.append("Cigna DPPO is in network.")

    response = await chat(client, "  Do you take Cigna?  ")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert names[0] == "conversation"
    assert set(names[1:-1]) == {"token"}
    assert names[-1] == "done"
    assert "".join(data["text"] for name, data in events if name == "token") == (
        "Cigna DPPO is in network."
    )

    conversation = await Conversation.get(UUID(events[0][1]["conversation_id"]))
    assert conversation is not None
    assert [(m.role, m.content) for m in conversation.messages] == [
        (MessageRole.USER, "Do you take Cigna?"),
        (MessageRole.ASSISTANT, "Cigna DPPO is in network."),
    ]
    assert conversation.expires_at is not None
    assert conversation.flags == []


async def test_follow_up_reuses_conversation_and_sends_history(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.replies += ["Hello! How can I help?", "Bethesda and Rockville."]
    first = parse_sse((await chat(client, "Hi")).text)
    conversation_id = UUID(first[0][1]["conversation_id"])

    second = parse_sse((await chat(client, "Where are you?", conversation_id)).text)

    assert second[0] == (
        "conversation",
        {"type": "conversation", "conversation_id": str(conversation_id)},
    )
    assert [m.text for m in model.calls[1][1:]] == [
        "Hi",
        "Hello! How can I help?",
        "Where are you?",
    ]
    conversation = await Conversation.get(conversation_id)
    assert conversation is not None
    assert conversation.user_turns == 2


async def test_emergency_flag_is_streamed_before_tokens_and_persisted(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.replies.append("Please go to the nearest emergency room.")

    events = parse_sse((await chat(client, "My jaw is swollen and the bleeding won't stop")).text)

    names = [name for name, _ in events]
    assert names[:2] == ["conversation", "flag"]
    assert events[1][1] == {"type": "flag", "flag": "emergency"}
    assert names.index("flag") < names.index("token")
    conversation = await Conversation.get(UUID(events[0][1]["conversation_id"]))
    assert conversation is not None
    assert conversation.flags == ["emergency"]


async def test_unknown_conversation_returns_404(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    response = await chat(client, "Hello again", uuid4())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert model.calls == []


async def test_turn_limit_returns_409(client: AsyncClient, model: ScriptedChatModel) -> None:
    conversation = Conversation()
    for i in range(MAX_USER_TURNS):
        conversation.append(MessageRole.USER, f"question {i}")
        conversation.append(MessageRole.ASSISTANT, f"answer {i}")
    await conversation.insert()

    response = await chat(client, "One more?", conversation.id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conversation_limit"
    assert model.calls == []


@pytest.mark.parametrize("message", ["", "   ", "x" * 1001])
async def test_invalid_messages_are_rejected(
    client: AsyncClient, model: ScriptedChatModel, message: str
) -> None:
    response = await chat(client, message)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert model.calls == []


async def test_llm_failure_streams_error_and_keeps_user_message(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.error = openai.OpenAIError("connection reset")

    events = parse_sse((await chat(client, "Do you take Aetna?")).text)

    names = [name for name, _ in events]
    assert names == ["conversation", "error"]
    assert events[1][1]["code"] == "upstream_unavailable"
    assert "(301) 555-0148" in events[1][1]["message"]
    conversation = await Conversation.get(UUID(events[0][1]["conversation_id"]))
    assert conversation is not None
    assert [m.role for m in conversation.messages] == [MessageRole.USER]
