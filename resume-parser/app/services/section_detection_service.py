"""Detect common and descriptive resume section headings."""

import re


SECTION_ALIASES = {
    "summary": ("summary", "profile", "objective", "about me", "professional summary"),
    "skills": ("skills", "technical skills", "technologies", "tech stack", "competencies"),
    "experience": ("experience", "work experience", "employment", "professional experience"),
    "education": ("education", "academic background", "qualifications"),
    "projects": ("projects", "project experience", "selected work", "my work", "academic projects", "personal projects"),
    "certifications": ("certifications", "certificates", "licenses"),
    "achievements": ("achievements", "awards", "accomplishments"),
}


class SectionDetectionService:
    def detect(self, text: str) -> dict[str, str]:
        lines = text.splitlines()
        sections: dict[str, list[str]] = {name: [] for name in SECTION_ALIASES}
        current = "other"
        for raw_line in lines:
            line = raw_line.strip()
            detected = self._detect_heading(line)
            if detected:
                current = detected
                continue
            if current in sections and line:
                sections[current].append(line)
        return {name: "\n".join(content) for name, content in sections.items() if content}

    @staticmethod
    def _detect_heading(line: str) -> str | None:
        if not line or len(line) > 70 or line.endswith((".", ",", ";")):
            return None
        normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
        for section, aliases in SECTION_ALIASES.items():
            if normalized in aliases:
                return section
        if line.isupper() and len(line.split()) <= 5:
            for section, aliases in SECTION_ALIASES.items():
                if any(alias in normalized for alias in aliases):
                    return section
        return None
