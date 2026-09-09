"""Resume resource endpoints."""

from fastapi import APIRouter, File, Request, Response, UploadFile, status

from app.controllers.resume_controller import ResumeController
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume_schema import Project, ResumeResponse, SkillsResponse, ProjectsResponse

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _repository(request: Request) -> ResumeRepository:
    return ResumeRepository(request.app.state.database.database)


def _controller(request: Request) -> ResumeController:
    return ResumeController(_repository(request), request.app.state.settings)


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED, summary="Upload and process a resume")
async def upload_resume(request: Request, response: Response, file: UploadFile = File(...)) -> ResumeResponse:
    result, resume_id = await _controller(request).upload(file)
    response.headers["X-Resume-ID"] = resume_id
    return result


@router.get("/{resume_id}", response_model=ResumeResponse, summary="Get a resume")
async def get_resume(resume_id: str, request: Request) -> ResumeResponse:
    return await _controller(request).get(resume_id)


@router.get("/{resume_id}/skills", response_model=SkillsResponse, summary="Get resume skills")
async def get_skills(resume_id: str, request: Request) -> SkillsResponse:
    return await _controller(request).skills(resume_id)


@router.get("/{resume_id}/projects", response_model=ProjectsResponse, summary="Get resume projects")
async def get_projects(resume_id: str, request: Request) -> ProjectsResponse:
    return await _controller(request).projects(resume_id)


@router.post("/{resume_id}/reprocess", response_model=ResumeResponse, summary="Reprocess a resume")
async def reprocess_resume(resume_id: str, request: Request) -> ResumeResponse:
    return await _controller(request).reprocess(resume_id)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a resume")
async def delete_resume(resume_id: str, request: Request) -> None:
    await _controller(request).delete(resume_id)
