from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and .env files."""

    app_name: str = Field(default="Forge AI")
    environment: Literal["development", "test", "production"] = Field(default="development")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    version: str = Field(default="0.1.0")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FORGE_AI_",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_cached_settings() -> Settings:
    """Return process-wide settings for dependency injection."""
    return Settings()
