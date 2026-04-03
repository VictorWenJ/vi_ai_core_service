"""Normalized response models for LLM access."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class LLMUsage:
    """Normalized token usage."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class LLMResponse:
    """Normalized provider response returned to business code."""

    content: str
    provider: str
    model: str | None = None
    usage: LLMUsage | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
