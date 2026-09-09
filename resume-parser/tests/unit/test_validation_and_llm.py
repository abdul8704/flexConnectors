import pytest

from app.core.exceptions import AppException
from app.services.json_validation_service import JsonValidationService
from app.services.llm_service import NullLLMService


@pytest.mark.asyncio
async def test_null_llm_provider_is_safe_default() -> None:
    service = NullLLMService()
    assert await service.extract_resume_information("React only") == {}
    assert await service.summarize_project({"description": "Built a tool."}) == "Built a tool."


def test_resume_json_validation_rejects_unknown_public_fields() -> None:
    with pytest.raises(AppException) as error:
        JsonValidationService().validate_resume({"phone": "123", "projects": []})

    assert error.value.code == "JSON_VALIDATION_FAILED"


def test_resume_json_validation_accepts_exact_public_shape() -> None:
    result = JsonValidationService().validate_resume({
        "email": None,
        "linkedin": None,
        "phoneNum": None,
        "languages": [],
        "frameworks/libraries": [],
        "tools": [],
        "databases": [],
        "domain": [],
        "projects": [],
    })

    assert result.frameworks_libraries == []
