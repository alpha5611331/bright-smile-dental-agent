from typing import NoReturn

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from pymongo.errors import ServerSelectionTimeoutError

from bright_smile import main as main_module
from bright_smile.api.deps import get_mongo_client
from bright_smile.core.config import Environment, Settings
from bright_smile.core.errors import ErrorCode
from bright_smile.db.mongo import MongoClient, create_client
from bright_smile.main import create_app
from tests.factories import make_settings


async def test_health_ok_with_reachable_database(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


class _UnreachableAdmin:
    async def command(self, *_: object) -> NoReturn:
        raise ServerSelectionTimeoutError("simulated outage")


class _UnreachableClient:
    """Stands in for a MongoDB client whose server went away after startup."""

    admin = _UnreachableAdmin()


async def test_health_degraded_when_database_becomes_unreachable(
    app: FastAPI, client: AsyncClient
) -> None:
    app.dependency_overrides[get_mongo_client] = _UnreachableClient
    try:
        response = await client.get("/api/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "db": "unavailable"}


async def test_startup_fails_fast_and_closes_client_when_database_is_down(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    closed: list[bool] = []

    async def failing_init_db(*_: object) -> NoReturn:
        raise ServerSelectionTimeoutError("simulated outage")

    real_create_client = create_client

    def tracking_create_client(s: Settings) -> MongoClient:
        mongo = real_create_client(s)
        real_close = mongo.close

        async def close() -> None:
            closed.append(True)
            await real_close()

        monkeypatch.setattr(mongo, "close", close)
        return mongo

    monkeypatch.setattr(main_module, "init_db", failing_init_db)
    monkeypatch.setattr(main_module, "create_client", tracking_create_client)
    app = create_app(settings)

    with pytest.raises(ServerSelectionTimeoutError):
        async with LifespanManager(app):
            pass  # pragma: no cover

    assert closed == [True]


async def test_unknown_route_uses_error_contract(client: AsyncClient) -> None:
    response = await client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": ErrorCode.NOT_FOUND, "message": "Not Found", "details": []}
    }


async def test_docs_are_disabled_in_production() -> None:
    app = create_app(make_settings(environment=Environment.PRODUCTION))

    assert app.docs_url is None
    assert app.openapi_url is None
