from io import BytesIO

import fitz
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class FakeDatabase:
    def __init__(self) -> None:
        self.database = FakeStore()

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass


class FakeResult:
    def __init__(self, modified_count=0, deleted_count=0) -> None:
        self.modified_count = modified_count
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self) -> None:
        self.documents = {}

    async def insert_one(self, document) -> None:
        self.documents[document["_id"]] = document

    async def replace_one(self, query, document, upsert=False) -> None:
        self.documents[query["_id"]] = document

    async def find_one(self, query):
        if "_id" in query:
            return self.documents.get(query["_id"])
        return next(
            (document for document in self.documents.values()
             if document.get("metadata", {}).get("file_hash") == query.get("metadata.file_hash")),
            None,
        )

    async def update_one(self, query, update):
        document = self.documents.get(query["_id"])
        if document is None:
            return FakeResult()
        document.update(update["$set"])
        return FakeResult(modified_count=1)

    async def delete_one(self, query):
        return FakeResult(deleted_count=1 if self.documents.pop(query["_id"], None) else 0)


class FakeStore:
    def __init__(self) -> None:
        self.resumes = FakeCollection()


def pdf_bytes() -> bytes:
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Resume")
    content = document.tobytes()
    document.close()
    return content


def test_upload_endpoint_returns_contract(monkeypatch, tmp_path) -> None:
    settings = Settings(upload_directory=str(tmp_path))
    application = create_app(settings=settings, database=FakeDatabase())

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("candidate.pdf", BytesIO(pdf_bytes()), "application/pdf")},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert set(body["data"]) == {
        "email", "linkedin", "phoneNum", "languages", "frameworks/libraries",
        "tools", "databases", "domain", "projects",
    }
    assert response.headers["X-Resume-ID"]
    assert len(list(tmp_path.iterdir())) == 1


def test_upload_endpoint_returns_standard_error(monkeypatch, tmp_path) -> None:
    settings = Settings(upload_directory=str(tmp_path))
    application = create_app(settings=settings, database=FakeDatabase())

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("candidate.txt", b"not supported", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {
            "code": "INVALID_FILE_TYPE",
            "message": "Only PDF and DOCX resumes are supported.",
        },
    }


def test_resume_resource_endpoints(monkeypatch, tmp_path) -> None:
    settings = Settings(upload_directory=str(tmp_path))
    application = create_app(settings=settings, database=FakeDatabase())

    with TestClient(application) as client:
        upload_response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("candidate.pdf", BytesIO(pdf_bytes()), "application/pdf")},
        )
        resume_id = upload_response.headers["X-Resume-ID"]

        assert client.get(f"/api/v1/resumes/{resume_id}").status_code == 200
        assert client.get(f"/api/v1/resumes/{resume_id}/skills").status_code == 200
        assert client.get(f"/api/v1/resumes/{resume_id}/projects").status_code == 200
        assert client.post(f"/api/v1/resumes/{resume_id}/reprocess").status_code == 200
        assert client.delete(f"/api/v1/resumes/{resume_id}").status_code == 204
        assert client.get(f"/api/v1/resumes/{resume_id}").status_code == 404
