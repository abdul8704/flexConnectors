"""Health check endpoint."""

from fastapi import APIRouter

from app.schemas.response_schema import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health",
    description="Returns a lightweight liveness response without contacting external services.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(success=True, status="healthy")
