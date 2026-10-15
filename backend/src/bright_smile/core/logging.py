"""Logging configuration (loguru).

- Development: colored, human-readable lines on stderr.
- Production: one JSON object per line on stdout, written from a background queue.
- Standard-library loggers (uvicorn, pymongo, httpx, ...) are intercepted and routed through loguru.
- `diagnose` is off in production so tracebacks never include local variable values (possible PII).

Never log message content or personal data (SPEC section 10.1). Pass context as keyword fields:
`logger.info("lead_captured", lead_id=lead_id, priority=priority)`.
"""

import inspect
import json
import logging
import sys
from datetime import UTC
from enum import Enum
from typing import TYPE_CHECKING, override

from loguru import logger

from bright_smile.core.config import LogLevel

if TYPE_CHECKING:
    from loguru import Message, Record

_INTERCEPTED_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "pymongo", "httpx")
_LOGGER_NAME_KEY = "logger_name"
_DEV_FORMAT = (
    "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan> | <level>{message}</level>"
)


class InterceptHandler(logging.Handler):
    """Forward standard-library log records to loguru, preserving level and caller."""

    @override
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame is not None and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).bind(
            **{_LOGGER_NAME_KEY: record.name}
        ).log(level, record.getMessage())


def _normalize_record(record: "Record") -> None:
    """Report intercepted records under their original logger name (e.g. `uvicorn.access`) and
    render enum fields as their plain values in every sink."""
    if (name := record["extra"].pop(_LOGGER_NAME_KEY, None)) is not None:
        record["name"] = str(name)
    for key, value in record["extra"].items():
        if isinstance(value, Enum):
            record["extra"][key] = value.value
        elif isinstance(value, list) and any(isinstance(v, Enum) for v in value):
            record["extra"][key] = [v.value if isinstance(v, Enum) else v for v in value]


def _dev_format(record: "Record") -> str:
    """Human-readable line; structured fields are appended only when present."""
    suffix = " | <dim>{extra}</dim>" if record["extra"] else ""
    return _DEV_FORMAT + suffix + "\n{exception}"


def _serialize(record: "Record") -> str:
    payload: dict[str, object] = {
        "ts": record["time"].astimezone(UTC).isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "event": record["message"],
        **record["extra"],
    }
    if record["exception"] is not None:
        exc_type = record["exception"].type
        payload["error_type"] = exc_type.__name__ if exc_type else None
    return json.dumps(payload, default=str)


def _json_sink(message: "Message") -> None:
    sys.stdout.write(_serialize(message.record) + "\n")
    sys.stdout.flush()


def configure_logging(level: LogLevel, *, json_logs: bool) -> None:
    """Install loguru sinks and route standard logging through them. Safe to call repeatedly."""
    logger.remove()
    logger.configure(patcher=_normalize_record)
    if json_logs:
        logger.add(_json_sink, level=level.value, enqueue=True, backtrace=False, diagnose=False)
    else:
        logger.add(sys.stderr, level=level.value, format=_dev_format, backtrace=True, diagnose=True)

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in _INTERCEPTED_LOGGERS:
        std_logger = logging.getLogger(name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False
