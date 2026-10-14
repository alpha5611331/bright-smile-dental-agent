"""Test data builders shared across test modules."""

from typing import Any
from uuid import uuid4

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from bright_smile.core.config import Settings


class TestEnv(BaseSettings):
    """Test-only configuration, read from `TEST_*` environment variables."""

    __test__ = False  # not a test class
    model_config = SettingsConfigDict(env_prefix="TEST_", env_file=None)

    mongodb_uri: str = "mongodb://localhost:27017"


def make_settings(**overrides: Any) -> Settings:  # noqa: ANN401  # mirrors Settings' heterogeneous kwargs
    """Build isolated settings: no `.env` file, a unique database, and dummy secrets."""
    values: dict[str, Any] = {
        "openai_api_key": SecretStr("sk-test"),
        "mongodb_uri": SecretStr(TestEnv().mongodb_uri),
        "mongodb_db": f"bright_smile_test_{uuid4().hex[:12]}",
        "mongodb_server_selection_timeout_ms": 2000,
        "session_secret": SecretStr("x" * 32),
        "staff_password_hash": SecretStr("$argon2id$test"),
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)
