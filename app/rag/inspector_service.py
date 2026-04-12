"""Knowledge inspector and retrieval debug domain service."""

from __future__ import annotations

from typing import Any

from app.config import AppConfig
from app.rag.document_service import RAGDocumentService
from app.rag.models import RetrievalResult
from app.rag.retrieval.service import KnowledgeRetrievalService
from app.rag.runtime import RAGRuntime


class RAGInspectorService:
    """Provide document/chunk inspection and retrieval debug helpers."""

    def __init__(
        self,
        *,
        app_config: AppConfig,
        rag_runtime: RAGRuntime,
        retrieval_service: KnowledgeRetrievalService,
        document_service: RAGDocumentService,
    ) -> None:
        self._app_config = app_config
        self._rag_runtime = rag_runtime
        self._retrieval_service = retrieval_service
        self._document_service = document_service

    def list_documents(self) -> list[dict[str, Any]]:
        return self._document_service.list_documents()

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        return self._document_service.get_document(document_id)

    def list_document_chunks(self, document_id: str) -> list[dict[str, Any]] | None:
        return self._document_service.list_document_chunks(document_id)

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        return self._document_service.get_chunk(chunk_id)

    def retrieve_for_chat(
        self,
        *,
        query_text: str,
        metadata_filter: dict[str, Any] | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        if self._rag_runtime.enabled:
            return self._rag_runtime.retrieve_for_chat(
                query_text=query_text,
                metadata_filter=metadata_filter,
                top_k=top_k,
            )
        try:
            return self._retrieval_service.retrieve(
                query_text=query_text,
                metadata_filter=metadata_filter,
                top_k=top_k,
            )
        except Exception as exc:
            resolved_top_k = top_k or self._app_config.rag_config.retrieval_top_k
            return RetrievalResult.degraded(
                query_text=query_text,
                top_k=resolved_top_k,
                metadata_filter=metadata_filter,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    def retrieval_debug(
        self,
        *,
        query_text: str,
        metadata_filter: dict[str, Any] | None = None,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        result = self.retrieve_for_chat(
            query_text=query_text,
            metadata_filter=metadata_filter,
            top_k=top_k,
        )
        return {
            "query_text": query_text,
            "top_k": result.trace.top_k,
            "status": result.trace.status,
            "hits": [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "score": chunk.score,
                    "title": chunk.title,
                    "source_type": chunk.source_type,
                    "origin_uri": chunk.origin_uri,
                    "metadata": dict(chunk.metadata),
                    "snippet": self._document_service.snippet(chunk.text, max_chars=240),
                }
                for chunk in result.retrieved_chunks
            ],
            "citations": [citation.to_dict() for citation in result.citations],
            "trace": result.trace.to_dict(),
        }

