"""Lead creation use case: applies the domain rules and links the conversation (SPEC section 6)."""

from datetime import datetime

from loguru import logger

from bright_smile.core.clock import utc_now
from bright_smile.db.documents.conversation import Conversation
from bright_smile.db.documents.lead import Lead
from bright_smile.domain.flags import Flag
from bright_smile.domain.leads import LeadSource, compute_priority
from bright_smile.domain.schedule import is_after_hours, sla_due_at
from bright_smile.schemas.leads import LeadCreate


async def create_lead(
    data: LeadCreate,
    *,
    source: LeadSource,
    conversation: Conversation | None = None,
    now: datetime | None = None,
) -> Lead:
    """Persist a lead with computed priority, SLA, and after-hours flag.

    When the lead comes from a chat, the conversation is linked and its TTL is cleared so the
    transcript is kept for the front desk.
    """
    created_at = now or utc_now()
    lead = Lead(
        conversation_id=conversation.id if conversation else None,
        name=data.name,
        phone=data.phone,
        email=str(data.email),
        reason=data.reason,
        preferred_location=data.preferred_location,
        patient_type=data.patient_type,
        interest=data.interest,
        priority=compute_priority(
            interest=data.interest,
            patient_type=data.patient_type,
            emergency_flagged=bool(conversation and Flag.EMERGENCY in conversation.flags),
        ),
        contact_consent=data.contact_consent,
        source=source,
        after_hours=is_after_hours(created_at),
        created_at=created_at,
        updated_at=created_at,
        sla_due_at=sla_due_at(created_at),
    )
    await lead.insert()

    if conversation is not None:
        conversation.lead_id = lead.id
        conversation.expires_at = None
        await conversation.save()

    logger.info(
        "lead_created",
        lead_id=str(lead.id),
        source=source,
        priority=lead.priority,
        interest=lead.interest,
        after_hours=lead.after_hours,
    )
    return lead
