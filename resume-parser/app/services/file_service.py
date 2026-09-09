"""Secure resume upload validation and storage."""

import hashlib
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import fitz
from docx import Document
from fastapi import UploadFile, status

from app.core.config import Settings
from app.core.exceptions import AppException

SUPPORTED_TYPES = {".pdf": "pdf", ".docx": "docx"}
CHUNK_SIZE = 1024 * 1024


class StoredUpload:
    def __init__(self, upload_id: str, file_type: str, size_bytes: int, file_hash: str, path: Path) -> None:
        self.upload_id = upload_id
        self.file_type = file_type
        self.size_bytes = size_bytes
        self.file_hash = file_hash
        self.path = path


class FileService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._max_size = settings.max_resume_size_mb * 1024 * 1024

    async def store_resume(self, upload: UploadFile) -> StoredUpload:
        extension = Path(upload.filename or "").suffix.lower()
        file_type = SUPPORTED_TYPES.get(extension)
        if file_type is None:
            raise AppException(
                "INVALID_FILE_TYPE",
                "Only PDF and DOCX resumes are supported.",
                status.HTTP_400_BAD_REQUEST,
            )

        upload_directory = Path(self._settings.upload_directory)
        upload_id = str(uuid4())
        destination = upload_directory / f"{upload_id}{extension}"
        size_bytes = 0
        digest = hashlib.sha256()

        try:
            upload_directory.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stored_file:
                while chunk := await upload.read(CHUNK_SIZE):
                    size_bytes += len(chunk)
                    if size_bytes > self._max_size:
                        raise AppException(
                            "FILE_TOO_LARGE",
                            f"Resume files must not exceed {self._settings.max_resume_size_mb} MB.",
                            status.HTTP_413_CONTENT_TOO_LARGE,
                        )
                    stored_file.write(chunk)
                    digest.update(chunk)

            if size_bytes == 0:
                raise AppException("EMPTY_FILE", "The uploaded resume is empty.")

            self._validate_content(destination, file_type)
            return StoredUpload(upload_id, file_type, size_bytes, digest.hexdigest(), destination)
        except AppException:
            destination.unlink(missing_ok=True)
            raise
        except Exception as error:
            destination.unlink(missing_ok=True)
            raise AppException(
                "INVALID_FILE_CONTENT",
                "The uploaded resume is corrupted or has an invalid file format.",
                status.HTTP_400_BAD_REQUEST,
            ) from error
        finally:
            await upload.close()

    @staticmethod
    def _validate_content(path: Path, file_type: str) -> None:
        with path.open("rb") as file_handle:
            header = file_handle.read(8)

        if file_type == "pdf":
            if not header.startswith(b"%PDF-"):
                raise AppException("INVALID_MIME_TYPE", "The file content is not a valid PDF.")
            with path.open("rb") as file_handle:
                content = file_handle.read()
            with fitz.open(stream=content, filetype="pdf") as document:
                document.page_count
            return

        if not header.startswith(b"PK") or not FileService._is_docx_archive(path):
            raise AppException("INVALID_MIME_TYPE", "The file content is not a valid DOCX document.")
        Document(path)

    @staticmethod
    def _is_docx_archive(path: Path) -> bool:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            return "[Content_Types].xml" in names and "word/document.xml" in names
