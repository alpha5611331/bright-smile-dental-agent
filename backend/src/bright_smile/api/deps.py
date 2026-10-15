"""FastAPI dependencies shared across routers."""

from collections.abc import Awaitable, Callable
from typing import Annotated, cast

from fastapi import Depends, Request

from bright_smile.agent.graph import Agent
from bright_smile.core.config import Settings
from bright_smile.core.errors import AppError, ErrorCode
from bright_smile.core.rate_limit import Policy, RateLimiter
from bright_smile.core.security import SESSION_COOKIE, SessionSigner
from bright_smile.db.mongo import MongoClient


def get_app_settings(request: Request) -> Settings:
    return cast("Settings", request.app.state.settings)


def get_mongo_client(request: Request) -> MongoClient:
    return cast("MongoClient", request.app.state.mongo_client)


def get_agent(request: Request) -> Agent:
    return cast("Agent", request.app.state.agent)


def get_rate_limiter(request: Request) -> RateLimiter:
    return cast("RateLimiter", request.app.state.rate_limiter)


def get_session_signer(request: Request) -> SessionSigner:
    return cast("SessionSigner", request.app.state.session_signer)


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
MongoClientDep = Annotated[MongoClient, Depends(get_mongo_client)]
AgentDep = Annotated[Agent, Depends(get_agent)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]
SessionSignerDep = Annotated[SessionSigner, Depends(get_session_signer)]


def client_ip(request: Request, settings: SettingsDep) -> str:
    """Client address; the first X-Forwarded-For hop is trusted only behind a known proxy."""
    if settings.trust_proxy_headers and (forwarded := request.headers.get("x-forwarded-for")):
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


ClientIpDep = Annotated[str, Depends(client_ip)]


def rate_limit(policy: Policy) -> Callable[..., Awaitable[None]]:
    """Dependency factory enforcing a rate-limit policy per client IP (SPEC section 10.2)."""

    async def enforce(limiter: RateLimiterDep, ip: ClientIpDep) -> None:
        retry_after = limiter.hit(policy, ip)
        if retry_after is not None:
            raise AppError(
                ErrorCode.RATE_LIMITED,
                "Too many requests. Please wait a moment and try again.",
                headers={"Retry-After": str(retry_after)},
            )

    return enforce


async def require_staff(request: Request, signer: SessionSignerDep) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token or not signer.verify(token):
        raise AppError(ErrorCode.UNAUTHORIZED, "Staff login required")


StaffOnly = Depends(require_staff)
