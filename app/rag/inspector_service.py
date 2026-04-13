"""Knowledge inspector 与检索调试应用服务。"""

from __future__ import annotations

from typing import Any

from app.config import AppConfig
from app.rag.content_store.local_store import LocalRAGContentStore
from app.rag.models import RetrievalResult
from app.rag.repository.build_document_repository import BuildDocumentRepository
from app.rag.repository.build_task_repository import BuildTaskRepository
from app.rag.repository.chunk_repository import ChunkRepository
from app.rag.repository.document_repository import DocumentRepository
from app.rag.repository.document_version_repository import DocumentVersionRepository
from app.rag.repository.read_models import BuildTaskRecord
from app.rag.retrieval.service import KnowledgeRetrievalService
from app.rag.retrieval.vector_store import BaseVectorStore
from app.rag.runtime import RAGRuntime


class RAGInspectorService:
    """提供 document/chunk/build 查询与 retrieval debug 能力。"""

    def __init__(
        self,
        *,
        app_config: AppConfig,
        rag_runtime: RAGRuntime,
        retrieval_service: KnowledgeRetrievalService,
        document_repository: DocumentRepository,
        document_version_repository: DocumentVersionRepository,
        build_task_repository: BuildTaskRepository,
        build_document_repository: BuildDocumentRepository,
        chunk_repository: ChunkRepository,
        content_store: LocalRAGContentStore,
        vector_store: BaseVectorStore,
    ) -> None:
        self._app_config = app_config
        self._rag_runtime = rag_runtime
        self._retrieval_service = retrieval_service
        self._document_repository = document_repository
        self._document_version_repository = document_version_repository
        self._build_task_repository = build_task_repository
        self._build_document_repository = build_document_repository
        self._chunk_repository = chunk_repository
        self._content_store = content_store
        self._vector_store = vector_store

    def list_documents(self) -> list[dict[str, Any]]:
        documents = self._document_repository.list_documents()
        chunk_count_mapping = self._document_repository.get_chunk_counts_by_document_ids(
            document_ids=[document.document_id for document in documents]
        )
        payloads: list[dict[str, Any]] = []
        for document in documents:
            payloads.append(
                {
                    "document_id": document.document_id,
                    "title": document.title,
                    "source_type": document.source_type,
                    "origin_uri": document.origin_uri,
                    "file_name": document.file_name,
                    "jurisdiction": document.jurisdiction,
                    "domain": document.domain,
                    "tags": list(document.tags_details),
                    "effective_at": None,
                    "updated_at": document.updated_at,
                    "visibility": document.visibility,
                    "metadata": {},
                    "chunk_count": int(chunk_count_mapping.get(document.document_id, 0)),
                }
            )
        return payloads

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        document_payload = self._document_repository.get_document(document_id=document_id)
        if document_payload is None:
            return None
        latest_version_id = document_payload.latest_version_id
        version_payload = (
            self._document_version_repository.get_version(version_id=latest_version_id)
            if latest_version_id
            else None
        )
        content = ""
        metadata = {}
        if version_payload is not None:
            content = self._content_store.read_normalized_text(
                storage_path=version_payload.normalized_storage_path
            )
            metadata = dict(version_payload.metadata_details or {})
        chunk_count_mapping = self._document_repository.get_chunk_counts_by_document_ids(
            document_ids=[document_id]
        )
        return {
            "document_id": document_payload.document_id,
            "title": document_payload.title,
            "source_type": document_payload.source_type,
            "content": content,
            "origin_uri": document_payload.origin_uri,
            "file_name": document_payload.file_name,
            "jurisdiction": document_payload.jurisdiction,
            "domain": document_payload.domain,
            "tags": list(document_payload.tags_details),
            "effective_at": None,
            "updated_at": document_payload.updated_at,
            "visibility": document_payload.visibility,
            "metadata": metadata,
            "chunk_count": int(chunk_count_mapping.get(document_id, 0)),
            "latest_version_id": latest_version_id,
        }

    def list_document_chunks(self, document_id: str) -> list[dict[str, Any]] | None:
        document_payload = self._document_repository.get_document(document_id=document_id)
        if document_payload is None:
            return None
        chunk_payloads = self._chunk_repository.list_by_document_id(document_id=document_id)
        return [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "embedding_model": chunk.embedding_model_name,
                "chunk_text_preview": chunk.chunk_preview,
                "metadata": dict(chunk.metadata_details or {}),
                "vector_point_id": chunk.vector_point_id,
                "vector_dimension": chunk.vector_dimension,
                "vector_collection": chunk.vector_collection,
            }
            for chunk in chunk_payloads
        ]

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        chunk_payload = self._chunk_repository.get_chunk(chunk_id=chunk_id)
        if chunk_payload is None:
            return None
        return {
            "chunk_id": chunk_payload.chunk_id,
            "document_id": chunk_payload.document_id,
            "chunk_index": chunk_payload.chunk_index,
            "token_count": chunk_payload.token_count,
            "embedding_model": chunk_payload.embedding_model_name,
            "chunk_text": chunk_payload.chunk_preview,
            "chunk_text_preview": chunk_payload.chunk_preview,
            "metadata": dict(chunk_payload.metadata_details or {}),
            "vector_point_id": chunk_payload.vector_point_id,
            "vector_dimension": chunk_payload.vector_dimension,
            "vector_collection": chunk_payload.vector_collection,
            "document_version_id": chunk_payload.document_version_id,
            "build_id": chunk_payload.build_id,
        }

    def get_chunk_vector_detail(self, *, chunk_id: str) -> dict[str, Any] | None:
        chunk_payload = self._chunk_repository.get_chunk(chunk_id=chunk_id)
        if chunk_payload is None:
            return None
        vector_payload = self._vector_store.fetch_point(
            point_id=chunk_payload.vector_point_id
        )
        if vector_payload is None:
            return {
                "chunk_id": chunk_id,
                "vector_point_id": chunk_payload.vector_point_id,
                "vector_collection": chunk_payload.vector_collection,
                "found": False,
                "vector": [],
                "vector_dimension": chunk_payload.vector_dimension,
                "payload": {},
            }
        return {
            "chunk_id": chunk_id,
            "vector_point_id": chunk_payload.vector_point_id,
            "vector_collection": chunk_payload.vector_collection,
            "found": True,
            "vector": list(vector_payload.get("vector") or []),
            "vector_dimension": int(vector_payload.get("vector_dimension") or 0),
            "payload": dict(vector_payload.get("payload") or {}),
        }

    def list_builds(self) -> list[dict[str, Any]]:
        task_payloads = self._build_task_repository.list_tasks()
        return [self._to_build_detail_payload(task_payload) for task_payload in task_payloads]

    def get_build(self, build_id: str) -> dict[str, Any] | None:
        task_payload = self._build_task_repository.get_task(build_id=build_id)
        if task_payload is None:
            return None
        return self._to_build_detail_payload(task_payload)

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
                    "snippet": self._snippet(chunk.text, max_chars=240),
                }
                for chunk in result.retrieved_chunks
            ],
            "citations": [citation.to_dict() for citation in result.citations],
            "trace": result.trace.to_dict(),
        }

    @staticmethod
    def _snippet(text: str, *, max_chars: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= max_chars:
            return normalized
        if max_chars <= 3:
            return normalized[:max_chars]
        return f"{normalized[: max_chars - 3]}..."

    def _to_build_detail_payload(self, task_payload: BuildTaskRecord) -> dict[str, Any]:
        build_id = task_payload.build_id
        build_documents = self._build_document_repository.list_by_build_id(build_id=build_id)
        statistics_details = dict(task_payload.statistics_details or {})
        quality_gate_details = dict(task_payload.quality_gate_details or {})
        return {
            "metadata": {
                "build_id": build_id,
                "version_id": task_payload.build_version_id,
                "build_version_id": task_payload.build_version_id,
                "status": task_payload.status,
                "chunk_strategy_name": task_payload.chunk_strategy_name,
                "chunk_strategy_version": task_payload.chunk_strategy_name,
                "embedding_model_name": task_payload.embedding_model_name,
                "embedding_model_version": task_payload.embedding_model_name,
                "started_at": task_payload.started_at,
                "completed_at": task_payload.completed_at,
                "created_at": task_payload.created_at,
            },
            "statistics": {
                "requested_document_count": int(
                    statistics_details.get("requested_document_count", 0)
                ),
                "processed_document_count": int(
                    statistics_details.get("processed_document_count", 0)
                ),
                "skipped_document_count": int(
                    statistics_details.get("skipped_document_count", 0)
                ),
                "failed_document_count": int(
                    statistics_details.get("failed_document_count", 0)
                ),
                "chunk_count": int(statistics_details.get("chunk_count", 0)),
                "upserted_count": int(statistics_details.get("upserted_count", 0)),
                "embedding_batch_count": int(
                    statistics_details.get("embedding_batch_count", 0)
                ),
                "latency_ms": float(statistics_details.get("latency_ms", 0.0)),
            },
            "quality_gate": {
                "passed": bool(quality_gate_details.get("passed", False)),
                "failed_rules": list(quality_gate_details.get("failed_rules") or []),
                "failure_ratio": float(quality_gate_details.get("failure_ratio", 0.0)),
                "empty_chunk_ratio": float(quality_gate_details.get("empty_chunk_ratio", 0.0)),
                "max_failure_ratio": float(
                    quality_gate_details.get("max_failure_ratio", 0.0)
                ),
                "max_empty_chunk_ratio": float(
                    quality_gate_details.get("max_empty_chunk_ratio", 0.0)
                ),
            },
            "manifest": dict(task_payload.manifest_details or {}),
            "ingestion_results": [
                {
                    "document_id": record.document_id,
                    "document_version_id": record.document_version_id,
                    "chunk_count": record.chunk_count,
                    "vector_count": record.vector_count,
                    "action": record.action,
                    "error_message": record.error_message,
                }
                for record in build_documents
            ],
        }
