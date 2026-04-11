"""Gemini Provider 脚手架。"""

from __future__ import annotations

from app.providers.chat.base import BaseLLMProvider, ProviderNotImplementedError
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse


class GeminiProvider(BaseLLMProvider):
    """面向后续 Gemini 接入的脚手架。"""

    provider_name = "gemini"

    def chat(self, request: LLMRequest) -> LLMResponse:
        self.ensure_non_streaming(request)
        raise ProviderNotImplementedError(
            "Gemini Provider 当前仅为脚手架（Phase 1）。TODO：实现厂商 API 映射。"
        )
