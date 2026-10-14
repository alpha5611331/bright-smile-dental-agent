"""Shared error contract: every non-2xx JSON response uses `ErrorResponse` (SPEC section 7.3)."""

from collections.abc import Mapping
from enum import StrEnum
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    CONVERSATION_LIMIT = "conversation_limit"
    UPSTREAM_UNAVAILABLE = "upstream_unavailable"
    INTERNAL_ERROR = "internal_error"


STATUS_FOR_CODE: dict[ErrorCode, HTTPStatus] = {
    ErrorCode.VALIDATION_ERROR: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.UNAUTHORIZED: HTTPStatus.UNAUTHORIZED,
    ErrorCode.NOT_FOUND: HTTPStatus.NOT_FOUND,
    ErrorCode.RATE_LIMITED: HTTPStatus.TOO_MANY_REQUESTS,
    ErrorCode.CONVERSATION_LIMIT: HTTPStatus.CONFLICT,
    ErrorCode.UPSTREAM_UNAVAILABLE: HTTPStatus.SERVICE_UNAVAILABLE,
    ErrorCode.INTERNAL_ERROR: HTTPStatus.INTERNAL_SERVER_ERROR,
}

_CODE_FOR_STATUS: dict[int, ErrorCode] = {s.value: c for c, s in STATUS_FOR_CODE.items()}


class ValidationIssue(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str = Field(min_length=1)
    details: list[ValidationIssue] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorBody


class AppError(Exception):
    """Raise anywhere in request handling to return a structured error response."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.headers = headers

    @property
    def status_code(self) -> int:
        return STATUS_FOR_CODE[self.code].value


def error_response(
    code: ErrorCode,
    message: str,
    *,
    status_code: int | None = None,
    details: list[ValidationIssue] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or []))
    return JSONResponse(
        status_code=status_code or STATUS_FOR_CODE[code].value,
        content=jsonable_encoder(body),
        headers=headers,
    )


async def _app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):  # pragma: no cover - registered for AppError only
        raise exc
    return error_response(exc.code, exc.message, headers=exc.headers)


async def _validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):  # pragma: no cover
        raise exc
    details = [
        ValidationIssue(
            loc=list(err.get("loc", ())), msg=err.get("msg", ""), type=err.get("type", "")
        )
        for err in exc.errors()
    ]
    return error_response(ErrorCode.VALIDATION_ERROR, "Request validation failed", details=details)


async def _http_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):  # pragma: no cover
        raise exc
    code = _CODE_FOR_STATUS.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    message = exc.detail or HTTPStatus(exc.status_code).phrase
    return error_response(code, message, status_code=exc.status_code, headers=exc.headers)


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.opt(exception=exc).error(
        "unhandled_error", path=request.url.path, error_type=type(exc).__name__
    )
    return error_response(ErrorCode.INTERNAL_ERROR, "Internal server error")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
