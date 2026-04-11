"""豆包 Provider 脚手架。"""

from __future__ import annotations

from app.providers.chat.base import BaseLLMProvider, ProviderNotImplementedError
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse


class DoubaoProvider(BaseLLMProvider):
    """面向后续豆包接入的脚手架。"""

    provider_name = "doubao"

    def chat(self, request: LLMRequest) -> LLMResponse:
        self.ensure_non_streaming(request)
        raise ProviderNotImplementedError(
            "豆包 Provider 当前仅为脚手架（Phase 1）。TODO：实现厂商 API 映射。"
        )
