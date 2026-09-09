"""Canonicalize and deduplicate extracted skills."""

from app.services.skill_extraction_service import SkillEvidence


NORMALIZATION_MAP = {
    "js": "JavaScript", "node": "Node.js", "nodejs": "Node.js", "reactjs": "React", "react.js": "React",
    "mongo db": "MongoDB", "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
}


class SkillNormalizationService:
    def normalize(self, skills: list[SkillEvidence]) -> dict[str, list[str]]:
        categorized: dict[str, list[str]] = {}
        seen: set[str] = set()
        for skill in skills:
            canonical = NORMALIZATION_MAP.get(skill.name.lower(), skill.name)
            key = canonical.lower()
            if key in seen:
                continue
            seen.add(key)
            categorized.setdefault(skill.category, []).append(canonical)
        return categorized
