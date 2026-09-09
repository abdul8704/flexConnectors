from datetime import UTC, datetime

import pytest

from app.models.resume import ResumeDocument, ResumeMetadata
from app.repositories.resume_repository import ResumeRepository


class FakeResult:
    def __init__(self, modified_count: int = 0, deleted_count: int = 0) -> None:
        self.modified_count = modified_count
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict] = {}

    async def insert_one(self, document: dict) -> None:
        self.documents[document["_id"]] = document

    async def replace_one(self, query: dict, document: dict, upsert: bool = False) -> None:
        self.documents[query["_id"]] = document

    async def find_one(self, query: dict) -> dict | None:
        if "_id" in query:
            return self.documents.get(query["_id"])
        return next(
            (
                document
                for document in self.documents.values()
                if document.get("metadata", {}).get("file_hash") == query["metadata.file_hash"]
            ),
            None,
        )

    async def update_one(self, query: dict, update: dict) -> FakeResult:
        document = self.documents.get(query["_id"])
        if document is None:
            return FakeResult()
        document.update(update["$set"])
        return FakeResult(modified_count=1)

    async def delete_one(self, query: dict) -> FakeResult:
        deleted = self.documents.pop(query["_id"], None)
        return FakeResult(deleted_count=1 if deleted else 0)


class FakeDatabase:
    def __init__(self) -> None:
        self.resumes = FakeCollection()


@pytest.mark.asyncio
async def test_resume_repository_crud_and_hash_lookup() -> None:
    repository = ResumeRepository(FakeDatabase())
    resume = ResumeDocument(
        metadata=ResumeMetadata(original_file_type="pdf", file_hash="abc123"),
    )

    await repository.create(resume)
    assert (await repository.find_by_id(resume.id)).id == resume.id
    assert (await repository.find_by_file_hash("abc123")).id == resume.id

    assert await repository.update(resume.id, {"frameworks_libraries": ["FastAPI"]})
    updated = await repository.find_by_id(resume.id)
    assert updated.frameworks_libraries == ["FastAPI"]
    assert updated.updated_at >= datetime.now(UTC).replace(microsecond=0)

    assert await repository.delete(resume.id)
    assert await repository.find_by_id(resume.id) is None
