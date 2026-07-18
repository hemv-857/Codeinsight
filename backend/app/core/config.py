from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and .env files."""

    app_name: str = Field(default="CodeInsight")
    conversation_database_path: Path = Field(
        default=Path("data/conversations/codeinsight-conversations.sqlite3")
    )
    cors_origins: str = Field(default="")
    embedding_batch_size: PositiveInt = Field(default=64)
    github_token: SecretStr | None = Field(default=None)
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_provider: Literal["openai", "ollama"] = Field(default="openai")
    environment: Literal["development", "test", "production"] = Field(default="development")
    graph_database_path: Path = Field(default=Path("data/graphs/codeinsight-graph.sqlite3"))
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    repository_clone_timeout_seconds: PositiveInt = Field(default=300)
    metadata_database_path: Path = Field(default=Path("data/codeinsight.sqlite3"))
    neo4j_database: str = Field(default="neo4j")
    neo4j_password: str = Field(default="codeinsight-dev")
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_username: str = Field(default="neo4j")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_embedding_model: str = Field(default="nomic-embed-text")
    openai_api_key: SecretStr | None = Field(default=None)
    llm_provider: Literal["ollama", "groq", "none"] = Field(default="ollama")
    groq_api_key: SecretStr | None = Field(default=None)
    ollama_chat_model: str = Field(default="llama3.2")
    groq_chat_model: str = Field(default="llama-3.3-70b-versatile")
    parser_provider: Literal["safe", "tree_sitter"] = Field(default="tree_sitter")
    repository_chunk_max_chars: PositiveInt = Field(default=12_000)
    repository_storage_path: Path = Field(default=Path("data/repositories"))
    repository_zip_max_bytes: PositiveInt = Field(default=100 * 1024 * 1024)
    vector_database_path: Path = Field(default=Path("data/vectors/codeinsight-vectors.sqlite3"))
    version: str = Field(default="0.1.0")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CODEINSIGHT_",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_cached_settings() -> Settings:
    """Return process-wide settings for dependency injection."""
    return Settings()
