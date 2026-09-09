"""Consistent error response schemas."""

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = False
    error: ErrorDetail
