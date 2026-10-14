import json
import logging

import pytest
from loguru import logger

from bright_smile.core.config import LogLevel
from bright_smile.core.logging import configure_logging


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
