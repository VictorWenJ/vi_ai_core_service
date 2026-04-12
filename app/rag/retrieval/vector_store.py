"""Vector store abstractions for knowledge retrieval."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math
from typing import Any
from uuid import uuid4

from app.rag.models import KnowledgeChunk, KnowledgeDocument, RetrievedChunk


class BaseVectorStore(ABC):
    """Stable vector store interface for RAG."""

    @abstractmethod
    def ensure_collection(self, vector_size: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert(
        self,
        *,
        document: KnowledgeDocument,
        chunks: list[KnowledgeChunk],
        vectors: list[list[float]],
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        *,
        query_vector: list[float],
        top_k: int,
        metadata_filter: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        raise NotImplementedError

    @abstractmethod
    def get_collection_name(self) -> str:
        """返回向量集合名称。"""
        raise NotImplementedError

    @abstractmethod
    def fetch_point(self, *, point_id: str) -> dict[str, Any] | None:
        """按 point_id 回读向量详情。"""
        raise NotImplementedError


@dataclass
class _InMemoryEntry:
    # 入库向量数据。
    vector: list[float]
    # 与向量绑定的业务 payload。
    payload: dict[str, Any]


class InMemoryVectorStore(BaseVectorStore):
    """Deterministic in-memory vector store for tests and local fallback."""

    def __init__(self) -> None:
        self._entries: list[_InMemoryEntry] = []
        self._vector_size: int | None = None

    def ensure_collection(self, vector_size: int) -> None:
        if vector_size <= 0:
            raise ValueError("vector_size must be > 0.")
        if self._vector_size is None:
            self._vector_size = vector_size
        elif self._vector_size != vector_size:
            raise ValueError("Vector size mismatch for in-memory collection.")

    def upsert(
        self,
        *,
        document: KnowledgeDocument,
        chunks: list[KnowledgeChunk],
        vectors: list[list[float]],
    ) -> int:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors size mismatch.")
        if not chunks:
            return 0

        self.ensure_collection(len(vectors[0]))
        for chunk, vector in zip(chunks, vectors, strict=True):
            payload = _build_chunk_payload(document=document, chunk=chunk)
            self._entries = [
                entry
                for entry in self._entries
                if entry.payload["chunk_id"] != chunk.chunk_id
            ]
            self._entries.append(_InMemoryEntry(vector=list(vector), payload=payload))
        return len(chunks)

    def query(
        self,
        *,
        query_vector: list[float],
        top_k: int,
        metadata_filter: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        if not self._entries:
            return []

        scored: list[tuple[float, dict[str, Any]]] = []
        for entry in self._entries:
            if metadata_filter and not _matches_filter(entry.payload, metadata_filter):
                continue
            score = _cosine_similarity(query_vector, entry.vector)
            if score_threshold is not None and score < score_threshold:
                continue
            scored.append((score, entry.payload))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = scored[:top_k]
        return [self._to_retrieved_chunk(score, payload) for score, payload in selected]

    def get_collection_name(self) -> str:
        return "in_memory_vector_store"

    def fetch_point(self, *, point_id: str) -> dict[str, Any] | None:
        for entry in self._entries:
            if entry.payload.get("chunk_id") != point_id:
                continue
            return {
                "point_id": point_id,
                "vector": list(entry.vector),
                "vector_dimension": len(entry.vector),
                "payload": dict(entry.payload),
            }
        return None

    @staticmethod
    def _to_retrieved_chunk(score: float, payload: dict[str, Any]) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=payload["chunk_id"],
            document_id=payload["document_id"],
            text=payload.get("chunk_text", ""),
            score=score,
            title=payload.get("title"),
            origin_uri=payload.get("origin_uri"),
            source_type=payload.get("source_type"),
            jurisdiction=payload.get("jurisdiction"),
            domain=payload.get("domain"),
            effective_at=payload.get("effective_at"),
            updated_at=payload.get("updated_at"),
            metadata=dict(payload.get("metadata", {})),
        )


class QdrantVectorStore(BaseVectorStore):
    """Qdrant vector store implementation."""

    def __init__(
        self,
        *,
        url: str,
        collection_name: str,
        api_key: str | None = None,
    ) -> None:
        self._url = url
        self._collection_name = collection_name
        self._api_key = api_key
        self._client = self._build_client()

    def ensure_collection(self, vector_size: int) -> None:
        qdrant_models = self._import_qdrant_models()
        if self._client.collection_exists(collection_name=self._collection_name):
            return
        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=vector_size,
                distance=qdrant_models.Distance.COSINE,
            ),
        )

    def upsert(
        self,
        *,
        document: KnowledgeDocument,
        chunks: list[KnowledgeChunk],
        vectors: list[list[float]],
    ) -> int:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors size mismatch.")
        if not chunks:
            return 0
        self.ensure_collection(len(vectors[0]))

        qdrant_models = self._import_qdrant_models()
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            payload = _build_chunk_payload(document=document, chunk=chunk)
            points.append(
                qdrant_models.PointStruct(
                    id=chunk.chunk_id or uuid4().hex,
                    vector=vector,
                    payload=payload,
                )
            )

        self._client.upsert(collection_name=self._collection_name, points=points)
        return len(points)

    def query(
        self,
        *,
        query_vector: list[float],
        top_k: int,
        metadata_filter: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        qdrant_filter = self._build_qdrant_filter(metadata_filter)
        hits = self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
            score_threshold=score_threshold,
        )
        results: list[RetrievedChunk] = []
        for hit in hits:
            payload = dict(hit.payload or {})
            results.append(
                RetrievedChunk(
                    chunk_id=payload.get("chunk_id", str(hit.id)),
                    document_id=payload.get("document_id", ""),
                    text=payload.get("chunk_text", ""),
                    score=float(hit.score),
                    title=payload.get("title"),
                    origin_uri=payload.get("origin_uri"),
                    source_type=payload.get("source_type"),
                    jurisdiction=payload.get("jurisdiction"),
                    domain=payload.get("domain"),
                    effective_at=payload.get("effective_at"),
                    updated_at=payload.get("updated_at"),
                    metadata=dict(payload.get("metadata", {})),
                )
            )
        return results

    def _build_client(self):
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise RuntimeError(
                "Missing dependency 'qdrant-client'. Install requirements first."
            ) from exc
        return QdrantClient(url=self._url, api_key=self._api_key)

    @staticmethod
    def _import_qdrant_models():
        from qdrant_client.http import models as qdrant_models  # pragma: no cover

        return qdrant_models

    def _build_qdrant_filter(self, metadata_filter: dict[str, Any] | None):
        if not metadata_filter:
            return None
        qdrant_models = self._import_qdrant_models()
        conditions = []
        for key, value in metadata_filter.items():
            if isinstance(value, list):
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchAny(any=value),
                    )
                )
            else:
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=value),
                    )
                )
        return qdrant_models.Filter(must=conditions)

    def get_collection_name(self) -> str:
        return self._collection_name

    def fetch_point(self, *, point_id: str) -> dict[str, Any] | None:
        points = self._client.retrieve(
            collection_name=self._collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=True,
        )
        if not points:
            return None
        point = points[0]
        vector = point.vector
        if isinstance(vector, dict):
            first_vector = next(iter(vector.values()), [])
        else:
            first_vector = vector or []
        payload = dict(point.payload or {})
        return {
            "point_id": str(point.id),
            "vector": list(first_vector),
            "vector_dimension": len(first_vector),
            "payload": payload,
        }


def _build_chunk_payload(
    *,
    document: KnowledgeDocument,
    chunk: KnowledgeChunk,
) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": document.document_id,
        "chunk_text": chunk.chunk_text,
        "chunk_index": chunk.chunk_index,
        "token_count": chunk.token_count,
        "embedding_model": chunk.embedding_model,
        "title": document.title,
        "origin_uri": document.origin_uri,
        "source_type": document.source_type,
        "jurisdiction": document.jurisdiction,
        "domain": document.domain,
        "effective_at": document.effective_at,
        "updated_at": document.updated_at,
        "visibility": document.visibility,
        "file_name": document.file_name,
        "tags": list(document.tags),
        "metadata": {
            **dict(document.metadata),
            **dict(chunk.metadata or {}),
        },
    }


def _matches_filter(payload: dict[str, Any], metadata_filter: dict[str, Any]) -> bool:
    for key, expected in metadata_filter.items():
        actual = payload.get(key)
        if isinstance(expected, list):
            if isinstance(actual, list):
                if not any(item in actual for item in expected):
                    return False
            else:
                if actual not in expected:
                    return False
            continue
        if actual != expected:
            return False
    return True


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    min_size = min(len(left), len(right))
    numerator = sum(left[i] * right[i] for i in range(min_size))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
