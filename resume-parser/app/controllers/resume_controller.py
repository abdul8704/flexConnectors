"""Application controller for resume resource operations."""

from pathlib import Path

from fastapi import UploadFile, status

from app.core.config import Settings
from app.core.exceptions import AppException
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume_schema import (
    CandidateInformation,
    Project,
    ProjectsData,
    ProjectsResponse,
    Resume,
    ResumeResponse,
    SkillsResponse,
)
from app.services.file_service import FileService
from app.services.resume_service import ResumeService


class ResumeController:
    def __init__(self, repository: ResumeRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def upload(self, file: UploadFile) -> tuple[ResumeResponse, str]:
        stored_upload = await FileService(self._settings).store_resume(file)
        existing = await self._repository.find_by_file_hash(stored_upload.file_hash)
        if existing:
            stored_upload.path.unlink(missing_ok=True)
            return ResumeResponse(data=self._public_resume(existing)), existing.id
        try:
            document = await ResumeService(self._repository).process_file(
                stored_upload.path, stored_upload.file_type, stored_upload.file_hash
            )
        except Exception:
            stored_upload.path.unlink(missing_ok=True)
            raise
        return ResumeResponse(data=self._public_resume(document)), document.id

    async def get(self, resume_id: str) -> ResumeResponse:
        document = await self._find(resume_id)
        return ResumeResponse(data=self._public_resume(document))

    async def skills(self, resume_id: str) -> SkillsResponse:
        document = await self._find(resume_id)
        return SkillsResponse(data=self._public_skills(document))

    async def projects(self, resume_id: str) -> ProjectsResponse:
        document = await self._find(resume_id)
        return ProjectsResponse(data=ProjectsData(projects=[Project.model_validate(project) for project in document.projects]))

    async def reprocess(self, resume_id: str) -> ResumeResponse:
        document = await self._find(resume_id)
        stored_path = self._safe_stored_path(document.metadata.stored_path)
        if stored_path is None or not stored_path.exists():
            raise AppException("RESUME_FILE_NOT_FOUND", "The stored resume file is no longer available.", status.HTTP_404_NOT_FOUND)
        document.metadata.stored_path = str(stored_path)
        return ResumeResponse(data=self._public_resume(await ResumeService(self._repository).reprocess(document)))

    async def delete(self, resume_id: str) -> None:
        document = await self._find(resume_id)
        stored_path = self._safe_stored_path(document.metadata.stored_path)
        if stored_path is not None:
            stored_path.unlink(missing_ok=True)
        await self._repository.delete(resume_id)

    async def _find(self, resume_id: str):
        document = await self._repository.find_by_id(resume_id)
        if document is None:
            raise AppException("RESUME_NOT_FOUND", "Resume not found.", status.HTTP_404_NOT_FOUND)
        return document

    @staticmethod
    def _public_resume(document) -> Resume:
        return Resume(
            email=document.email,
            linkedin=document.linkedin,
            phoneNum=document.phoneNum,
            languages=document.languages,
            frameworks_libraries=document.frameworks_libraries,
            tools=document.tools,
            databases=document.databases,
            domain=document.domain,
            projects=document.projects,
        )

    @staticmethod
    def _public_skills(document) -> CandidateInformation:
        return CandidateInformation(
            email=document.email,
            linkedin=document.linkedin,
            phoneNum=document.phoneNum,
            languages=document.languages,
            frameworks_libraries=document.frameworks_libraries,
            tools=document.tools,
            databases=document.databases,
            domain=document.domain,
        )

    def _safe_stored_path(self, stored_path: str | None) -> Path | None:
        if not stored_path:
            return None
        upload_root = Path(self._settings.upload_directory).resolve()
        candidate = Path(stored_path)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(upload_root)
        except ValueError:
            return None
        return candidate
