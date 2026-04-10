"""Text cleaner for ingestion pipeline."""

from __future__ import annotations

import re


class DocumentCleaner:
    """Apply minimal deterministic cleaning for ingestion text."""

    _MULTI_BLANK_LINES = re.compile(r"\n{3,}")
    _TRAILING_WHITESPACE = re.compile(r"[ \t]+$", re.MULTILINE)

    def clean(self, content: str) -> str:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        normalized = self._TRAILING_WHITESPACE.sub("", normalized)
        normalized = self._MULTI_BLANK_LINES.sub("\n\n", normalized)
        return normalized.strip()
