"""Patient chat endpoint: one message in, a Server-Sent Event stream out (SPEC section 7.2)."""

from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.sse import EventSourceResponse, ServerSentEvent

from bright_smile.api.deps import AgentDep, rate_limit
from bright_smile.core.errors import error_responses
from bright_smile.core.rate_limit import Policy
from bright_smile.db.documents.conversation import Conversation
from bright_smile.schemas.chat import ChatRequest, ChatStreamEvent
from bright_smile.services.chat import open_conversation, stream_reply

router = APIRouter(prefix="/chat", tags=["chat"])


async def _resolve_conversation(body: ChatRequest) -> Conversation:
    """Runs before the stream starts, so lookup and limit errors still get a proper status code."""
    return await open_conversation(body.conversation_id)


@router.post(
    "",
    response_class=EventSourceResponse,
    summary="Send a message and stream the assistant's reply",
    dependencies=[Depends(rate_limit(Policy.CHAT))],
    responses={
        status.HTTP_200_OK: {
            "model": ChatStreamEvent,
            "description": "Server-Sent Events; each `data` line is one of these payloads",
        },
        **error_responses(
            status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT, status.HTTP_429_TOO_MANY_REQUESTS
        ),
    },
)
async def post_chat(
    body: ChatRequest,
    conversation: Annotated[Conversation, Depends(_resolve_conversation)],
    agent: AgentDep,
) -> AsyncIterable[ServerSentEvent]:
    async for event in stream_reply(agent, conversation, body.message):
        yield ServerSentEvent(event=event.type, data=event)
