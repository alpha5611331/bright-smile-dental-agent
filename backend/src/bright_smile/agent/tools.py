"""Agent tools. `capture_lead` turns a collected appointment request into a lead (SPEC US-2)."""

from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel

from bright_smile.db.documents.conversation import Conversation
from bright_smile.domain.leads import LeadSource, Priority
from bright_smile.schemas.leads import LeadCreate
from bright_smile.services.leads import create_lead

CONVERSATION_CONFIG_KEY = "conversation"


class CapturedLead(BaseModel):
    """Tool artifact: surfaced to the client as a `lead_captured` event, hidden from the model."""

    lead_id: str
    priority: Priority


def conversation_config(conversation: Conversation) -> RunnableConfig:
    """Run config that gives tools access to the live conversation object."""
    return {"configurable": {CONVERSATION_CONFIG_KEY: conversation}}


def _conversation_from(config: RunnableConfig) -> Conversation:
    conversation = config.get("configurable", {}).get(CONVERSATION_CONFIG_KEY)
    if not isinstance(conversation, Conversation):
        raise TypeError("capture_lead requires the conversation in the run config")
    return conversation


async def _capture_lead(
    config: RunnableConfig,
    **fields: Any,  # noqa: ANN401  # validated by the LeadCreate args schema
) -> tuple[str, CapturedLead | None]:
    conversation = _conversation_from(config)
    if conversation.lead_id is not None:
        return (
            "This visitor's request was already received. Do not submit it again; tell them the "
            "front desk will call within one business day.",
            None,
        )
    lead = await create_lead(
        LeadCreate.model_validate(fields), source=LeadSource.CHAT, conversation=conversation
    )
    return (
        "Request saved. Confirm to the visitor that the front desk will call within one business "
        "day, and remind them what to bring.",
        CapturedLead(lead_id=str(lead.id), priority=lead.priority),
    )


capture_lead: BaseTool = StructuredTool.from_function(
    coroutine=_capture_lead,
    name="capture_lead",
    description=(
        "Save the visitor's appointment request for a front-desk callback. Call only after the "
        "visitor has given their name, phone, email, reason for visit, preferred location, and "
        "explicit permission to be contacted."
    ),
    args_schema=LeadCreate,
    response_format="content_and_artifact",
)

AGENT_TOOLS: tuple[BaseTool, ...] = (capture_lead,)
