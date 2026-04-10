"""Retrieval service for chat orchestration."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.observability.log_until import log_report
from app.providers.embedding_base import BaseEmbeddingProvider
from app.rag.citation.formatter import build_citations
from app.rag.models import RetrievalResult, RetrievalTrace
from app.rag.retrieval.rendering import render_knowledge_block
from app.rag.retrieval.vector_store import BaseVectorStore


class RetrievalExecutionError(RuntimeError):
    """Raised when retrieval cannot be completed."""


class KnowledgeRetrievalService:
    """Query embeddings + vector index and build citation-ready output."""

    def __init__(
        self,
        *,
        embedding_provider: BaseEmbeddingProvider,
        vector_store: BaseVectorStore,
        embedding_model: str,
        default_top_k: int,
        default_score_threshold: float | None = None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._embedding_model = embedding_model
        self._default_top_k = default_top_k
        self._default_score_threshold = default_score_threshold

    def retrieve(
        self,
        *,
        query_text: str,
        top_k: int | None = None,
        metadata_filter: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> RetrievalResult:
        started_at = perf_counter()
        resolved_top_k = top_k or self._default_top_k
        resolved_filter = dict(metadata_filter or {})
        resolved_score_threshold = (
            score_threshold
            if score_threshold is not None
            else self._default_score_threshold
        )
        try:
            embedding_result = self._embedding_provider.embed_texts(
                [query_text],
                model=self._embedding_model,
            )
            if not embedding_result.vectors:
                raise RetrievalExecutionError("Embedding provider returned empty vectors.")

            query_vector = embedding_result.vectors[0]
            retrieved_chunks = self._vector_store.query(
                query_vector=query_vector,
                top_k=resolved_top_k,
                metadata_filter=resolved_filter,
                score_threshold=resolved_score_threshold,
            )
            citations = build_citations(retrieved_chunks)
            knowledge_block = render_knowledge_block(retrieved_chunks)
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            trace = RetrievalTrace(
                status="succeeded",
                query_text=query_text,
                top_k=resolved_top_k,
                metadata_filter=resolved_filter,
                hit_count=len(retrieved_chunks),
                citation_count=len(citations),
                latency_ms=latency_ms,
            )
            log_report(
                "rag.retrieval.succeeded",
                {
                    "query_text": query_text,
                    "top_k": resolved_top_k,
                    "metadata_filter": resolved_filter,
                    "score_threshold": resolved_score_threshold,
                    "hit_count": len(retrieved_chunks),
                    "citation_count": len(citations),
                    "latency_ms": latency_ms,
                },
            )
            return RetrievalResult(
                knowledge_block=knowledge_block,
                retrieved_chunks=retrieved_chunks,
                citations=citations,
                trace=trace,
            )
        except Exception as exc:
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            log_report(
                "rag.retrieval.failed",
                {
                    "query_text": query_text,
                    "top_k": resolved_top_k,
                    "metadata_filter": resolved_filter,
                    "score_threshold": resolved_score_threshold,
                    "latency_ms": latency_ms,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise RetrievalExecutionError(str(exc)) from exc
