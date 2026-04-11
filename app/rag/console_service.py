"""Internal console service for ingestion/build/inspection/evaluation APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from app.config import AppConfig
from app.context.policies.tokenizer import CharacterTokenCounter
from app.observability.log_until import log_report
from app.providers.embeddings.registry import build_embedding_provider
from app.rag.evaluation.models import (
    AnswerLabel,
    CitationLabel,
    EvaluationDataset,
    EvaluationRunResult,
    EvaluationSample,
    RetrievalLabel,
)
from app.rag.evaluation.runner import RAGEvaluationRunner
from app.rag.ingestion.chunker import StructuredTokenChunker
from app.rag.ingestion.cleaner import DocumentCleaner
from app.rag.ingestion.parser import DocumentParser
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline
from app.rag.models import (
    KnowledgeChunk,
    KnowledgeDocument,
    OfflineBuildManifest,
    OfflineBuildResult,
    RetrievalResult,
    now_utc_iso,
)
from app.rag.retrieval.service import KnowledgeRetrievalService
from app.rag.retrieval.vector_store import InMemoryVectorStore, QdrantVectorStore
from app.rag.runtime import RAGRuntime


def _utc_version_suffix() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class InternalConsoleRAGService:
    """Provide minimal backend capabilities for internal console pages."""

    def __init__(self, *, app_config: AppConfig, rag_runtime: RAGRuntime) -> None:
        self._app_config = app_config
        self._rag_runtime = rag_runtime
        self._lock = RLock()

        parser = DocumentParser()
        cleaner = DocumentCleaner()
        chunker = StructuredTokenChunker(token_counter=CharacterTokenCounter())
        embedding_provider = build_embedding_provider(app_config)
        vector_store = self._build_vector_store(app_config=app_config)
        rag_config = app_config.rag_config

        self._retrieval_service = KnowledgeRetrievalService(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            embedding_model=rag_config.embedding_model,
            default_top_k=rag_config.retrieval_top_k,
            default_score_threshold=rag_config.score_threshold,
        )
        self._pipeline = KnowledgeIngestionPipeline(
            parser=parser,
            cleaner=cleaner,
            chunker=chunker,
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            embedding_model=rag_config.embedding_model,
            chunk_token_size=rag_config.chunk_token_size,
            overlap_token_size=rag_config.chunk_overlap_token_size,
            chunk_strategy_version="structure-token-overlap-v1",
            embedding_model_version=rag_config.embedding_model,
        )
        self._evaluation_runner = RAGEvaluationRunner(rag_runtime=self)

        self._documents: dict[str, KnowledgeDocument] = {}
        self._chunks: dict[str, KnowledgeChunk] = {}
        self._document_chunk_ids: dict[str, list[str]] = {}

        self._manifest: OfflineBuildManifest | None = None
        self._build_results: dict[str, OfflineBuildResult] = {}
        self._build_ids: list[str] = []

        self._evaluation_runs: dict[str, EvaluationRunResult] = {}
        self._evaluation_run_ids: list[str] = []

    def upload_document(
        self,
        *,
        content: str,
        file_name: str,
        title: str | None = None,
        document_id: str | None = None,
        source_type: str | None = None,
        jurisdiction: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("上传文档内容不能为空。")
        resolved_source_type = source_type or self._resolve_source_type_from_file_name(file_name)
        resolved_title = (title or "").strip() or Path(file_name).stem or "untitled"
        document = DocumentParser.parse_text(
            content=normalized_content,
            title=resolved_title,
            source_type=resolved_source_type,
            document_id=document_id,
            origin_uri=file_name,
            file_name=file_name,
            jurisdiction=jurisdiction,
            domain=domain,
            tags=tags or [],
            metadata=dict(metadata or {}),
        )
        with self._lock:
            self._documents[document.document_id] = document
            self._document_chunk_ids.setdefault(document.document_id, [])
        log_report(
            "console.knowledge.document.uploaded",
            {
                "document_id": document.document_id,
                "title": document.title,
                "source_type": document.source_type,
                "file_name": document.file_name,
            },
        )
        return document

    def create_build(
        self,
        *,
        version_id: str | None = None,
        force_rebuild_document_ids: list[str] | None = None,
        max_failure_ratio: float = 0.0,
        max_empty_chunk_ratio: float = 0.0,
    ) -> OfflineBuildResult:
        with self._lock:
            documents = [self._clone_document(document) for document in self._documents.values()]
            if not documents:
                raise ValueError("当前没有可构建的文档。请先上传文档。")
            resolved_version_id = (version_id or "").strip() or f"console-{_utc_version_suffix()}"
            result = self._pipeline.build_documents(
                documents=documents,
                version_id=resolved_version_id,
                previous_manifest=self._manifest,
                force_rebuild_document_ids=force_rebuild_document_ids or [],
                max_failure_ratio=max_failure_ratio,
                max_empty_chunk_ratio=max_empty_chunk_ratio,
            )
            self._manifest = result.manifest
            self._build_results[result.metadata.build_id] = result
            if result.metadata.build_id not in self._build_ids:
                self._build_ids.insert(0, result.metadata.build_id)
            self._sync_documents_and_chunks_from_build(result)
        return result

    def list_builds(self) -> list[OfflineBuildResult]:
        with self._lock:
            return [
                self._build_results[build_id]
                for build_id in self._build_ids
                if build_id in self._build_results
            ]

    def get_build(self, build_id: str) -> OfflineBuildResult | None:
        with self._lock:
            return self._build_results.get(build_id)

    def list_documents(self) -> list[dict[str, Any]]:
        with self._lock:
            items = []
            for document in self._documents.values():
                chunk_ids = self._document_chunk_ids.get(document.document_id, [])
                items.append(
                    {
                        "document_id": document.document_id,
                        "title": document.title,
                        "source_type": document.source_type,
                        "origin_uri": document.origin_uri,
                        "file_name": document.file_name,
                        "jurisdiction": document.jurisdiction,
                        "domain": document.domain,
                        "tags": list(document.tags),
                        "effective_at": document.effective_at,
                        "updated_at": document.updated_at,
                        "visibility": document.visibility,
                        "metadata": dict(document.metadata),
                        "chunk_count": len(chunk_ids),
                    }
                )
            return sorted(items, key=lambda item: item["updated_at"] or "", reverse=True)

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        with self._lock:
            document = self._documents.get(document_id)
            if document is None:
                return None
            chunk_ids = self._document_chunk_ids.get(document.document_id, [])
            return {
                "document_id": document.document_id,
                "title": document.title,
                "source_type": document.source_type,
                "content": document.content,
                "origin_uri": document.origin_uri,
                "file_name": document.file_name,
                "jurisdiction": document.jurisdiction,
                "domain": document.domain,
                "tags": list(document.tags),
                "effective_at": document.effective_at,
                "updated_at": document.updated_at,
                "visibility": document.visibility,
                "metadata": dict(document.metadata),
                "chunk_count": len(chunk_ids),
            }

    def list_document_chunks(self, document_id: str) -> list[dict[str, Any]] | None:
        with self._lock:
            if document_id not in self._documents:
                return None
            chunk_ids = self._document_chunk_ids.get(document_id, [])
            chunks = [self._chunks[chunk_id] for chunk_id in chunk_ids if chunk_id in self._chunks]
            return [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "embedding_model": chunk.embedding_model,
                    "chunk_text_preview": self._snippet(chunk.chunk_text, max_chars=220),
                    "metadata": dict(chunk.metadata),
                }
                for chunk in sorted(chunks, key=lambda item: item.chunk_index)
            ]

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        with self._lock:
            chunk = self._chunks.get(chunk_id)
            if chunk is None:
                return None
            return {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "embedding_model": chunk.embedding_model,
                "chunk_text": chunk.chunk_text,
                "metadata": dict(chunk.metadata),
            }

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

    def create_evaluation_run(
        self,
        *,
        dataset_id: str | None = None,
        version_id: str | None = None,
        samples: list[dict[str, Any]] | None = None,
        run_metadata: dict[str, Any] | None = None,
    ) -> EvaluationRunResult:
        dataset = self._build_dataset(
            dataset_id=dataset_id,
            version_id=version_id,
            samples=samples or [],
        )
        run_result = self._evaluation_runner.run(
            dataset,
            metadata=run_metadata or {"trigger": "internal_console"},
        )
        with self._lock:
            self._evaluation_runs[run_result.run_id] = run_result
            if run_result.run_id not in self._evaluation_run_ids:
                self._evaluation_run_ids.insert(0, run_result.run_id)
        return run_result

    def list_evaluation_runs(self) -> list[EvaluationRunResult]:
        with self._lock:
            return [
                self._evaluation_runs[run_id]
                for run_id in self._evaluation_run_ids
                if run_id in self._evaluation_runs
            ]

    def get_evaluation_run(self, run_id: str) -> EvaluationRunResult | None:
        with self._lock:
            return self._evaluation_runs.get(run_id)

    def get_runtime_summary(self) -> dict[str, Any]:
        rag_config = self._app_config.rag_config
        with self._lock:
            return {
                "service": "vi_ai_core_service",
                "default_provider": self._app_config.default_provider,
                "rag_enabled": rag_config.enabled,
                "embedding_provider": rag_config.embedding_provider,
                "embedding_model": rag_config.embedding_model,
                "retrieval_top_k": rag_config.retrieval_top_k,
                "score_threshold": rag_config.score_threshold,
                "chunk_token_size": rag_config.chunk_token_size,
                "chunk_overlap_token_size": rag_config.chunk_overlap_token_size,
                "document_count": len(self._documents),
                "chunk_count": len(self._chunks),
                "build_count": len(self._build_results),
                "evaluation_run_count": len(self._evaluation_runs),
            }

    def get_runtime_config_summary(self) -> dict[str, Any]:
        with self._lock:
            providers = {
                name: {
                    "default_model": config.default_model,
                    "base_url": config.base_url,
                    "timeout_seconds": config.timeout_seconds,
                    "api_key_configured": bool(config.api_key),
                }
                for name, config in self._app_config.providers.items()
            }
            return {
                "default_provider": self._app_config.default_provider,
                "providers": providers,
                "streaming": {
                    "enabled": self._app_config.streaming_config.streaming_enabled,
                    "heartbeat_interval_seconds": self._app_config.streaming_config.stream_heartbeat_interval_seconds,
                    "request_timeout_seconds": self._app_config.streaming_config.stream_request_timeout_seconds,
                    "emit_usage": self._app_config.streaming_config.stream_emit_usage,
                    "emit_trace": self._app_config.streaming_config.stream_emit_trace,
                    "cancel_enabled": self._app_config.streaming_config.stream_cancel_enabled,
                },
                "rag": {
                    "enabled": self._app_config.rag_config.enabled,
                    "qdrant_url": self._app_config.rag_config.qdrant_url,
                    "qdrant_collection": self._app_config.rag_config.qdrant_collection,
                    "embedding_provider": self._app_config.rag_config.embedding_provider,
                    "embedding_model": self._app_config.rag_config.embedding_model,
                    "retrieval_top_k": self._app_config.rag_config.retrieval_top_k,
                    "score_threshold": self._app_config.rag_config.score_threshold,
                },
            }

    def get_runtime_health(self) -> dict[str, Any]:
        summary = self.get_runtime_summary()
        return {
            "status": "ok",
            "service": summary["service"],
            "checked_at": now_utc_iso(),
            "summary": summary,
        }

    @staticmethod
    def _resolve_source_type_from_file_name(file_name: str) -> str:
        suffix = Path(file_name).suffix.lower()
        if suffix == ".md":
            return "markdown_file"
        if suffix == ".txt":
            return "text_file"
        return "raw_text"

    @staticmethod
    def _snippet(text: str, *, max_chars: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= max_chars:
            return normalized
        if max_chars <= 3:
            return normalized[:max_chars]
        return f"{normalized[: max_chars - 3]}..."

    @staticmethod
    def _clone_document(document: KnowledgeDocument) -> KnowledgeDocument:
        return KnowledgeDocument(
            document_id=document.document_id,
            title=document.title,
            source_type=document.source_type,
            content=document.content,
            origin_uri=document.origin_uri,
            file_name=document.file_name,
            jurisdiction=document.jurisdiction,
            domain=document.domain,
            tags=list(document.tags),
            effective_at=document.effective_at,
            updated_at=document.updated_at,
            visibility=document.visibility,
            metadata=dict(document.metadata),
        )

    def _sync_documents_and_chunks_from_build(self, build_result: OfflineBuildResult) -> None:
        for ingestion_result in build_result.ingestion_results:
            document = ingestion_result.document
            self._documents[document.document_id] = document
            old_chunk_ids = self._document_chunk_ids.get(document.document_id, [])
            for chunk_id in old_chunk_ids:
                self._chunks.pop(chunk_id, None)
            new_chunk_ids: list[str] = []
            for chunk in ingestion_result.chunks:
                self._chunks[chunk.chunk_id] = chunk
                new_chunk_ids.append(chunk.chunk_id)
            self._document_chunk_ids[document.document_id] = new_chunk_ids

    @staticmethod
    def _build_vector_store(*, app_config: AppConfig):
        rag_config = app_config.rag_config
        if not rag_config.enabled:
            return InMemoryVectorStore()
        return QdrantVectorStore(
            url=rag_config.qdrant_url,
            collection_name=rag_config.qdrant_collection,
            api_key=rag_config.qdrant_api_key,
        )

    def _build_dataset(
        self,
        *,
        dataset_id: str | None,
        version_id: str | None,
        samples: list[dict[str, Any]],
    ) -> EvaluationDataset:
        normalized_dataset_id = (dataset_id or "").strip() or "console-rag-dataset"
        normalized_version_id = (version_id or "").strip() or f"console-{_utc_version_suffix()}"
        if samples:
            dataset_samples = [self._sample_from_payload(index, sample) for index, sample in enumerate(samples)]
            return EvaluationDataset(
                dataset_id=normalized_dataset_id,
                version_id=normalized_version_id,
                samples=dataset_samples,
            )

        generated_samples = self._build_default_samples_from_documents()
        if not generated_samples:
            raise ValueError("未提供评估样本，且当前没有可用于自动生成样本的文档。")
        return EvaluationDataset(
            dataset_id=normalized_dataset_id,
            version_id=normalized_version_id,
            samples=generated_samples,
        )

    def _build_default_samples_from_documents(self) -> list[EvaluationSample]:
        with self._lock:
            documents = list(self._documents.values())
        samples: list[EvaluationSample] = []
        for index, document in enumerate(documents[:10], start=1):
            required_terms = [
                term.lower()
                for term in document.title.split()
                if term.strip()
            ][:3]
            samples.append(
                EvaluationSample(
                    sample_id=f"auto-{index}-{document.document_id}",
                    query_text=document.title,
                    retrieval_label=RetrievalLabel(
                        expected_document_ids=[document.document_id],
                        expected_chunk_ids=[],
                        min_recall=0.5,
                    ),
                    citation_label=CitationLabel(
                        expected_citation_ids=[],
                        expected_document_ids=[document.document_id],
                        min_recall=0.5,
                        min_precision=0.0,
                    ),
                    answer_label=AnswerLabel(
                        required_terms=required_terms,
                        forbidden_terms=[],
                        min_required_term_hit_ratio=0.0,
                        max_forbidden_term_hit_count=0,
                    ),
                    metadata={"auto_generated": True},
                )
            )
        return samples

    @staticmethod
    def _sample_from_payload(index: int, payload: dict[str, Any]) -> EvaluationSample:
        sample_id = str(payload.get("sample_id") or f"manual-{index + 1}")
        query_text = str(payload.get("query_text") or "").strip()
        if not query_text:
            raise ValueError("评估样本 query_text 不能为空。")
        return EvaluationSample(
            sample_id=sample_id,
            query_text=query_text,
            metadata_filter=dict(payload.get("metadata_filter") or {}),
            top_k=payload.get("top_k"),
            retrieval_label=RetrievalLabel(**dict(payload.get("retrieval_label") or {})),
            citation_label=CitationLabel(**dict(payload.get("citation_label") or {})),
            answer_label=AnswerLabel(**dict(payload.get("answer_label") or {})),
            metadata=dict(payload.get("metadata") or {}),
        )
