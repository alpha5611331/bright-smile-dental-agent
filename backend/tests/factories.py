"""Test data builders shared across test modules."""

from typing import Any
from uuid import uuid4

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from bright_smile.core.config import Settings
from bright_smile.core.security import hash_password

STAFF_PASSWORD = "correct horse battery staple"  # noqa: S105  # test-only credential
_STAFF_PASSWORD_HASH = hash_password(STAFF_PASSWORD)  # hashed once per test session


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
        "staff_password_hash": SecretStr(_STAFF_PASSWORD_HASH),
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def lead_payload(**overrides: Any) -> dict[str, Any]:  # noqa: ANN401  # JSON-like test payload
    """A valid appointment request as the API or the capture_lead tool would receive it."""
    payload: dict[str, Any] = {
        "name": "Jane Doe",
        "phone": "(301) 652-1234",
        "email": "jane.doe@example.com",
        "reason": "Interested in Invisalign",
        "preferred_location": "bethesda",
        "patient_type": "new",
        "interest": "invisalign",
        "contact_consent": True,
    }
    payload.update(overrides)
    return payload
