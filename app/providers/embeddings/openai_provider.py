"""OpenAI embedding provider."""

from __future__ import annotations

from typing import Any

from app.providers.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingProviderConfigurationError,
    EmbeddingProviderInvocationError,
    EmbeddingResult,
)

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - runtime dependency check
    OpenAI = None


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Embedding provider backed by OpenAI-compatible embeddings API."""

    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str | None = None,
        timeout_seconds: float = 60.0,
        client: Any | None = None,
    ) -> None:
        self._api_key = (api_key or "").strip()
        self._base_url = (base_url or "").strip() or None
        self._timeout_seconds = timeout_seconds
        self._client = client or self._build_client()

    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(
                vectors=[],
                model=model or "",
                dimensions=0,
            )
        if not model:
            raise EmbeddingProviderConfigurationError(
                "Embedding model is required for OpenAI embedding provider."
            )
        try:
            response = self._client.embeddings.create(model=model, input=texts)
        except Exception as exc:  # pragma: no cover - runtime dependency
            raise EmbeddingProviderInvocationError(
                f"OpenAI embedding request failed: {exc}"
            ) from exc

        vectors = [list(item.embedding) for item in response.data]
        dimensions = len(vectors[0]) if vectors else 0
        response_model = getattr(response, "model", None) or model
        return EmbeddingResult(vectors=vectors, model=response_model, dimensions=dimensions)

    def _build_client(self):
        if OpenAI is None:
            raise EmbeddingProviderConfigurationError(
                "Missing dependency 'openai'. Install requirements first."
            )
        if not self._api_key:
            raise EmbeddingProviderConfigurationError("OPENAI_API_KEY is required for embeddings.")

        kwargs: dict[str, Any] = {
            "api_key": self._api_key,
            "timeout": self._timeout_seconds,
        }
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return OpenAI(**kwargs)
