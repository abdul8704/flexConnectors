from io import BytesIO

import fitz
import pytest
from docx import Document
from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import AppException
from app.services.file_service import FileService


def pdf_bytes() -> bytes:
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Resume")
    content = document.tobytes()
    document.close()
    return content


def docx_bytes() -> bytes:
    document = Document()
    document.add_paragraph("Resume")
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def upload(content: bytes, filename: str) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content))


@pytest.mark.asyncio
async def test_stores_valid_pdf_with_uuid_name_and_hash(tmp_path) -> None:
    service = FileService(Settings(upload_directory=str(tmp_path)))

    stored = await service.store_resume(upload(pdf_bytes(), "candidate.pdf"))

    assert stored.file_type == "pdf"
    assert stored.path.parent == tmp_path
    assert stored.path.name == f"{stored.upload_id}.pdf"
    assert stored.path.exists()
    assert len(stored.file_hash) == 64


@pytest.mark.asyncio
async def test_stores_valid_docx(tmp_path) -> None:
    stored = await FileService(Settings(upload_directory=str(tmp_path))).store_resume(
        upload(docx_bytes(), "candidate.docx")
    )

    assert stored.file_type == "docx"
    assert stored.path.suffix == ".docx"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "filename", "code"),
    [
        (b"content", "candidate.txt", "INVALID_FILE_TYPE"),
        (b"not a pdf", "candidate.pdf", "INVALID_MIME_TYPE"),
        (b"", "candidate.pdf", "EMPTY_FILE"),
    ],
)
async def test_rejects_invalid_uploads(tmp_path, content, filename, code) -> None:
    service = FileService(Settings(upload_directory=str(tmp_path)))

    with pytest.raises(AppException) as error:
        await service.store_resume(upload(content, filename))

    assert error.value.code == code
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_rejects_oversized_upload_and_cleans_file(tmp_path) -> None:
    settings = Settings(upload_directory=str(tmp_path), max_resume_size_mb=1)
    service = FileService(settings)

    with pytest.raises(AppException) as error:
        await service.store_resume(upload(b"x" * (1024 * 1024 + 1), "candidate.pdf"))

    assert error.value.code == "FILE_TOO_LARGE"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_rejects_structurally_corrupt_pdf(tmp_path) -> None:
    service = FileService(Settings(upload_directory=str(tmp_path)))

    with pytest.raises(AppException) as error:
        await service.store_resume(upload(b"%PDF-not-valid", "candidate.pdf"))

    assert error.value.code == "INVALID_FILE_CONTENT"
    assert list(tmp_path.iterdir()) == []
