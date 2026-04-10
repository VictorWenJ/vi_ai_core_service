"""Deterministic embedding provider for local and test usage."""

from __future__ import annotations

import hashlib
import math

from app.providers.embedding_base import BaseEmbeddingProvider, EmbeddingResult


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """Hash-based deterministic embedding implementation."""

    provider_name = "deterministic"

    def __init__(self, *, dimension: int = 64) -> None:
        if dimension <= 0:
            raise ValueError("Embedding dimension must be greater than 0.")
        self._dimension = dimension

    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        normalized_texts = [text for text in texts if text is not None]
        if not normalized_texts:
            return EmbeddingResult(
                vectors=[],
                model=model or "deterministic-text-v1",
                dimensions=self._dimension,
            )

        vectors = [self._embed_text(text) for text in normalized_texts]
        return EmbeddingResult(
            vectors=vectors,
            model=model or "deterministic-text-v1",
            dimensions=self._dimension,
        )

    def _embed_text(self, text: str) -> list[float]:
        payload = text.strip().encode("utf-8")
        digest = hashlib.sha256(payload).digest()
        values: list[float] = []
        for index in range(self._dimension):
            byte = digest[index % len(digest)]
            shifted = ((byte / 255.0) * 2.0) - 1.0
            values.append(shifted)

        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            return values
        return [value / norm for value in values]
