import pytest
from pydantic import SecretStr, ValidationError

from bright_smile.core.config import Environment, LogLevel, Settings
from tests.factories import make_settings


def test_defaults_are_applied() -> None:
    settings = make_settings()

    assert settings.openai_model == "gpt-5.4-mini"
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.log_level is LogLevel.INFO
    assert settings.trust_proxy_headers is False
    assert settings.is_production is False


def test_secrets_are_masked_in_repr() -> None:
    settings = make_settings(openai_api_key=SecretStr("sk-very-secret"))

    assert "sk-very-secret" not in repr(settings)
    assert settings.openai_api_key.get_secret_value() == "sk-very-secret"


def test_production_flag() -> None:
    assert make_settings(environment=Environment.PRODUCTION).is_production is True


def test_short_session_secret_is_rejected() -> None:
    with pytest.raises(ValidationError, match="session_secret"):
        make_settings(session_secret=SecretStr("too-short"))


def test_invalid_database_name_is_rejected() -> None:
    with pytest.raises(ValidationError, match="mongodb_db"):
        make_settings(mongodb_db="bad name!")


def test_missing_required_values_fail_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("OPENAI_API_KEY", "MONGODB_URI", "SESSION_SECRET", "STAFF_PASSWORD_HASH"):
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    missing = {str(err["loc"][0]) for err in exc_info.value.errors()}
    assert missing == {"openai_api_key", "mongodb_uri", "session_secret", "staff_password_hash"}


def test_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setenv("MONGODB_URI", "mongodb://example:27017")
    monkeypatch.setenv("SESSION_SECRET", "s" * 40)
    monkeypatch.setenv("STAFF_PASSWORD_HASH", "$argon2id$hash")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    settings = Settings(_env_file=None)

    assert settings.environment is Environment.PRODUCTION
    assert settings.log_level is LogLevel.WARNING
    assert settings.openai_api_key.get_secret_value() == "sk-env"
