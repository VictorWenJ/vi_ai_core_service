"""LLM Provider 的基础抽象与共享异常。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import ProviderConfig
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse


class ProviderError(Exception):
    """Provider 层错误基类。"""


class ProviderConfigurationError(ProviderError):
    """当 Provider 配置缺失或无效时抛出。"""


class ProviderInvocationError(ProviderError):
    """当厂商 SDK 或 API 调用失败时抛出。"""


class ProviderNotImplementedError(ProviderError):
    """用于尚未实现的 Provider 脚手架。"""


class StreamNotImplementedError(ProviderError):
    """在功能未实现时请求流式能力会抛出。"""


class BaseLLMProvider(ABC):
    """所有 Provider（含脚手架）的稳定接口。"""

    provider_name: str = "base"

    def __init__(self, provider_config: ProviderConfig) -> None:
        self._provider_config = provider_config

    @property
    def provider_config(self) -> ProviderConfig:
        return self._provider_config

    @abstractmethod
    def chat(self, request: LLMRequest) -> LLMResponse:
        """执行标准非流式聊天请求。"""

    def stream_chat(self, request: LLMRequest) -> LLMResponse:
        raise StreamNotImplementedError(
            f"Provider '{self.provider_name}' 暂未实现流式能力。"
        )

    def ensure_api_key(self) -> str:
        if not self.provider_config.api_key:
            raise ProviderConfigurationError(
                f"Provider '{self.provider_name}' 需要 API Key。"
            )
        return self.provider_config.api_key

    def ensure_non_streaming(self, request: LLMRequest) -> None:
        if request.stream:
            raise StreamNotImplementedError(
                "当前基础阶段仅支持 chat()，不支持流式。"
            )
