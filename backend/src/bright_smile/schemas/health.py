"""Health check response models."""

from enum import StrEnum

from pydantic import BaseModel


class ServiceStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"


class DependencyStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"


class HealthResponse(BaseModel):
    status: ServiceStatus
    db: DependencyStatus
