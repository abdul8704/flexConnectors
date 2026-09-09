"""Provider-neutral LLM boundary with a deterministic default."""

from abc import ABC, abstractmethod
from typing import Any


class LLMService(ABC):
    @abstractmethod
    async def extract_resume_information(self, text: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def summarize_project(self, project: dict[str, Any]) -> str:
        raise NotImplementedError


class NullLLMService(LLMService):
    async def extract_resume_information(self, text: str) -> dict[str, Any]:
        return {}

    async def summarize_project(self, project: dict[str, Any]) -> str:
        return str(project.get("description", ""))
