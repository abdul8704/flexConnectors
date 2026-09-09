"""Validate structured extraction output before persistence."""

from typing import Any

from pydantic import ValidationError

from app.core.exceptions import AppException
from app.schemas.resume_schema import Resume


class JsonValidationService:
    def validate_resume(self, value: dict[str, Any]) -> Resume:
        try:
            return Resume.model_validate(value)
        except ValidationError as error:
            raise AppException("JSON_VALIDATION_FAILED", "Resume data failed schema validation.") from error
