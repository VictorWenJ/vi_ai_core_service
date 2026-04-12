"""Factory for embedding providers."""

from __future__ import annotations

from app.config import AppConfig
from app.providers.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingProviderConfigurationError,
)
from app.providers.embeddings.deterministic_provider import DeterministicEmbeddingProvider
from app.providers.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.providers.embeddings.tei_provider import TEIEmbeddingProvider


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
    if provider_name == "tei":
        tei_config = app_config.tei_embedding_config
        return TEIEmbeddingProvider(
            base_url=tei_config.base_url,
            timeout_seconds=tei_config.timeout_seconds,
            default_model=app_config.rag_config.embedding_model,
        )
    raise EmbeddingProviderConfigurationError(
        f"Unsupported embedding provider '{provider_name}'."
    )
