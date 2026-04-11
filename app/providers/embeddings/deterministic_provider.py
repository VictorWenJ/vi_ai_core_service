"""Deterministic embedding provider for local and test usage."""

from __future__ import annotations

import hashlib
import math

from app.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResult


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
        # 1) 先去掉首尾空白并转为 UTF-8 字节，作为稳定哈希输入。
        payload = text.strip().encode("utf-8")
        # 2) 计算 SHA-256 摘要，得到固定长度字节序列。
        digest = hashlib.sha256(payload).digest()
        values: list[float] = []
        # 3) 按目标维度循环取摘要字节，并把 [0,255] 线性映射到 [-1,1]。
        for index in range(self._dimension):
            byte = digest[index % len(digest)]
            shifted = ((byte / 255.0) * 2.0) - 1.0
            values.append(shifted)

        # 4) 对向量做 L2 归一化，避免长度差异影响余弦相似度。
        norm = math.sqrt(sum(value * value for value in values))
        # 极端情况下范数为 0 时直接返回原向量，避免除零错误。
        if norm == 0:
            return values
        return [value / norm for value in values]
