"""Service-layer orchestration for LLM chat requests."""

from __future__ import annotations

from dataclasses import replace

from app.config import AppConfig
from app.providers.registry import ProviderRegistry
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse
from app.services.prompt_service import PromptService


class LLMService:
    """Business-facing entrypoint for Phase 1 chat requests."""

    def __init__(
        self,
        config: AppConfig,
        registry: ProviderRegistry | None = None,
        prompt_service: PromptService | None = None,
    ) -> None:
        self._config = config
        self._registry = registry or ProviderRegistry(config)
        self._prompt_service = prompt_service or PromptService()

    def chat(self, request: LLMRequest) -> LLMResponse:
        normalized_request = self._normalize_request(request)
        provider = self._registry.get_provider(normalized_request.provider or "")
        return provider.chat(normalized_request)

    def _normalize_request(self, request: LLMRequest) -> LLMRequest:
        provider_name = request.provider or self._config.default_provider
        provider_config = self._registry.get_provider_config(provider_name)
        model_name = request.model or provider_config.default_model

        if not model_name:
            env_var_name = f"{provider_name.upper()}_DEFAULT_MODEL"
            raise ValueError(
                f"Model is required for provider '{provider_name}'. "
                f"Provide it in the request or configure {env_var_name}."
            )

        if request.stream:
            raise NotImplementedError(
                "Streaming is intentionally out of scope for this Phase 1 implementation."
            )

        normalized_messages = list(request.messages)
        if request.system_prompt:
            normalized_messages = self._prompt_service.build_messages(
                system_prompt=request.system_prompt,
                messages=normalized_messages,
            )

        if not normalized_messages:
            raise ValueError("At least one message is required.")

        return replace(
            request,
            provider=provider_name,
            model=model_name,
            messages=normalized_messages,
        )
