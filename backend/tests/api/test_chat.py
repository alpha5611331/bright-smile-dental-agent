import json
from collections.abc import Iterator
from typing import Any
from uuid import UUID, uuid4

import httpx
import openai
import pytest
from beanie import PydanticObjectId
from fastapi import FastAPI
from httpx import AsyncClient

from bright_smile.agent.graph import build_agent
from bright_smile.agent.tools import AGENT_TOOLS
from bright_smile.api.deps import get_agent
from bright_smile.db.documents.conversation import Conversation, MessageRole
from bright_smile.db.documents.lead import Lead
from bright_smile.domain.leads import LeadSource
from bright_smile.services.chat import MAX_USER_TURNS
from tests.factories import lead_payload
from tests.fakes import ScriptedChatModel, tool_call

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
    app.dependency_overrides[get_agent] = lambda: build_agent(scripted, AGENT_TOOLS)
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


async def test_chat_captures_a_lead_and_keeps_the_transcript(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.replies += [
        tool_call("capture_lead", **lead_payload()),
        "Thanks, Jane! The front desk will call you within one business day.",
    ]

    events = parse_sse((await chat(client, "Book me for an Invisalign consult please")).text)

    names = [name for name, _ in events]
    assert names[0] == "conversation"
    assert "lead_captured" in names
    assert names.index("lead_captured") < names.index("token")
    assert names[-1] == "done"
    captured = dict(events)["lead_captured"]
    assert captured["priority"] == "P2"

    conversation_id = UUID(events[0][1]["conversation_id"])
    lead = await Lead.get(PydanticObjectId(captured["lead_id"]))
    assert lead is not None
    assert lead.conversation_id == conversation_id
    assert lead.source is LeadSource.CHAT
    conversation = await Conversation.get(conversation_id)
    assert conversation is not None
    assert conversation.lead_id == lead.id
    assert conversation.expires_at is None  # transcripts with a lead are kept
    assert model.bound_tools == ["capture_lead"]


async def test_emergency_conversation_makes_the_lead_p1(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.replies += [
        "Please go to the nearest emergency room. I can also take your details.",
        tool_call("capture_lead", **lead_payload(interest="other", patient_type="existing")),
        "Got it.",
    ]
    first = parse_sse((await chat(client, "My face is badly swollen")).text)
    conversation_id = UUID(first[0][1]["conversation_id"])

    second = parse_sse((await chat(client, "Yes please call me", conversation_id)).text)

    assert dict(second)["lead_captured"]["priority"] == "P1"


async def test_invalid_tool_input_is_returned_to_the_model_for_a_re_ask(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.replies += [
        tool_call("capture_lead", **lead_payload(phone="12345")),
        "Could you double-check your phone number?",
    ]

    events = parse_sse((await chat(client, "Please book me")).text)

    names = [name for name, _ in events]
    assert "lead_captured" not in names
    assert names[-1] == "done"
    tool_result = model.calls[1][-1]
    assert tool_result.type == "tool"
    assert "phone" in tool_result.text
    assert (
        await Lead.find(Lead.conversation_id == UUID(events[0][1]["conversation_id"])).count() == 0
    )


async def test_capture_is_idempotent_per_conversation(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.replies += [
        tool_call("capture_lead", **lead_payload()),
        "Done.",
        tool_call("capture_lead", **lead_payload()),
        "Already received.",
    ]
    first = parse_sse((await chat(client, "Book me")).text)
    conversation_id = UUID(first[0][1]["conversation_id"])

    second = parse_sse((await chat(client, "Book me again", conversation_id)).text)

    assert "lead_captured" not in [name for name, _ in second]
    assert await Lead.find(Lead.conversation_id == conversation_id).count() == 1


async def test_chat_is_rate_limited_per_client(
    client: AsyncClient, model: ScriptedChatModel
) -> None:
    model.replies += ["ok"] * 20
    for _ in range(20):
        assert (await chat(client, "Hi")).status_code == 200

    response = await chat(client, "One more")

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
    assert "retry-after" in response.headers
    assert len(model.calls) == 20
