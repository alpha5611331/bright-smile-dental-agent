"""Lead input validation, shared by the `capture_lead` tool and the form fallback (SPEC 3, US-2)."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

from bright_smile.db.documents.conversation import MessageRole
from bright_smile.domain.flags import Flag
from bright_smile.domain.leads import (
    Interest,
    LeadSource,
    LeadStatus,
    PatientType,
    PreferredLocation,
    Priority,
)

UsPhone = Annotated[
    str,
    PhoneNumberValidator(default_region="US", number_format="E164", supported_regions=["US"]),
]
"""US phone number, normalized to E.164 (e.g. `+13015550148`)."""

PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
VisitReason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


def _require_consent(value: bool) -> bool:  # noqa: FBT001  # pydantic validator signature
    if not value:
        raise ValueError("the visitor must agree to be contacted by the front desk")
    return value


ContactConsent = Annotated[bool, AfterValidator(_require_consent)]


class LeadCreate(BaseModel):
    """A validated appointment request."""

    model_config = ConfigDict(extra="forbid")

    name: PersonName = Field(description="Visitor's full name")
    phone: UsPhone = Field(description="US phone number the front desk should call")
    email: EmailStr = Field(description="Visitor's email address")
    reason: VisitReason = Field(description="Reason for the visit, in the visitor's words")
    preferred_location: PreferredLocation = Field(
        description="Preferred office: bethesda, rockville, or no_preference"
    )
    patient_type: PatientType = Field(
        default=PatientType.UNKNOWN, description="new or existing patient, if known"
    )
    interest: Interest = Field(
        default=Interest.OTHER, description="Closest match to what the visitor wants"
    )
    contact_consent: ContactConsent = Field(
        description="True only if the visitor explicitly agreed to be contacted"
    )


class LeadCreated(BaseModel):
    id: str
    priority: Priority


# Staff-facing models (SPEC section 7.1). ------------------------------------------------------


class LeadSort(StrEnum):
    PRIORITY = "priority"  # highest priority first, then oldest first (default triage view)
    NEWEST = "newest"
    OLDEST = "oldest"


class LeadOut(BaseModel):
    id: str
    conversation_id: UUID | None
    name: str
    phone: str
    email: str
    reason: str
    preferred_location: PreferredLocation
    patient_type: PatientType
    interest: Interest
    priority: Priority
    status: LeadStatus
    source: LeadSource
    after_hours: bool
    notes: str
    created_at: datetime
    updated_at: datetime
    sla_due_at: datetime
    contacted_at: datetime | None
    overdue: bool = Field(description="Still `new` after its SLA deadline")


class TranscriptMessage(BaseModel):
    role: MessageRole
    content: str
    created_at: datetime


class LeadDetail(LeadOut):
    flags: list[Flag]
    transcript: list[TranscriptMessage]


class LeadPage(BaseModel):
    items: list[LeadOut]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


class LeadUpdate(BaseModel):
    """Staff edits. Omitted fields are left unchanged."""

    model_config = ConfigDict(extra="forbid")

    status: LeadStatus | None = None
    notes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] | None = None


class LeadStats(BaseModel):
    new_today: int = Field(ge=0, description="Leads created today (practice time)")
    overdue: int = Field(ge=0, description="Leads still `new` after their SLA deadline")
    open_high_value: int = Field(ge=0, description="Open P2 leads (Invisalign, implants, crowns)")
    after_hours_share: float = Field(
        ge=0, le=1, description="Share of all leads captured while both offices were closed"
    )
