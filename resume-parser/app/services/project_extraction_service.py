"""Conservative project extraction from project sections."""

import re
from dataclasses import dataclass

from app.services.skill_extraction_service import SKILL_ALIASES, SKILL_CATALOG


@dataclass(frozen=True)
class ExtractedProject:
    project_name: str
    description: str
    technologies: dict[str, list[str]]
    features: list[str]
    responsibilities: list[str]
    role: str | None = None
    duration: str | None = None
    results: str | None = None


class ProjectExtractionService:
    def extract(self, project_text: str) -> list[ExtractedProject]:
        if not project_text.strip():
            return []
        blocks = [block.strip() for block in re.split(r"\n\s*\n", project_text) if block.strip()]
        projects: list[ExtractedProject] = []
        for index, block in enumerate(blocks):
            lines = block.splitlines()
            name = lines[0].strip("-: ") if lines else f"Project {index + 1}"
            description = " ".join(line.strip("-•* ") for line in lines[1:] if line.strip()) or name
            technologies = self._technologies(block)
            features = [line.strip("-•* ") for line in lines[1:] if line.lstrip().startswith(("-", "•", "*"))]
            projects.append(ExtractedProject(name, description, technologies, features, []))
        return projects

    @staticmethod
    def _technologies(text: str) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        for category, skills in SKILL_CATALOG.items():
            values = [
                SKILL_ALIASES.get(skill, (skill,))[0]
                for skill in skills
                if any(re.search(rf"(?<![\w+#]){re.escape(variant)}(?![\w+#])", text, re.IGNORECASE) for variant in SKILL_ALIASES.get(skill, (skill,)))
            ]
            if values:
                found[category] = values
        return found
