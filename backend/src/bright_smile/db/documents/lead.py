"""`leads` collection (SPEC section 6.1)."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID

import pymongo
from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from bright_smile.core.clock import utc_now
from bright_smile.domain.leads import (
    Interest,
    LeadSource,
    LeadStatus,
    PatientType,
    PreferredLocation,
    Priority,
)


class Lead(Document):
    """An appointment request waiting for a front-desk callback."""

    conversation_id: UUID | None = None
    name: str
    phone: str
    email: str
    reason: str
    preferred_location: PreferredLocation
    patient_type: PatientType
    interest: Interest
    priority: Priority
    status: LeadStatus = LeadStatus.NEW
    contact_consent: bool
    source: LeadSource
    after_hours: bool
    notes: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    sla_due_at: datetime
    contacted_at: datetime | None = None
    schema_version: int = 1

    class Settings:
        name = "leads"
        indexes: ClassVar[list[IndexModel]] = [
            IndexModel(
                [
                    ("status", pymongo.ASCENDING),
                    ("priority", pymongo.ASCENDING),
                    ("created_at", pymongo.DESCENDING),
                ]
            ),
            IndexModel([("conversation_id", pymongo.ASCENDING)]),
            IndexModel([("created_at", pymongo.DESCENDING)]),
        ]
