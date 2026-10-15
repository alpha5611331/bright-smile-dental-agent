"""Lead endpoints: public form fallback plus staff triage (SPEC sections 3 US-5, 7.1)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from bright_smile.api.deps import StaffOnly, rate_limit
from bright_smile.core.errors import error_responses
from bright_smile.core.rate_limit import Policy
from bright_smile.domain.leads import LeadSource, LeadStatus, PreferredLocation, Priority
from bright_smile.schemas.leads import (
    LeadCreate,
    LeadCreated,
    LeadDetail,
    LeadOut,
    LeadPage,
    LeadSort,
    LeadUpdate,
)
from bright_smile.services import leads as service

router = APIRouter(prefix="/leads", tags=["leads"])

_STAFF_ERRORS = error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Submit an appointment request from the form fallback",
    dependencies=[Depends(rate_limit(Policy.LEAD_FORM))],
    responses=error_responses(status.HTTP_429_TOO_MANY_REQUESTS),
)
async def post_lead(body: LeadCreate) -> LeadCreated:
    lead = await service.create_lead(body, source=LeadSource.FORM)
    return LeadCreated(id=str(lead.id), priority=lead.priority)


@router.get(
    "",
    summary="List leads for the front desk",
    dependencies=[StaffOnly],
    responses=_STAFF_ERRORS,
)
async def list_leads(
    status_filter: Annotated[list[LeadStatus] | None, Query(alias="status")] = None,
    priority: Annotated[list[Priority] | None, Query()] = None,
    location: Annotated[PreferredLocation | None, Query()] = None,
    sort: Annotated[LeadSort, Query()] = LeadSort.PRIORITY,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> LeadPage:
    return await service.list_leads(
        statuses=status_filter,
        priorities=priority,
        location=location,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{lead_id}",
    summary="Lead details with the chat transcript",
    dependencies=[StaffOnly],
    responses=_STAFF_ERRORS,
)
async def get_lead(lead_id: str) -> LeadDetail:
    return await service.get_lead_detail(lead_id)


@router.patch(
    "/{lead_id}",
    summary="Update a lead's status or notes",
    dependencies=[StaffOnly],
    responses=_STAFF_ERRORS,
)
async def patch_lead(lead_id: str, body: LeadUpdate) -> LeadOut:
    return await service.update_lead(lead_id, body)
