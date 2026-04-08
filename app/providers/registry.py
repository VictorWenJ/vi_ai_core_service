"""集中式 Provider 注册与解析。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import AppConfig
from app.providers.base import BaseLLMProvider, ProviderConfigurationError
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.doubao_provider import DoubaoProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.tongyi_provider import TongyiProvider


@dataclass(frozen=True)
class ProviderDescriptor:
    """用于治理友好查询的 Provider 成熟度与能力描述。"""

    provider_class: type[BaseLLMProvider]
    maturity: str
    capabilities: dict[str, Any] = field(default_factory=dict)


PROVIDER_CATALOG: dict[str, ProviderDescriptor] = {
    "openai": ProviderDescriptor(
        provider_class=OpenAIProvider,
        maturity="implemented",
        capabilities={
            "chat_non_streaming": True,
            "streaming": False,
            "multimodal": False,
            "tools": False,
            "structured_output": False,
        },
    ),
    "deepseek": ProviderDescriptor(
        provider_class=DeepSeekProvider,
        maturity="implemented",
        capabilities={
            "chat_non_streaming": True,
            "streaming": False,
            "multimodal": False,
            "tools": False,
            "structured_output": False,
        },
    ),
    "gemini": ProviderDescriptor(
        provider_class=GeminiProvider,
        maturity="scaffolded",
        capabilities={"chat_non_streaming": False},
    ),
    "doubao": ProviderDescriptor(
        provider_class=DoubaoProvider,
        maturity="scaffolded",
        capabilities={"chat_non_streaming": False},
    ),
    "tongyi": ProviderDescriptor(
        provider_class=TongyiProvider,
        maturity="scaffolded",
        capabilities={"chat_non_streaming": False},
    ),
}


class ProviderRegistry:
    """负责 Provider 解析的统一入口。"""

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
            descriptor = PROVIDER_CATALOG[normalized_name]
        except KeyError as exc:
            raise ProviderConfigurationError(
                f"不支持的 Provider '{provider_name}'。 "
                f"支持的 Provider：{', '.join(PROVIDER_CATALOG.keys())}。"
            ) from exc

        provider = descriptor.provider_class(self._config.get_provider_config(normalized_name))
        self._providers[normalized_name] = provider
        return provider

    def get_provider_config(self, provider_name: str):
        return self._config.get_provider_config(provider_name)

    def get_provider_descriptor(self, provider_name: str) -> ProviderDescriptor:
        normalized_name = provider_name.strip().lower()
        try:
            return PROVIDER_CATALOG[normalized_name]
        except KeyError as exc:
            raise ProviderConfigurationError(
                f"不支持的 Provider '{provider_name}'。 "
                f"支持的 Provider：{', '.join(PROVIDER_CATALOG.keys())}。"
            ) from exc
