"""Seed a scratch database with a front desk's week of appointment requests, off camera.

Not part of the product. Run from the backend so the app's own rules compute every
priority, SLA, and after-hours flag (nothing here decides them):

    MONGODB_DB=bright_smile_recording uv run --directory backend python ../scripts/videos/seed.py

It drops the `leads` and `conversations` collections first, so it refuses any database
whose name does not contain "recording". Every time is relative to the moment it runs,
so the dashboard reads the same way whatever day the take is made. The people are made
up: phone numbers are in the 555-01xx range reserved for fiction, emails are example.com.
"""

import asyncio
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from loguru import logger

from bright_smile.core.config import get_settings
from bright_smile.db.documents.conversation import Conversation
from bright_smile.db.documents.lead import Lead
from bright_smile.db.mongo import create_client, init_db
from bright_smile.domain.leads import (
    Interest,
    LeadSource,
    LeadStatus,
    PatientType,
    PreferredLocation,
)
from bright_smile.domain.schedule import PRACTICE_TZ, is_after_hours
from bright_smile.schemas.leads import LeadCreate
from bright_smile.services.leads import create_lead


def business_days_ago(now: datetime, days: int, at: time) -> datetime:
    """`at` practice time on the business day `days` business days before `now`."""
    day = now.astimezone(PRACTICE_TZ).date()
    while days:
        day -= timedelta(days=1)
        if day.weekday() < 5:
            days -= 1
    return datetime.combine(day, at, tzinfo=PRACTICE_TZ).astimezone(UTC)


def latest_after_hours(now: datetime, at_least: timedelta) -> datetime:
    """The most recent moment, at least `at_least` ago, when both offices were closed."""
    moment = (now - at_least).replace(second=0, microsecond=0)
    while not is_after_hours(moment):
        moment -= timedelta(minutes=10)
    return moment


@dataclass(frozen=True)
class Seed:
    name: str
    phone: str
    email: str
    reason: str
    location: PreferredLocation
    patient_type: PatientType
    interest: Interest
    created_at: datetime
    status: LeadStatus = LeadStatus.NEW
    notes: str = ""


def the_week(now: datetime) -> list[Seed]:
    return [
        Seed(
            "Maria Lopez",
            "+13015550111",
            "maria.lopez@example.com",
            "Cracked a front tooth this morning, it is sore when I bite.",
            PreferredLocation.ROCKVILLE,
            PatientType.EXISTING,
            Interest.EMERGENCY,
            now - timedelta(minutes=35),
        ),
        Seed(
            "David Chen",
            "+12405550112",
            "david.chen@example.com",
            "Missing a lower molar, want to talk about an implant.",
            PreferredLocation.BETHESDA,
            PatientType.EXISTING,
            Interest.IMPLANT,
            business_days_ago(now, 2, time(11, 5)),
        ),
        Seed(
            "Priya Raman",
            "+13015550113",
            "priya.raman@example.com",
            "Interested in the free Invisalign consultation.",
            PreferredLocation.BETHESDA,
            PatientType.NEW,
            Interest.INVISALIGN,
            latest_after_hours(now, timedelta(hours=1)),
        ),
        Seed(
            "Tom Becker",
            "+12405550114",
            "tom.becker@example.com",
            "Dentist said I need a crown on an upper tooth.",
            PreferredLocation.ROCKVILLE,
            PatientType.EXISTING,
            Interest.CROWN,
            business_days_ago(now, 1, time(14, 10)),
            status=LeadStatus.CONTACTED,
            notes="Left a voicemail. Try again after 4 PM.",
        ),
        Seed(
            "Aisha Khan",
            "+13015550115",
            "aisha.khan@example.com",
            "Just moved to Bethesda, looking for a new family dentist.",
            PreferredLocation.BETHESDA,
            PatientType.NEW,
            Interest.NEW_PATIENT_EXAM,
            now - timedelta(hours=2, minutes=10),
        ),
        Seed(
            "Emily Park",
            "+12405550116",
            "emily.park@example.com",
            "Would like teeth whitening before a wedding.",
            PreferredLocation.NO_PREFERENCE,
            PatientType.EXISTING,
            Interest.WHITENING,
            now - timedelta(hours=5, minutes=20),
        ),
        Seed(
            "Robert Hill",
            "+13015550117",
            "robert.hill@example.com",
            "Six-month cleaning.",
            PreferredLocation.ROCKVILLE,
            PatientType.EXISTING,
            Interest.CLEANING,
            business_days_ago(now, 3, time(9, 40)),
            status=LeadStatus.SCHEDULED,
            notes="Booked for a cleaning next Tuesday at 10 AM.",
        ),
        Seed(
            "Grace Liu",
            "+12405550118",
            "grace.liu@example.com",
            "Asked whether we take her HMO plan.",
            PreferredLocation.NO_PREFERENCE,
            PatientType.UNKNOWN,
            Interest.INSURANCE_QUESTION,
            business_days_ago(now, 4, time(16, 20)),
            status=LeadStatus.NOT_INTERESTED,
            notes="HMO plan, not accepted. Mentioned the membership plan.",
        ),
    ]


async def main() -> None:
    logger.remove()  # the app's own lead_created lines are noise here; keep a plain summary
    logger.add(sys.stdout, format="{message}", filter="__main__")
    settings = get_settings()
    if "recording" not in settings.mongodb_db:
        raise SystemExit(
            f"Refusing to seed {settings.mongodb_db!r}: it drops leads and conversations. "
            "Point MONGODB_DB at a scratch database whose name contains 'recording'."
        )
    client = create_client(settings)
    try:
        await init_db(client, settings)
        await Lead.get_pymongo_collection().delete_many({})
        await Conversation.get_pymongo_collection().delete_many({})

        now = datetime.now(UTC)
        for seed in the_week(now):
            lead = await create_lead(
                LeadCreate(
                    name=seed.name,
                    phone=seed.phone,
                    email=seed.email,
                    reason=seed.reason,
                    preferred_location=seed.location,
                    patient_type=seed.patient_type,
                    interest=seed.interest,
                    contact_consent=True,
                ),
                source=LeadSource.FORM,
                now=seed.created_at,
            )
            if seed.status is not LeadStatus.NEW or seed.notes:
                lead.status = seed.status
                lead.notes = seed.notes
                if seed.status is not LeadStatus.NEW:
                    lead.contacted_at = seed.created_at + timedelta(hours=3)
                await lead.save()
            logger.info(
                "  {} {:<12} {:<15} after_hours={}",
                lead.priority,
                seed.name,
                seed.status,
                lead.after_hours,
            )
        logger.info("Seeded {} leads into {}.", len(the_week(now)), settings.mongodb_db)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
