"""DeepSeek Provider 实现。"""

from __future__ import annotations

from typing import Any

from app.config import ProviderConfig
from app.providers.chat.openai_compatible_base import OpenAICompatibleBaseProvider


class DeepSeekProvider(OpenAICompatibleBaseProvider):
    """基于 OpenAI 兼容接口的 DeepSeek Provider。"""

    provider_name = "deepseek"

    def __init__(
        self,
        provider_config: ProviderConfig,
        client: Any | None = None,
    ) -> None:
        super().__init__(provider_config=provider_config, client=client)
