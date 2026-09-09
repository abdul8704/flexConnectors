"""Upload API response schemas."""

from pydantic import BaseModel, ConfigDict


class UploadData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    upload_id: str
    file_type: str
    size_bytes: int
    file_hash: str
    processing_status: str = "uploaded"


class UploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: UploadData
