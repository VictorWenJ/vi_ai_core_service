"""Service-level chat result wrappers."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rag.models import Citation, RetrievalTrace
from app.schemas.llm_response import LLMResponse


@dataclass
class ChatServiceResult:
    llm_response: LLMResponse
    citations: list[Citation] = field(default_factory=list)
    retrieval_trace: RetrievalTrace | None = None
