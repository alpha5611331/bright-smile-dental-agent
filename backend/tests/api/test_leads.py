from beanie import PydanticObjectId
from httpx import AsyncClient

from bright_smile.db.documents.lead import Lead
from bright_smile.domain.leads import LeadSource, LeadStatus, Priority
from bright_smile.domain.schedule import is_after_hours, sla_due_at
from tests.factories import lead_payload


async def test_form_fallback_creates_a_lead(client: AsyncClient) -> None:
    response = await client.post("/api/leads", json=lead_payload(interest="implant"))

    assert response.status_code == 201
    body = response.json()
    assert body["priority"] == "P2"
    lead = await Lead.get(PydanticObjectId(body["id"]))
    assert lead is not None
    assert lead.source is LeadSource.FORM
    assert lead.status is LeadStatus.NEW
    assert lead.conversation_id is None
    assert lead.phone == "+13016521234"
    assert lead.priority is Priority.P2
    assert lead.sla_due_at == sla_due_at(lead.created_at)
    assert lead.after_hours is is_after_hours(lead.created_at)


async def test_form_fallback_validates_input(client: AsyncClient) -> None:
    response = await client.post(
        "/api/leads", json=lead_payload(phone="12345", contact_consent=False)
    )

    assert response.status_code == 422
    fields = {tuple(d["loc"]) for d in response.json()["error"]["details"]}
    assert fields == {("body", "phone"), ("body", "contact_consent")}
