"""Staff session endpoints (SPEC sections 3 US-6, 7.4)."""

from fastapi import APIRouter, Depends, Response, status
from fastapi.concurrency import run_in_threadpool

from bright_smile.api.deps import SessionSignerDep, SettingsDep, StaffOnly, rate_limit
from bright_smile.core.errors import AppError, ErrorCode, error_responses
from bright_smile.core.rate_limit import Policy
from bright_smile.core.security import SESSION_COOKIE, verify_password
from bright_smile.schemas.auth import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log in with the staff password and receive a session cookie",
    dependencies=[Depends(rate_limit(Policy.LOGIN))],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS),
)
async def login(
    body: LoginRequest, settings: SettingsDep, signer: SessionSignerDep, response: Response
) -> None:
    valid = await run_in_threadpool(
        verify_password,
        body.password.get_secret_value(),
        settings.staff_password_hash.get_secret_value(),
    )
    if not valid:
        raise AppError(ErrorCode.UNAUTHORIZED, "Incorrect password")
    response.set_cookie(
        SESSION_COOKIE,
        signer.issue(),
        max_age=int(signer.max_age.total_seconds()),
        path="/",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="End the staff session")
async def logout(settings: SettingsDep, response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, secure=settings.is_production, samesite="lax"
    )


@router.get(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Check whether the staff session is valid",
    dependencies=[StaffOnly],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def me() -> None:
    return None
