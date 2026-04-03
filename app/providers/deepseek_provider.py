"""DeepSeek provider implementation."""

from __future__ import annotations

from typing import Any

from app.config import ProviderConfig
from app.providers.openai_compatible_base import OpenAICompatibleBaseProvider


class DeepSeekProvider(OpenAICompatibleBaseProvider):
    """DeepSeek provider built on the OpenAI-compatible API surface."""

    provider_name = "deepseek"

    def __init__(
        self,
        provider_config: ProviderConfig,
        client: Any | None = None,
    ) -> None:
        super().__init__(provider_config=provider_config, client=client)
