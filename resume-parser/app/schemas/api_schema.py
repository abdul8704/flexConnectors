"""Generic response schemas used by resource endpoints."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: T
