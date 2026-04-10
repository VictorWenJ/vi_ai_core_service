"""Runtime entrypoint for retrieval orchestration and degradation handling."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.config import AppConfig
from app.observability.log_until import log_report
from app.providers.embedding_registry import build_embedding_provider
from app.rag.models import RetrievalResult
from app.rag.retrieval.service import KnowledgeRetrievalService
from app.rag.retrieval.vector_store import InMemoryVectorStore, QdrantVectorStore


class RAGRuntime:
    """Service-facing runtime for retrieval and citation output."""

    def __init__(
        self,
        *,
        enabled: bool,
        retrieval_service: KnowledgeRetrievalService | None = None,
        default_top_k: int = 0,
    ) -> None:
        self._enabled = enabled
        self._retrieval_service = retrieval_service
        self._default_top_k = default_top_k

    @classmethod
    def from_app_config(cls, app_config: AppConfig) -> "RAGRuntime":
        rag_config = app_config.rag_config
        if not rag_config.enabled:
            return cls(
                enabled=False,
                retrieval_service=None,
                default_top_k=rag_config.retrieval_top_k,
            )

        embedding_provider = build_embedding_provider(app_config)
        vector_store = QdrantVectorStore(
            url=rag_config.qdrant_url,
            collection_name=rag_config.qdrant_collection,
            api_key=rag_config.qdrant_api_key,
        )
        retrieval_service = KnowledgeRetrievalService(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            embedding_model=rag_config.embedding_model,
            default_top_k=rag_config.retrieval_top_k,
            default_score_threshold=rag_config.score_threshold,
        )
        return cls(
            enabled=True,
            retrieval_service=retrieval_service,
            default_top_k=rag_config.retrieval_top_k,
        )

    @classmethod
    def disabled(cls, *, default_top_k: int = 4) -> "RAGRuntime":
        return cls(enabled=False, retrieval_service=None, default_top_k=default_top_k)

    @classmethod
    def for_testing(
        cls,
        app_config: AppConfig,
    ) -> "RAGRuntime":
        embedding_provider = build_embedding_provider(app_config)
        vector_store = InMemoryVectorStore()
        retrieval_service = KnowledgeRetrievalService(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            embedding_model=app_config.rag_config.embedding_model,
            default_top_k=app_config.rag_config.retrieval_top_k,
            default_score_threshold=app_config.rag_config.score_threshold,
        )
        return cls(
            enabled=True,
            retrieval_service=retrieval_service,
            default_top_k=app_config.rag_config.retrieval_top_k,
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def retrieve_for_chat(
        self,
        *,
        query_text: str,
        metadata_filter: dict[str, Any] | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        resolved_top_k = top_k or self._default_top_k
        if not self._enabled or self._retrieval_service is None:
            result = RetrievalResult.disabled(
                query_text=query_text,
                top_k=resolved_top_k,
                metadata_filter=metadata_filter,
            )
            log_report(
                "rag.retrieval.disabled",
                result.trace.to_dict(),
            )
            return result

        started_at = perf_counter()
        try:
            return self._retrieval_service.retrieve(
                query_text=query_text,
                top_k=resolved_top_k,
                metadata_filter=metadata_filter,
            )
        except Exception as exc:
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            result = RetrievalResult.degraded(
                query_text=query_text,
                top_k=resolved_top_k,
                metadata_filter=metadata_filter,
                error_type=type(exc).__name__,
                error_message=str(exc),
                latency_ms=latency_ms,
            )
            log_report(
                "rag.retrieval.degraded",
                result.trace.to_dict(),
            )
            return result
