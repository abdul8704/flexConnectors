# Resume Intelligence Backend

Frontend-independent FastAPI service for secure resume upload, deterministic extraction, structured skills, project analysis, and MongoDB persistence.

## Architecture

```text
HTTP route -> controller/service -> repository -> MongoDB
                         |
                         +-> file validation -> text extraction -> preprocessing
                             -> sections -> skills/projects -> Pydantic validation
```

The default implementation is deterministic and does not require an LLM key. The `LLMService` interface in `app/services/llm_service.py` is the integration point for a future OpenAI, Gemini, or other provider.

## Technology

- Python 3.11+
- FastAPI and Pydantic 2
- PyMuPDF for PDF extraction
- python-docx for DOCX extraction
- Async PyMongo for MongoDB
- Pytest and pytest-asyncio

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Documentation is available at `/docs` and `/redoc`. The liveness endpoint is `/api/v1/health`.

## Run With Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000` and MongoDB at `localhost:27017`.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | API display name |
| `APP_ENV` | Runtime environment |
| `APP_VERSION` | API version metadata |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DATABASE` | Database name |
| `MAX_RESUME_SIZE_MB` | Upload size limit |
| `UPLOAD_DIRECTORY` | Secure internal upload directory |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins |
| `LLM_PROVIDER` | Future provider selection |
| `LLM_API_KEY` | Future provider secret |
| `LLM_MODEL` | Future model name |

Never commit `.env` or API keys.

## API Contract

### Upload and process

```http
POST /api/v1/resumes/upload
Content-Type: multipart/form-data
```

Form field: `file` (`.pdf` or `.docx`). The response body contains exactly the candidate fields and projects defined below. The generated resume identifier is returned in the `X-Resume-ID` response header for subsequent resource requests.

The public success body is:

```json
{
  "success": true,
  "data": {
    "email": null,
    "linkedin": null,
    "phoneNum": null,
    "languages": [],
    "frameworks/libraries": [],
    "tools": [],
    "databases": [],
    "domain": [],
    "projects": []
  }
}
```

### Resource endpoints

- `GET /api/v1/resumes/{resume_id}`
- `GET /api/v1/resumes/{resume_id}/skills`
- `GET /api/v1/resumes/{resume_id}/projects`
- `POST /api/v1/resumes/{resume_id}/reprocess`
- `DELETE /api/v1/resumes/{resume_id}`

Errors always use:

```json
{
  "success": false,
  "error": {
    "code": "RESUME_NOT_FOUND",
    "message": "Resume not found."
  }
}
```

### Processing statuses

Documents support `uploaded`, `processing`, `completed`, and `failed`. The first version processes synchronously; the service boundary can be moved to a background worker later without changing the API contract.

## Security

Uploads are streamed, size-limited, validated by content and parseability, stored with UUID names, hashed with SHA-256, and deleted on failed validation. Original filenames are never used as paths. CORS is configured through `ALLOWED_ORIGINS`. `app/core/security.py` provides the authentication dependency boundary for integration with the parent application.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use generated PDF/DOCX fixtures and repository doubles; they do not make LLM calls. A running MongoDB instance is required only for live infrastructure validation.

## Database

The `resumes` collection stores the flat candidate fields, projects, parser metadata, file hash, and processing status. Indexes are created for email, languages, frameworks/libraries, databases, project names, and unique `metadata.file_hash`.

## Frontend Integration Guide

The frontend only needs the REST contract. Upload a `File` under the `file` field, read the `X-Resume-ID` response header, and use the resource endpoints for subsequent views. The skills endpoint returns the same exact candidate field names, while the projects endpoint returns `{ "projects": [] }` inside `data`. Do not depend on PDF parsing, MongoDB, filesystem paths, or extraction internals. Configure the frontend origin in `ALLOWED_ORIGINS`; authentication can be supplied by replacing the security dependency in the parent application.

## Future Extensions

The structured output is ready for job matching, resume scoring, skill-gap analysis, semantic search, RAG, and interview question generation. OCR and asynchronous processing are deliberately left as replaceable extensions.
