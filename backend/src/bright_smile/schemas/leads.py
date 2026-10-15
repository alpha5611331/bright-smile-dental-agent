"""Lead input validation, shared by the `capture_lead` tool and the form fallback (SPEC 3, US-2)."""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

from bright_smile.domain.leads import Interest, PatientType, PreferredLocation, Priority

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
