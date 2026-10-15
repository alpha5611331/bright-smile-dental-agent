"""Shared fixtures. Every test session uses its own throwaway MongoDB database."""

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from bright_smile.core.config import LogLevel, Settings
from bright_smile.core.logging import configure_logging
from bright_smile.core.rate_limit import RateLimiter
from bright_smile.main import create_app
from tests.factories import STAFF_PASSWORD, make_settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return make_settings()


@pytest.fixture(scope="session")
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(settings)
    async with LifespanManager(application):
        yield application
    cleanup: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        settings.mongodb_uri.get_secret_value()
    )
    await cleanup.drop_database(settings.mongodb_db)
    await cleanup.close()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


@pytest.fixture(autouse=True)
def _restore_logging() -> Iterator[None]:
    """Some tests reconfigure the global logger (JSON sink, production apps); undo it afterwards."""
    yield
    configure_logging(LogLevel.INFO, json_logs=False)


@pytest.fixture(autouse=True)
def _reset_rate_limits(request: pytest.FixtureRequest) -> None:
    """The app is shared across the session; start every test with fresh rate-limit windows."""
    if "app" in request.fixturenames:
        limiter: RateLimiter = request.getfixturevalue("app").state.rate_limiter
        limiter.reset()


@pytest.fixture
async def staff_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """A client with a valid staff session cookie."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        response = await http.post("/api/auth/login", json={"password": STAFF_PASSWORD})
        assert response.status_code == 204
        yield http
