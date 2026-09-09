"""End-to-end deterministic resume processing orchestration."""

import re
from pathlib import Path
from uuid import uuid4

from app.models.resume import ResumeDocument, ResumeMetadata
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume_schema import Resume
from app.services.json_validation_service import JsonValidationService
from app.services.preprocessing_service import PreprocessingService
from app.services.project_extraction_service import ProjectExtractionService
from app.services.project_summary_service import ProjectSummaryService
from app.services.section_detection_service import SectionDetectionService
from app.services.skill_extraction_service import SkillExtractionService
from app.services.skill_normalization_service import SkillNormalizationService
from app.services.text_extraction_service import TextExtractionService


class ResumeService:
    def __init__(self, repository: ResumeRepository) -> None:
        self._repository = repository
        self._text_extraction = TextExtractionService()
        self._preprocessing = PreprocessingService()
        self._sections = SectionDetectionService()
        self._skill_extraction = SkillExtractionService()
        self._skill_normalization = SkillNormalizationService()
        self._project_extraction = ProjectExtractionService()
        self._project_summary = ProjectSummaryService()
        self._validation = JsonValidationService()

    async def process_file(
        self,
        file_path: str | Path,
        file_type: str,
        file_hash: str,
        resume_id: str | None = None,
    ) -> ResumeDocument:
        extraction = self._text_extraction.extract_text(file_path, file_type)
        text = self._preprocessing.preprocess(extraction.text)
        sections = self._sections.detect(text)
        candidate = self._extract_candidate(text)
        extracted_skills = self._skill_extraction.extract(text, sections)
        categorized_skills = self._skill_normalization.normalize(extracted_skills)
        skills = self._public_skills(categorized_skills)
        projects = []
        for project in self._project_extraction.extract(sections.get("projects", "")):
            technologies = self._technology_list(project.technologies)
            projects.append({
                "project_name": project.project_name,
                "summary": self._project_summary.summarize(project),
                "problem": None,
                "solution": project.description,
                "technologies": technologies,
                "features": project.features,
                "responsibilities": project.responsibilities,
                "role": project.role,
                "duration": project.duration,
                "results": project.results,
            })

        document_id = resume_id or str(uuid4())
        validated = self._validation.validate_resume({
            **candidate,
            **skills,
            "domain": self._extract_domains(text),
            "projects": projects,
        })
        document = ResumeDocument(
            _id=document_id,
            email=validated.email,
            linkedin=validated.linkedin,
            phoneNum=validated.phoneNum,
            languages=validated.languages,
            frameworks_libraries=validated.frameworks_libraries,
            tools=validated.tools,
            databases=validated.databases,
            domain=validated.domain,
            projects=[project.model_dump() for project in validated.projects],
            metadata=ResumeMetadata(
                original_file_type=file_type,
                processing_status="completed",
                file_hash=file_hash,
                stored_path=str(file_path),
            ),
        )
        if resume_id:
            return await self._repository.replace(document)
        return await self._repository.create(document)

    async def reprocess(self, resume: ResumeDocument) -> ResumeDocument:
        return await self.process_file(
            resume.metadata.stored_path,
            resume.metadata.original_file_type,
            resume.metadata.file_hash or "",
            resume.id,
        )

    @staticmethod
    def _extract_candidate(text: str) -> dict[str, str | None]:
        email = next(iter(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)), None)
        linkedin = next(iter(re.findall(r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9._%+-]+", text, re.IGNORECASE)), None)
        phone = next(iter(re.findall(r"(?:\+?\d[\d ()-]{7,}\d)", text)), None)
        return {"email": email, "linkedin": linkedin, "phoneNum": phone}

    @staticmethod
    def _public_skills(values: dict[str, list[str]]) -> dict[str, list[str]]:
        mapping = {
            "programming_languages": "languages", "databases": "databases", "machine_learning": "frameworks_libraries",
            "data_science": "frameworks_libraries", "cloud": "frameworks_libraries", "devops": "tools", "frontend": "frameworks_libraries",
            "backend": "frameworks_libraries", "frameworks": "frameworks_libraries", "libraries": "frameworks_libraries",
            "tools": "tools",
        }
        public: dict[str, list[str]] = {"languages": [], "frameworks_libraries": [], "tools": [], "databases": []}
        for category, names in values.items():
            target = mapping.get(category)
            if target:
                public[target].extend(names)
        return {key: list(dict.fromkeys(value)) for key, value in public.items()}

    @staticmethod
    def _technology_list(values: dict[str, list[str]]) -> list[str]:
        return list(dict.fromkeys(name for names in values.values() for name in names))

    @staticmethod
    def _extract_domains(text: str) -> list[str]:
        domains = {
            "Web Development": r"\bweb development\b|\bweb application\b|\bwebsite\b",
            "Machine Learning": r"\bmachine learning\b|\bdeep learning\b",
            "Natural Language Processing": r"\bnatural language processing\b|\bNLP\b",
            "Data Science": r"\bdata science\b|\bdata analysis\b",
            "Cloud Computing": r"\bcloud computing\b",
            "Cybersecurity": r"\bcybersecurity\b|\bcyber security\b",
            "Mobile Development": r"\bmobile development\b|\bmobile application\b",
        }
        return [name for name, pattern in domains.items() if re.search(pattern, text, re.IGNORECASE)]
