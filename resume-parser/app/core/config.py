"""Environment-backed application settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Resume Intelligence API"
    app_env: str = "development"
    app_version: str = "1.0.0"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "resume_intelligence"
    mongodb_server_selection_timeout_ms: int = Field(default=5000, ge=100, le=60000)
    mongodb_connect_timeout_ms: int = Field(default=5000, ge=100, le=60000)

    llm_provider: str = "none"
    llm_api_key: str | None = None
    llm_model: str | None = None

    max_resume_size_mb: int = Field(default=10, ge=1, le=100)
    upload_directory: str = "uploads"
    allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
