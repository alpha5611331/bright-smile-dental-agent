"""Live evaluation fixtures: the real OpenAI model behind the real API (SPEC section 11.1).

Run with `uv run pytest -m eval`. Needs OPENAI_API_KEY in the environment or backend/.env and a
local MongoDB. Without a usable key every eval is skipped, never failed.
"""

import json
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from uuid import UUID

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import AsyncMongoClient

from bright_smile.main import create_app
from tests.factories import make_settings


class EvalEnv(BaseSettings):
    """Reads the real key and model from the environment or backend/.env."""

    __test__ = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"


def _usable_key(key: str) -> bool:
    return key.startswith("sk-") and "replace" not in key


@pytest.fixture(scope="session")
def eval_env() -> EvalEnv:
    env = EvalEnv()
    if not _usable_key(env.openai_api_key):
        pytest.skip("OPENAI_API_KEY is not set to a real key; live evals skipped")
    return env


@pytest.fixture(scope="session")
async def live_client(eval_env: EvalEnv) -> AsyncIterator[AsyncClient]:
    settings = make_settings(
        openai_api_key=SecretStr(eval_env.openai_api_key),
        openai_model=eval_env.openai_model,
    )
    app = create_app(settings)
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://eval", timeout=90) as http,
    ):
        app.state.rate_limiter.policies = {}  # evals are not traffic; never rate limit them
        yield http
    cleanup: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        settings.mongodb_uri.get_secret_value()
    )
    await cleanup.drop_database(settings.mongodb_db)
    await cleanup.close()


class Turn:
    """One assistant turn: the reply text and the events that came with it."""

    def __init__(self, events: list[tuple[str, dict[str, Any]]]) -> None:
        self.events = events
        self.names = [name for name, _ in events]
        self.reply = "".join(data["text"] for name, data in events if name == "token")
        self.conversation_id = UUID(events[0][1]["conversation_id"])

    def payload(self, name: str) -> dict[str, Any] | None:
        return next((data for event, data in self.events if event == name), None)

    def __repr__(self) -> str:  # shown by pytest when an assertion fails
        return f"Turn(events={self.names}, reply={self.reply!r})"


type Ask = Callable[..., Coroutine[Any, Any, Turn]]


@pytest.fixture
def ask(live_client: AsyncClient) -> Ask:
    async def _ask(message: str, conversation_id: UUID | None = None) -> Turn:
        payload: dict[str, str] = {"message": message}
        if conversation_id:
            payload["conversation_id"] = str(conversation_id)
        response = await live_client.post("/api/chat", json=payload)
        assert response.status_code == 200, response.text
        events: list[tuple[str, dict[str, Any]]] = []
        for block in response.text.replace("\r\n", "\n").strip().split("\n\n"):
            fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
            if "event" in fields:
                events.append((fields["event"], json.loads(fields["data"])))
        turn = Turn(events)
        assert turn.names[-1] == "done", f"turn did not finish: {turn!r}"
        return turn

    return _ask
