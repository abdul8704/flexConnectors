"""Normalize extracted text without removing meaningful resume structure."""

import re
import unicodedata


class PreprocessingService:
    def preprocess(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n[ \t]+", "\n", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()
