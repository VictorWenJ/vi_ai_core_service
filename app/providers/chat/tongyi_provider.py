"""通义 Provider 脚手架。"""

from __future__ import annotations

from app.providers.chat.base import BaseLLMProvider, ProviderNotImplementedError
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse


class TongyiProvider(BaseLLMProvider):
    """面向后续通义接入的脚手架。"""

    provider_name = "tongyi"

    def chat(self, request: LLMRequest) -> LLMResponse:
        self.ensure_non_streaming(request)
        raise ProviderNotImplementedError(
            "通义 Provider 当前仅为脚手架（Phase 1）。TODO：实现厂商 API 映射。"
        )
