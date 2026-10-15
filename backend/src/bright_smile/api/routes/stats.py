"""Dashboard statistics (SPEC section 3, US-5)."""

from fastapi import APIRouter, status

from bright_smile.api.deps import StaffOnly
from bright_smile.core.errors import error_responses
from bright_smile.schemas.leads import LeadStats
from bright_smile.services.leads import lead_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "",
    summary="Front-desk stat cards",
    dependencies=[StaffOnly],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def get_stats() -> LeadStats:
    return await lead_stats()
