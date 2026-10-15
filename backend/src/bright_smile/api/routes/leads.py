"""Lead endpoints. Public form fallback here; staff endpoints arrive with authentication (#9)."""

from fastapi import APIRouter, status

from bright_smile.domain.leads import LeadSource
from bright_smile.schemas.leads import LeadCreate, LeadCreated
from bright_smile.services.leads import create_lead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Submit an appointment request from the form fallback",
)
async def post_lead(body: LeadCreate) -> LeadCreated:
    lead = await create_lead(body, source=LeadSource.FORM)
    return LeadCreated(id=str(lead.id), priority=lead.priority)
