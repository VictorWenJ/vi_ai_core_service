"""Base abstractions and shared exceptions for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import ProviderConfig
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse


class ProviderError(Exception):
    """Base class for provider-layer errors."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is missing or invalid."""


class ProviderInvocationError(ProviderError):
    """Raised when the vendor SDK or API call fails."""


class ProviderNotImplementedError(ProviderError):
    """Raised for provider scaffolds that are intentionally not implemented yet."""


class StreamNotImplementedError(ProviderError):
    """Raised when streaming is requested before the feature exists."""


class BaseLLMProvider(ABC):
    """Stable interface for all providers, including scaffolds."""

    provider_name: str = "base"

    def __init__(self, provider_config: ProviderConfig) -> None:
        self._provider_config = provider_config

    @property
    def provider_config(self) -> ProviderConfig:
        return self._provider_config

    @abstractmethod
    def chat(self, request: LLMRequest) -> LLMResponse:
        """Execute a standard non-streaming chat request."""

    def stream_chat(self, request: LLMRequest) -> LLMResponse:
        raise StreamNotImplementedError(
            f"Streaming is not implemented yet for provider '{self.provider_name}'."
        )

    def ensure_api_key(self) -> str:
        if not self.provider_config.api_key:
            raise ProviderConfigurationError(
                f"Provider '{self.provider_name}' requires an API key."
            )
        return self.provider_config.api_key

    def ensure_non_streaming(self, request: LLMRequest) -> None:
        if request.stream:
            raise StreamNotImplementedError(
                "This Phase 1 foundation only supports chat(), not streaming."
            )
