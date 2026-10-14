"""Liveness and dependency health for deploy probes and cold-start warm-up."""

from fastapi import APIRouter, Response, status

from bright_smile.api.deps import MongoClientDep
from bright_smile.db.mongo import ping
from bright_smile.schemas.health import DependencyStatus, HealthResponse, ServiceStatus

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    summary="Service and database health",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def get_health(client: MongoClientDep, response: Response) -> HealthResponse:
    if await ping(client):
        return HealthResponse(status=ServiceStatus.OK, db=DependencyStatus.OK)
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status=ServiceStatus.DEGRADED, db=DependencyStatus.UNAVAILABLE)
