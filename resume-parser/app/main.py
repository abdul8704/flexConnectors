"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.api.routes.health import router as health_router
from app.api.routes.resume import router as resume_router
from app.core.config import get_settings
from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.database.mongodb import MongoDatabase

logger = get_logger(__name__)


def create_app(
    settings: Settings | None = None,
    database: MongoDatabase | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    database = database or MongoDatabase(settings)

    @asynccontextmanager
    async def app_lifespan(application: FastAPI):
        configure_logging()
        await database.connect()
        application.state.settings = settings
        application.state.database = database
        logger.info("Application startup")
        try:
            yield
        finally:
            await database.close()
            logger.info("Application shutdown")

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Frontend-independent resume parsing and intelligence API.",
        lifespan=app_lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    application.include_router(health_router, prefix="/api/v1")
    application.include_router(resume_router, prefix="/api/v1")

    @application.exception_handler(AppException)
    async def app_exception_handler(_: Request, error: AppException):
        return _error_response(error.status_code, error.code, error.message)

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, error: RequestValidationError):
        return _error_response(422, "VALIDATION_ERROR", "Request validation failed.")

    @application.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, error: HTTPException):
        return _error_response(error.status_code, "HTTP_ERROR", str(error.detail))

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, error: Exception):
        logger.exception("Unhandled application error", exc_info=error)
        return _error_response(500, "INTERNAL_SERVER_ERROR", "An internal server error occurred.")

    return application


def _error_response(status_code: int, code: str, message: str):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": {"code": code, "message": message}},
    )


app = create_app()
