"""FastAPI application factory.

Run locally with `uv run fastapi dev src/bright_smile/main.py`, which serves the module-level `app`.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute
from loguru import logger

from bright_smile import __version__
from bright_smile.agent.graph import build_agent
from bright_smile.agent.llm import create_chat_model
from bright_smile.agent.tools import AGENT_TOOLS
from bright_smile.api.router import API_PREFIX, api_router
from bright_smile.core.config import Settings, get_settings
from bright_smile.core.errors import ErrorResponse, register_error_handlers
from bright_smile.core.logging import configure_logging
from bright_smile.core.rate_limit import RateLimiter
from bright_smile.core.security import SessionSigner
from bright_smile.db.mongo import create_client, init_db


def _operation_id(route: APIRoute) -> str:
    """Stable, readable operation IDs (e.g. `health-get_health`) for generated API clients."""
    return f"{route.tags[0]}-{route.name}" if route.tags else route.name


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Tests pass explicit settings; production loads them from the environment."""
    resolved = settings or get_settings()
    configure_logging(resolved.log_level, json_logs=resolved.is_production)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = create_client(resolved)
        app.state.settings = resolved
        app.state.mongo_client = client
        app.state.agent = build_agent(create_chat_model(resolved), AGENT_TOOLS)
        app.state.rate_limiter = RateLimiter()
        app.state.session_signer = SessionSigner(resolved.session_secret)
        try:
            await init_db(client, resolved)
            logger.info("startup_complete", environment=resolved.environment, version=__version__)
            yield
        finally:
            await client.close()
            logger.info("shutdown_complete")

    docs_enabled = not resolved.is_production
    app = FastAPI(
        title="Bright Smile Dental AI Front Desk API",
        version=__version__,
        lifespan=lifespan,
        docs_url=f"{API_PREFIX}/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url=f"{API_PREFIX}/openapi.json" if docs_enabled else None,
        responses={"default": {"model": ErrorResponse, "description": "Error"}},
        generate_unique_id_function=_operation_id,
    )
    register_error_handlers(app)
    app.include_router(api_router)
    return app


def __getattr__(name: str) -> FastAPI:
    """Lazily build `app` for ASGI servers, so importing this module never needs env vars."""
    if name == "app":
        return create_app()
    raise AttributeError(name)


def __dir__() -> list[str]:
    """List the lazy `app` too: `fastapi dev` and `fastapi run` look for it with `dir()`."""
    return [*globals(), "app"]
