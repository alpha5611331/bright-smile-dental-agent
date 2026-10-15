"""Single source of the current time, so time-dependent logic is easy to test."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
