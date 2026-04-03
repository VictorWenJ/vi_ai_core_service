"""Shared base for OpenAI-compatible chat providers."""

from __future__ import annotations

from typing import Any

from app.config import ProviderConfig
from app.providers.base import (
    BaseLLMProvider,
    ProviderConfigurationError,
    ProviderInvocationError,
)
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse, LLMUsage

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime if dependency is missing
    OpenAI = None


class OpenAICompatibleBaseProvider(BaseLLMProvider):
    """Base implementation for providers that expose an OpenAI-compatible API."""

    provider_name = "openai_compatible"

    def __init__(
        self,
        provider_config: ProviderConfig,
        client: Any | None = None,
    ) -> None:
        super().__init__(provider_config)
        self._client = client or self._build_client()

    def chat(self, request: LLMRequest) -> LLMResponse:
        self.ensure_non_streaming(request)

        if not request.model:
            raise ProviderConfigurationError(
                f"Provider '{self.provider_name}' requires a model."
            )

        payload = {
            "model": request.model,
            "messages": self._to_vendor_messages(request),
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        try:
            vendor_response = self._client.chat.completions.create(**payload)
        except Exception as exc:  # pragma: no cover - depends on vendor runtime
            raise ProviderInvocationError(
                f"Provider '{self.provider_name}' request failed: {exc}"
            ) from exc

        return self._to_response(vendor_response)

    def _build_client(self):
        if OpenAI is None:
            raise ProviderConfigurationError(
                "Missing dependency 'openai'. Install it with 'pip install openai'."
            )

        client_kwargs = {
            "api_key": self.ensure_api_key(),
            "timeout": self.provider_config.timeout_seconds,
        }
        if self.provider_config.base_url:
            client_kwargs["base_url"] = self.provider_config.base_url

        return OpenAI(**client_kwargs)

    def _to_vendor_messages(self, request: LLMRequest) -> list[dict[str, str]]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in request.messages
        ]

    def _to_response(self, vendor_response: Any) -> LLMResponse:
        choice = vendor_response.choices[0]
        usage = getattr(vendor_response, "usage", None)
        response_usage = None
        if usage is not None:
            response_usage = LLMUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", None),
                completion_tokens=getattr(usage, "completion_tokens", None),
                total_tokens=getattr(usage, "total_tokens", None),
            )

        raw_response = {
            key: getattr(vendor_response, key)
            for key in ("id", "object", "created")
            if getattr(vendor_response, key, None) is not None
        } or None

        return LLMResponse(
            content=choice.message.content or "",
            provider=self.provider_name,
            model=getattr(vendor_response, "model", None),
            usage=response_usage,
            finish_reason=getattr(choice, "finish_reason", None),
            metadata={},
            raw_response=raw_response,
        )
