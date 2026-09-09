"""MongoDB client lifecycle and index management."""

from typing import Any

from pymongo import ASCENDING, AsyncMongoClient

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoDatabase:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncMongoClient[dict[str, Any]] | None = None
        self._database = None

    async def connect(self) -> None:
        if self._client is not None:
            return

        self._client = AsyncMongoClient(
            self._settings.mongodb_uri,
            serverSelectionTimeoutMS=self._settings.mongodb_server_selection_timeout_ms,
            connectTimeoutMS=self._settings.mongodb_connect_timeout_ms,
        )
        await self._client.admin.command("ping")
        self._database = self._client[self._settings.mongodb_database]
        await self._create_indexes()
        logger.info("MongoDB connection established")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")

    @property
    def database(self):
        if self._database is None:
            raise RuntimeError("MongoDB is not connected")
        return self._database

    async def _create_indexes(self) -> None:
        resumes = self.database.resumes
        await resumes.create_index([("email", ASCENDING)], name="candidate_email")
        await resumes.create_index([("languages", ASCENDING)], name="languages_lookup")
        await resumes.create_index([("frameworks_libraries", ASCENDING)], name="frameworks_libraries_lookup")
        await resumes.create_index([("databases", ASCENDING)], name="databases_lookup")
        await resumes.create_index(
            [("projects.project_name", ASCENDING)],
            name="project_name",
        )
        indexes = await resumes.index_information()
        existing_hash_index = indexes.get("file_hash")
        if existing_hash_index and not existing_hash_index.get("unique", False):
            await resumes.drop_index("file_hash")
        await resumes.create_index([("metadata.file_hash", ASCENDING)], name="file_hash", unique=True)
