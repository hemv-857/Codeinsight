from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and .env files."""

    app_name: str = Field(default="Forge AI")
    environment: Literal["development", "test", "production"] = Field(default="development")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    repository_clone_timeout_seconds: PositiveInt = Field(default=300)
    repository_storage_path: Path = Field(default=Path("data/repositories"))
    repository_zip_max_bytes: PositiveInt = Field(default=100 * 1024 * 1024)
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
