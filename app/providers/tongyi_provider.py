"""Tongyi provider scaffold."""

from __future__ import annotations

from app.providers.base import BaseLLMProvider, ProviderNotImplementedError
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse


class TongyiProvider(BaseLLMProvider):
    """Scaffold for future Tongyi integration."""

    provider_name = "tongyi"

    def chat(self, request: LLMRequest) -> LLMResponse:
        self.ensure_non_streaming(request)
        raise ProviderNotImplementedError(
            "Tongyi provider is scaffolded only in Phase 1. TODO: implement vendor API mapping."
        )
