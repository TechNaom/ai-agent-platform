"""Application settings, loaded from the environment (never hard-coded secrets)."""

from enum import StrEnum
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    CI = "ci"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ai-agent-platform"
    environment: Environment = Environment.LOCAL
    log_level: str = "INFO"
    database_url: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
