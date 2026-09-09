"""Evidence-preserving project summaries."""

from app.services.project_extraction_service import ExtractedProject


class ProjectSummaryService:
    def summarize(self, project: ExtractedProject) -> str:
        return f"{project.project_name}: {project.description}".strip()
