"""Service-level chat result wrappers."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rag.models import Citation, RetrievalTrace
from app.schemas.llm_response import LLMResponse


@dataclass
class ChatServiceResult:
    # 标准化 LLM 响应对象。
    llm_response: LLMResponse
    # 基于检索结果生成的引用列表；无命中时为空数组。
    citations: list[Citation] = field(default_factory=list)
    # 检索链路追踪信息；检索禁用或失败时可为空。
    retrieval_trace: RetrievalTrace | None = None
