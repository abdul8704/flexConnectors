"""Persistence operations for resume documents."""

from datetime import UTC, datetime
from typing import Any

from app.models.resume import ResumeDocument


class ResumeRepository:
    def __init__(self, database: Any) -> None:
        self._collection = database.resumes

    async def create(self, resume: ResumeDocument) -> ResumeDocument:
        await self._collection.insert_one(resume.model_dump(by_alias=True, mode="python"))
        return resume

    async def replace(self, resume: ResumeDocument) -> ResumeDocument:
        await self._collection.replace_one(
            {"_id": resume.id},
            resume.model_dump(by_alias=True, mode="python"),
            upsert=True,
        )
        return resume

    async def find_by_id(self, resume_id: str) -> ResumeDocument | None:
        document = await self._collection.find_one({"_id": resume_id})
        return ResumeDocument.model_validate(document) if document else None

    async def update(self, resume_id: str, changes: dict[str, Any]) -> bool:
        if "frameworks_libraries" in changes:
            changes["frameworks/libraries"] = changes.pop("frameworks_libraries")
        changes["updated_at"] = datetime.now(UTC)
        result = await self._collection.update_one({"_id": resume_id}, {"$set": changes})
        return result.modified_count > 0

    async def delete(self, resume_id: str) -> bool:
        result = await self._collection.delete_one({"_id": resume_id})
        return result.deleted_count > 0

    async def find_by_file_hash(self, file_hash: str) -> ResumeDocument | None:
        document = await self._collection.find_one({"metadata.file_hash": file_hash})
        return ResumeDocument.model_validate(document) if document else None
