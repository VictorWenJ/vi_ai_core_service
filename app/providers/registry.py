"""Centralized provider registration and resolution."""

from __future__ import annotations

from app.config import AppConfig
from app.providers.base import BaseLLMProvider, ProviderConfigurationError
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.doubao_provider import DoubaoProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.tongyi_provider import TongyiProvider

PROVIDER_CLASS_MAP: dict[str, type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "gemini": GeminiProvider,
    "doubao": DoubaoProvider,
    "tongyi": TongyiProvider,
}


class ProviderRegistry:
    """Single place responsible for provider resolution."""

    def __init__(
        self,
        config: AppConfig,
        provider_overrides: dict[str, BaseLLMProvider] | None = None,
    ) -> None:
        self._config = config
        self._providers: dict[str, BaseLLMProvider] = {}

        if provider_overrides:
            self._providers.update(
                {
                    provider_name.strip().lower(): provider
                    for provider_name, provider in provider_overrides.items()
                }
            )

    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        normalized_name = provider_name.strip().lower()
        if normalized_name in self._providers:
            return self._providers[normalized_name]

        try:
            provider_class = PROVIDER_CLASS_MAP[normalized_name]
        except KeyError as exc:
            raise ProviderConfigurationError(
                f"Unsupported provider '{provider_name}'. "
                f"Supported providers: {', '.join(PROVIDER_CLASS_MAP.keys())}."
            ) from exc

        provider = provider_class(self._config.get_provider_config(normalized_name))
        self._providers[normalized_name] = provider
        return provider

    def get_provider_config(self, provider_name: str):
        return self._config.get_provider_config(provider_name)
