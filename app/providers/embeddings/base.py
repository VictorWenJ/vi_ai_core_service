"""Embedding provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class EmbeddingProviderError(Exception):
    """Base embedding provider error."""


class EmbeddingProviderConfigurationError(EmbeddingProviderError):
    """Raised when embedding provider configuration is invalid."""


class EmbeddingProviderInvocationError(EmbeddingProviderError):
    """Raised when embedding provider invocation fails."""


@dataclass
class EmbeddingResult:
    # 与输入文本一一对应的向量数组。
    vectors: list[list[float]]
    # 生成向量所使用的模型标识。
    model: str
    # 向量维度大小，单位为维（dimension）。
    dimensions: int


class BaseEmbeddingProvider(ABC):
    """Stable interface for text embedding providers."""

    provider_name: str = "base_embedding"

    @abstractmethod
    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        raise NotImplementedError
