"""Factory for embedding providers."""

from __future__ import annotations

from app.config import AppConfig
from app.providers.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingProviderConfigurationError,
)
from app.providers.embeddings.deterministic_provider import DeterministicEmbeddingProvider
from app.providers.embeddings.openai_provider import OpenAIEmbeddingProvider


def build_embedding_provider(app_config: AppConfig) -> BaseEmbeddingProvider:
    provider_name = app_config.rag_config.embedding_provider.strip().lower()
    if provider_name == "deterministic":
        return DeterministicEmbeddingProvider(
            dimension=app_config.rag_config.embedding_dimension
        )
    if provider_name == "openai":
        openai_config = app_config.get_provider_config("openai")
        return OpenAIEmbeddingProvider(
            api_key=openai_config.api_key,
            base_url=openai_config.base_url,
            timeout_seconds=openai_config.timeout_seconds,
        )
    raise EmbeddingProviderConfigurationError(
        f"Unsupported embedding provider '{provider_name}'."
    )
