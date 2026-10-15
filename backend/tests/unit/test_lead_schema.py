import pytest
from pydantic import ValidationError

from bright_smile.domain.leads import Interest, PatientType
from bright_smile.schemas.leads import LeadCreate
from tests.factories import lead_payload


def test_valid_payload_is_normalized() -> None:
    lead = LeadCreate.model_validate(lead_payload(name="  Jane Doe  ", phone="301.652.1234"))

    assert lead.name == "Jane Doe"
    assert lead.phone == "+13016521234"
    assert lead.interest is Interest.INVISALIGN


def test_optional_fields_default_to_unknown_and_other() -> None:
    payload = lead_payload()
    del payload["patient_type"], payload["interest"]

    lead = LeadCreate.model_validate(payload)

    assert lead.patient_type is PatientType.UNKNOWN
    assert lead.interest is Interest.OTHER


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("phone", "+44 20 7946 0958"),  # not a US number
        ("phone", "12345"),
        ("email", "not-an-email"),
        ("name", "   "),
        ("reason", "x" * 501),
        ("preferred_location", "baltimore"),
        ("interest", "braces_for_dogs"),
        ("contact_consent", False),
    ],
)
def test_invalid_values_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError) as exc_info:
        LeadCreate.model_validate(lead_payload(**{field: value}))

    assert exc_info.value.errors()[0]["loc"] == (field,)


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="extra"):
        LeadCreate.model_validate(lead_payload(date_of_birth="1990-01-01"))
