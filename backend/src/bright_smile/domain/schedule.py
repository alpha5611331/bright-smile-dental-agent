"""Callback SLA and after-hours rules in practice time, America/New_York (SPEC section 6.4)."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

PRACTICE_TZ = ZoneInfo("America/New_York")
SLA_DEADLINE = time(17, 0)

# Windows when at least one office is certainly open, by weekday (Monday = 0).
# Friday: Rockville is open until 5 PM (Bethesda closes at 3 PM).
# Saturday: 9 AM to 1 PM, the overlap of the two conflicting Bethesda Saturday ranges in the KB.
OPEN_WINDOWS: dict[int, tuple[time, time]] = {
    0: (time(8, 0), time(17, 0)),
    1: (time(8, 0), time(17, 0)),
    2: (time(8, 0), time(17, 0)),
    3: (time(8, 0), time(17, 0)),
    4: (time(8, 0), time(17, 0)),
    5: (time(9, 0), time(13, 0)),
}


def _require_aware(moment: datetime) -> None:
    if moment.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")


def _is_business_day(day: date) -> bool:
    return day.weekday() < 5  # Monday to Friday; holidays are out of scope (SPEC 1.2)


def sla_due_at(created_at: datetime) -> datetime:
    """5:00 PM practice time on the next business day after `created_at`, returned in UTC."""
    _require_aware(created_at)
    day = created_at.astimezone(PRACTICE_TZ).date() + timedelta(days=1)
    while not _is_business_day(day):
        day += timedelta(days=1)
    return datetime.combine(day, SLA_DEADLINE, tzinfo=PRACTICE_TZ).astimezone(UTC)


def is_after_hours(moment: datetime) -> bool:
    """True when neither office is certainly open at `moment`."""
    _require_aware(moment)
    local = moment.astimezone(PRACTICE_TZ)
    window = OPEN_WINDOWS.get(local.weekday())
    if window is None:
        return True
    opens, closes = window
    return not (opens <= local.time() < closes)


def is_overdue(sla_due: datetime, now: datetime) -> bool:
    _require_aware(sla_due)
    _require_aware(now)
    return now > sla_due
