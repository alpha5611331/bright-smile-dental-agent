"""Application settings loaded from the environment with pydantic-settings.

This is the only module that reads environment variables. Everything else receives a
`Settings` instance through `get_settings()` or the FastAPI dependency.
"""

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ReasoningEffort(StrEnum):
    """OpenAI reasoning effort. Reasoning tokens count toward the output cap, so chat stays low."""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Settings(BaseSettings):
    """Validated runtime configuration. See SPEC section 12.1."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        env_parse_none_str="",  # an empty value (e.g. OPENAI_REASONING_EFFORT=) means "unset"
    )

    openai_api_key: SecretStr
    openai_model: str = Field(default="gpt-5.4-mini", min_length=1)
    openai_reasoning_effort: ReasoningEffort | None = ReasoningEffort.LOW
    openai_timeout_seconds: float = Field(default=30.0, gt=0, le=120)

    mongodb_uri: SecretStr
    mongodb_db: str = Field(default="bright_smile", min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    mongodb_server_selection_timeout_ms: int = Field(default=5000, ge=100, le=60_000)

    session_secret: SecretStr = Field(min_length=32)
    staff_password_hash: SecretStr

    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.INFO
    trust_proxy_headers: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once and validated at startup."""
    return Settings()
