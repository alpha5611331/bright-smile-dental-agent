from datetime import UTC, datetime, timedelta

import pytest

from bright_smile.domain.schedule import PRACTICE_TZ, is_after_hours, is_overdue, sla_due_at


def et(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=PRACTICE_TZ)


@pytest.mark.parametrize(
    ("created", "due"),
    [
        (et(2026, 10, 13, 10), et(2026, 10, 14, 17)),  # Tue 10 AM -> Wed 5 PM
        (et(2026, 10, 16, 18), et(2026, 10, 19, 17)),  # Fri 6 PM -> Mon 5 PM
        (et(2026, 10, 17, 11), et(2026, 10, 19, 17)),  # Sat -> Mon
        (et(2026, 10, 18, 23, 59), et(2026, 10, 19, 17)),  # Sun late -> Mon
        (et(2026, 10, 15, 0, 1), et(2026, 10, 16, 17)),  # Thu just after midnight -> Fri
    ],
)
def test_sla_is_5pm_next_business_day(created: datetime, due: datetime) -> None:
    assert sla_due_at(created) == due
    assert sla_due_at(created).tzinfo is UTC


def test_sla_uses_practice_time_not_utc() -> None:
    # Tue 11 PM in New York is already Wednesday in UTC; the SLA is still Wednesday 5 PM ET.
    created_utc = et(2026, 10, 13, 23).astimezone(UTC)
    assert created_utc.weekday() == 2

    assert sla_due_at(created_utc) == et(2026, 10, 14, 17)


def test_sla_across_daylight_saving_start() -> None:
    # Clocks spring forward on Sunday 2026-03-08: Friday 5 PM is EST, Monday 5 PM is EDT.
    due = sla_due_at(et(2026, 3, 6, 12))

    assert due == et(2026, 3, 9, 17)
    assert due == datetime(2026, 3, 9, 21, 0, tzinfo=UTC)


def test_sla_across_daylight_saving_end() -> None:
    due = sla_due_at(et(2026, 10, 30, 12))  # Friday before the 2026-11-01 fall back

    assert due == datetime(2026, 11, 2, 22, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("moment", "after_hours"),
    [
        (et(2026, 10, 14, 7, 59), True),  # Wed before opening
        (et(2026, 10, 14, 8, 0), False),  # Wed opening
        (et(2026, 10, 14, 16, 59), False),
        (et(2026, 10, 14, 17, 0), True),  # Wed closing
        (et(2026, 10, 16, 16, 0), False),  # Fri 4 PM: Rockville still open
        (et(2026, 10, 17, 8, 30), True),  # Sat before the certain window
        (et(2026, 10, 17, 9, 0), False),  # Sat 9 AM to 1 PM
        (et(2026, 10, 17, 13, 0), True),
        (et(2026, 10, 18, 11, 0), True),  # Sunday
    ],
)
def test_after_hours(moment: datetime, after_hours: bool) -> None:
    assert is_after_hours(moment) is after_hours


def test_overdue() -> None:
    due = et(2026, 10, 14, 17)

    assert is_overdue(due, due + timedelta(seconds=1)) is True
    assert is_overdue(due, due) is False


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        sla_due_at(datetime(2026, 10, 14, 12))  # noqa: DTZ001  # intentionally naive
