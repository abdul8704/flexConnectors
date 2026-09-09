"""Evidence-based deterministic skill extraction."""

import re
from dataclasses import dataclass


SKILL_CATALOG = {
    "programming_languages": ("Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Ruby", "PHP", "Kotlin", "Swift"),
    "frontend": ("React", "Angular", "Vue", "HTML", "CSS", "Tailwind CSS"),
    "backend": ("Node.js", "Express", "FastAPI", "Django", "Flask", ".NET", "Spring Boot"),
    "databases": ("MongoDB", "PostgreSQL", "MySQL", "SQLite", "Redis", "DynamoDB"),
    "frameworks": ("Next.js", "Spring", "Laravel", "TensorFlow", "PyTorch"),
    "libraries": ("pandas", "NumPy", "scikit-learn", "OpenCV", "spaCy", "sentence-transformers"),
    "cloud": ("AWS", "Azure", "Google Cloud", "GCP", "Firebase"),
    "devops": ("Docker", "Kubernetes", "GitHub Actions", "Jenkins", "Terraform"),
    "machine_learning": ("Machine Learning", "Deep Learning", "NLP", "Natural Language Processing", "Computer Vision"),
    "data_science": ("Data Science", "Data Analysis", "Power BI", "Tableau"),
    "tools": ("Git", "GitHub", "Postman", "Jira", "Linux"),
}

SKILL_ALIASES = {
    "React": ("React", "ReactJS", "React.js"),
    "Node.js": ("Node.js", "NodeJS", "Node"),
    "MongoDB": ("MongoDB", "Mongo DB"),
    "JavaScript": ("JavaScript", "JS"),
}


@dataclass(frozen=True)
class SkillEvidence:
    name: str
    category: str
    evidence: list[str]
    confidence: float = 0.96


class SkillExtractionService:
    def extract(self, text: str, sections: dict[str, str]) -> list[SkillEvidence]:
        results: dict[str, SkillEvidence] = {}
        for category, skills in SKILL_CATALOG.items():
            for skill in skills:
                variants = SKILL_ALIASES.get(skill, (skill,))
                matches = [line.strip() for line in text.splitlines() if any(self._matches(variant, line) for variant in variants)]
                if matches:
                    canonical = self._normalize(skill)
                    results[canonical] = SkillEvidence(canonical, category, matches[:5])
        return list(results.values())

    @staticmethod
    def _matches(skill: str, line: str) -> bool:
        return re.search(rf"(?<![\w+#]){re.escape(skill)}(?![\w+#])", line, re.IGNORECASE) is not None

    @staticmethod
    def _normalize(skill: str) -> str:
        aliases = {"JavaScript": "JavaScript", "TypeScript": "TypeScript", "React": "React", "Node.js": "Node.js", "Natural Language Processing": "NLP"}
        return aliases.get(skill, skill)
