"""Persistence model for a processed resume document."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ResumeMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    original_file_type: str
    parser_version: str = "1.0.0"
    processing_status: Literal["uploaded", "processing", "completed", "failed"] = "uploaded"
    file_hash: str | None = None
    error_code: str | None = None
    stored_path: str | None = None


class ResumeDocument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    email: str | None = None
    linkedin: str | None = None
    phoneNum: str | None = None
    languages: list[str] = Field(default_factory=list)
    frameworks_libraries: list[str] = Field(default_factory=list, alias="frameworks/libraries")
    tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ResumeMetadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
