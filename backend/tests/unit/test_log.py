import json
import logging
from collections.abc import Iterator

import pytest
from loguru import logger

from bright_smile.core.config import LogLevel
from bright_smile.core.logging import configure_logging
from bright_smile.domain.flags import Flag
from bright_smile.domain.leads import Priority


@pytest.fixture(autouse=True)
def restore_logging() -> Iterator[None]:
    """These tests reconfigure the global logger; restore readable logs for the rest of the run."""
    yield
    configure_logging(LogLevel.INFO, json_logs=False)


def test_json_logs_include_structured_fields(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(LogLevel.INFO, json_logs=True)

    logger.info("lead_captured", lead_id="abc123", priority="P2")
    logger.complete()

    line = capsys.readouterr().out.strip().splitlines()[-1]
    record = json.loads(line)
    assert record["event"] == "lead_captured"
    assert record["level"] == "INFO"
    assert record["lead_id"] == "abc123"
    assert record["priority"] == "P2"
    assert record["ts"].endswith("+00:00")


def test_enum_fields_are_logged_as_plain_values(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(LogLevel.INFO, json_logs=True)

    logger.info("lead_created", priority=Priority.P1, flags=[Flag.EMERGENCY])
    logger.complete()

    record = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert record["priority"] == "P1"
    assert record["flags"] == ["emergency"]


def test_stdlib_logs_are_intercepted(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(LogLevel.INFO, json_logs=True)

    logging.getLogger("uvicorn.error").warning("server_warning")
    logger.complete()

    record = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert record["event"] == "server_warning"
    assert record["logger"] == "uvicorn.error"
    assert record["level"] == "WARNING"


def test_level_filters_lower_records(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(LogLevel.WARNING, json_logs=True)

    logger.info("should_not_appear")
    logger.complete()

    assert "should_not_appear" not in capsys.readouterr().out
