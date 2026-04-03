"""Gemini provider scaffold."""

from __future__ import annotations

from app.providers.base import BaseLLMProvider, ProviderNotImplementedError
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Scaffold for future Gemini integration."""

    provider_name = "gemini"

    def chat(self, request: LLMRequest) -> LLMResponse:
        self.ensure_non_streaming(request)
        raise ProviderNotImplementedError(
            "Gemini provider is scaffolded only in Phase 1. TODO: implement vendor API mapping."
        )
