"""Lead creation use case: applies the domain rules and links the conversation (SPEC section 6)."""

from datetime import UTC, datetime, time
from typing import Any

from beanie import PydanticObjectId, SortDirection
from loguru import logger

from bright_smile.core.clock import utc_now
from bright_smile.core.errors import AppError, ErrorCode
from bright_smile.db.documents.conversation import Conversation
from bright_smile.db.documents.lead import Lead
from bright_smile.domain.flags import Flag
from bright_smile.domain.leads import (
    LeadSource,
    LeadStatus,
    PreferredLocation,
    Priority,
    compute_priority,
)
from bright_smile.domain.schedule import PRACTICE_TZ, is_after_hours, is_overdue, sla_due_at
from bright_smile.schemas.leads import (
    LeadCreate,
    LeadDetail,
    LeadOut,
    LeadPage,
    LeadSort,
    LeadStats,
    LeadUpdate,
    TranscriptMessage,
)


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


# Staff use cases ------------------------------------------------------------------------------

_SORTS: dict[LeadSort, list[tuple[str, SortDirection]]] = {
    LeadSort.PRIORITY: [
        ("priority", SortDirection.ASCENDING),
        ("created_at", SortDirection.ASCENDING),
    ],
    LeadSort.NEWEST: [("created_at", SortDirection.DESCENDING)],
    LeadSort.OLDEST: [("created_at", SortDirection.ASCENDING)],
}
OPEN_STATUSES = (LeadStatus.NEW, LeadStatus.CONTACTED)


def to_lead_out(lead: Lead, now: datetime) -> LeadOut:
    return LeadOut(
        id=str(lead.id),
        conversation_id=lead.conversation_id,
        name=lead.name,
        phone=lead.phone,
        email=lead.email,
        reason=lead.reason,
        preferred_location=lead.preferred_location,
        patient_type=lead.patient_type,
        interest=lead.interest,
        priority=lead.priority,
        status=lead.status,
        source=lead.source,
        after_hours=lead.after_hours,
        notes=lead.notes,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        sla_due_at=lead.sla_due_at,
        contacted_at=lead.contacted_at,
        overdue=lead.status is LeadStatus.NEW and is_overdue(lead.sla_due_at, now),
    )


async def list_leads(
    *,
    statuses: list[LeadStatus] | None,
    priorities: list[Priority] | None,
    location: PreferredLocation | None,
    sort: LeadSort,
    page: int,
    page_size: int,
) -> LeadPage:
    query: dict[str, Any] = {}
    if statuses:
        query["status"] = {"$in": [s.value for s in statuses]}
    if priorities:
        query["priority"] = {"$in": [p.value for p in priorities]}
    if location:
        query["preferred_location"] = location.value
    found = Lead.find(query)
    total = await found.count()
    leads = await found.sort(_SORTS[sort]).skip((page - 1) * page_size).limit(page_size).to_list()
    now = utc_now()
    return LeadPage(
        items=[to_lead_out(lead, now) for lead in leads],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_lead(lead_id: str) -> Lead:
    lead = await Lead.get(lead_id) if PydanticObjectId.is_valid(lead_id) else None
    if lead is None:
        raise AppError(ErrorCode.NOT_FOUND, "Lead not found")
    return lead


async def get_lead_detail(lead_id: str) -> LeadDetail:
    lead = await get_lead(lead_id)
    conversation = await Conversation.get(lead.conversation_id) if lead.conversation_id else None
    return LeadDetail(
        **to_lead_out(lead, utc_now()).model_dump(),
        flags=conversation.flags if conversation else [],
        transcript=[
            TranscriptMessage(role=m.role, content=m.content, created_at=m.created_at)
            for m in (conversation.messages if conversation else [])
        ],
    )


async def update_lead(lead_id: str, update: LeadUpdate) -> LeadOut:
    lead = await get_lead(lead_id)
    now = utc_now()
    if update.status is not None and update.status is not lead.status:
        if lead.status is LeadStatus.NEW and lead.contacted_at is None:
            lead.contacted_at = now  # first transition out of `new` (SPEC section 3, US-5)
        lead.status = update.status
    if update.notes is not None:
        lead.notes = update.notes
    lead.updated_at = now
    await lead.save()
    logger.info("lead_updated", lead_id=lead_id, status=lead.status)
    return to_lead_out(lead, now)


async def lead_stats(now: datetime | None = None) -> LeadStats:
    current = now or utc_now()
    local_midnight = datetime.combine(
        current.astimezone(PRACTICE_TZ).date(), time.min, tzinfo=PRACTICE_TZ
    )
    total = await Lead.find_all().count()
    after_hours = await Lead.find(Lead.after_hours == True).count()  # noqa: E712  # Beanie query
    return LeadStats(
        new_today=await Lead.find(Lead.created_at >= local_midnight.astimezone(UTC)).count(),
        overdue=await Lead.find(Lead.status == LeadStatus.NEW, Lead.sla_due_at < current).count(),
        open_high_value=await Lead.find(
            {"status": {"$in": [s.value for s in OPEN_STATUSES]}, "priority": Priority.P2.value}
        ).count(),
        after_hours_share=round(after_hours / total, 2) if total else 0.0,
    )
