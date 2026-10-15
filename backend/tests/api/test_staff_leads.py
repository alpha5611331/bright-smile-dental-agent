from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
from httpx import AsyncClient

from bright_smile.core.clock import utc_now
from bright_smile.db.documents.conversation import Conversation, MessageRole
from bright_smile.db.documents.lead import Lead
from bright_smile.domain.flags import Flag
from bright_smile.domain.leads import LeadSource, LeadStatus
from bright_smile.schemas.leads import LeadCreate
from bright_smile.services.leads import create_lead
from tests.factories import lead_payload


@pytest.fixture
async def clean_leads() -> AsyncIterator[None]:
    """Staff views aggregate over the whole collection, so each test starts from zero."""
    await Lead.delete_all()
    yield
    await Lead.delete_all()


async def make_lead(**overrides: object) -> Lead:
    return await create_lead(
        LeadCreate.model_validate(lead_payload(**overrides)), source=LeadSource.FORM
    )


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/leads"),
        ("GET", "/api/leads/507f1f77bcf86cd799439011"),
        ("PATCH", "/api/leads/507f1f77bcf86cd799439011"),
        ("GET", "/api/stats"),
    ],
)
async def test_staff_endpoints_require_a_session(
    client: AsyncClient, method: str, path: str
) -> None:
    response = await client.request(method, path, json={} if method == "PATCH" else None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


@pytest.mark.usefixtures("clean_leads")
async def test_default_view_sorts_by_priority_then_oldest(staff_client: AsyncClient) -> None:
    cleaning = await make_lead(interest="cleaning", patient_type="existing")  # P4
    implant = await make_lead(interest="implant")  # P2, older
    crown = await make_lead(interest="crown")  # P2, newer

    body = (await staff_client.get("/api/leads")).json()

    assert [item["id"] for item in body["items"]] == [
        str(implant.id),
        str(crown.id),
        str(cleaning.id),
    ]
    assert body["total"] == 3
    assert body["items"][0]["overdue"] is False


@pytest.mark.usefixtures("clean_leads")
async def test_filters_and_pagination(staff_client: AsyncClient) -> None:
    for _ in range(3):
        await make_lead(preferred_location="rockville", interest="cleaning", patient_type="new")
    await make_lead(preferred_location="bethesda")

    page = (
        await staff_client.get("/api/leads", params={"location": "rockville", "page_size": 2})
    ).json()
    by_priority = (
        await staff_client.get("/api/leads", params=[("priority", "P2"), ("priority", "P1")])
    ).json()

    assert (page["total"], len(page["items"]), page["page"]) == (3, 2, 1)
    assert by_priority["total"] == 1
    assert (await staff_client.get("/api/leads", params={"page_size": 101})).status_code == 422


@pytest.mark.usefixtures("clean_leads")
async def test_detail_includes_transcript_and_flags(staff_client: AsyncClient) -> None:
    conversation = Conversation(flags=[Flag.EMERGENCY])
    conversation.append(MessageRole.USER, "My jaw is swollen")
    conversation.append(MessageRole.ASSISTANT, "Please go to the nearest emergency room.")
    await conversation.insert()
    lead = await create_lead(
        LeadCreate.model_validate(lead_payload()), source=LeadSource.CHAT, conversation=conversation
    )

    detail = (await staff_client.get(f"/api/leads/{lead.id}")).json()

    assert detail["priority"] == "P1"
    assert detail["flags"] == ["emergency"]
    assert [m["role"] for m in detail["transcript"]] == ["user", "assistant"]


@pytest.mark.parametrize("lead_id", ["not-an-object-id", "507f1f77bcf86cd799439011"])
async def test_unknown_lead_is_404(staff_client: AsyncClient, lead_id: str) -> None:
    response = await staff_client.get(f"/api/leads/{lead_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.usefixtures("clean_leads")
async def test_status_changes_set_contacted_at_once(staff_client: AsyncClient) -> None:
    lead = await make_lead()

    contacted = (
        await staff_client.patch(f"/api/leads/{lead.id}", json={"status": "contacted"})
    ).json()
    scheduled = (
        await staff_client.patch(
            f"/api/leads/{lead.id}", json={"status": "scheduled", "notes": " Booked Tue 10am "}
        )
    ).json()

    assert contacted["status"] == "contacted"
    assert contacted["contacted_at"] is not None
    assert scheduled["status"] == "scheduled"
    assert scheduled["contacted_at"] == contacted["contacted_at"]
    assert scheduled["notes"] == "Booked Tue 10am"


async def test_invalid_updates_are_rejected(staff_client: AsyncClient) -> None:
    lead = await make_lead()

    bad_status = await staff_client.patch(f"/api/leads/{lead.id}", json={"status": "archived"})
    extra_field = await staff_client.patch(f"/api/leads/{lead.id}", json={"priority": "P1"})

    assert bad_status.status_code == 422
    assert extra_field.status_code == 422


async def test_non_json_bodies_are_rejected(staff_client: AsyncClient) -> None:
    """Cross-site forms can only send form or text bodies; JSON-only endpoints block CSRF."""
    lead = await make_lead()

    response = await staff_client.patch(
        f"/api/leads/{lead.id}",
        content='{"status": "contacted"}',
        headers={"content-type": "text/plain"},
    )

    assert response.status_code == 422


@pytest.mark.usefixtures("clean_leads")
async def test_stats(staff_client: AsyncClient) -> None:
    await make_lead(interest="invisalign")  # open P2, created now
    await create_lead(  # still new five days later: overdue
        LeadCreate.model_validate(lead_payload(interest="cleaning")),
        source=LeadSource.FORM,
        now=utc_now() - timedelta(days=5),
    )
    done = await make_lead(interest="implant")  # P2 but no longer open
    done.status = LeadStatus.SCHEDULED
    await done.save()
    after_hours = await Lead.find(Lead.after_hours == True).count()  # noqa: E712  # Beanie query

    stats = (await staff_client.get("/api/stats")).json()

    assert stats == {
        "new_today": 2,
        "overdue": 1,
        "open_high_value": 1,
        "after_hours_share": round(after_hours / 3, 2),
    }


async def test_stats_with_no_leads(staff_client: AsyncClient, clean_leads: None) -> None:
    assert (await staff_client.get("/api/stats")).json()["after_hours_share"] == 0.0
