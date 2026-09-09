from app.services.preprocessing_service import PreprocessingService
from app.services.project_extraction_service import ProjectExtractionService
from app.services.project_summary_service import ProjectSummaryService
from app.services.section_detection_service import SectionDetectionService
from app.services.skill_extraction_service import SkillExtractionService
from app.services.skill_normalization_service import SkillNormalizationService
from app.services.resume_service import ResumeService


def test_preprocessing_preserves_boundaries() -> None:
    result = PreprocessingService().preprocess(" Skills\r\n\r\nPython   React \n\n\n Projects ")
    assert result == "Skills\n\nPython React \n\nProjects"


def test_section_detection_handles_aliases() -> None:
    sections = SectionDetectionService().detect("MY WORK\nShop App\nBuilt with React\n\nTECHNICAL SKILLS\nPython")
    assert sections["projects"] == "Shop App\nBuilt with React"
    assert sections["skills"] == "Python"


def test_skills_are_explicit_and_normalized() -> None:
    text = "Built using ReactJS and Node.js. Mongo DB was used."
    extracted = SkillExtractionService().extract(text, {})
    normalized = SkillNormalizationService().normalize(extracted)
    assert "React" in normalized["frontend"]
    assert "Node.js" in normalized["backend"]
    assert "MongoDB" in normalized["databases"]
    assert "Redux" not in normalized.get("other", [])


def test_projects_and_summaries_do_not_invent_results() -> None:
    projects = ProjectExtractionService().extract("Shop App\nBuilt an online shop using React.\n- Product search")
    assert len(projects) == 1
    assert projects[0].technologies == {"frontend": ["React"]}
    assert projects[0].results is None
    assert ProjectSummaryService().summarize(projects[0]) == "Shop App: Built an online shop using React. Product search"


def test_public_contact_and_skill_mapping_uses_exact_names() -> None:
    candidate = ResumeService._extract_candidate(
        "dev@example.com https://www.linkedin.com/in/dev-user +1 (555) 123-4567"
    )
    skills = ResumeService._public_skills({
        "programming_languages": ["Python"],
        "frontend": ["React"],
        "tools": ["Git"],
        "databases": ["MongoDB"],
    })
    assert candidate == {
        "email": "dev@example.com",
        "linkedin": "https://www.linkedin.com/in/dev-user",
        "phoneNum": "+1 (555) 123-4567",
    }
    assert skills == {
        "languages": ["Python"],
        "frameworks_libraries": ["React"],
        "tools": ["Git"],
        "databases": ["MongoDB"],
    }


def test_domains_are_only_returned_when_explicitly_supported() -> None:
    assert ResumeService._extract_domains("Built a web application using React") == ["Web Development"]
    assert ResumeService._extract_domains("Built an application") == []
