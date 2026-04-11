"""Minimal ingestion pipeline: parser -> cleaner -> chunker -> embedding -> index."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Iterable

from app.observability.log_until import log_report
from app.providers.embeddings.base import BaseEmbeddingProvider
from app.rag.ingestion.chunker import StructuredTokenChunker
from app.rag.ingestion.cleaner import DocumentCleaner
from app.rag.ingestion.parser import DocumentParser
from app.rag.models import (
    IngestionResult,
    IngestionTrace,
    KnowledgeDocument,
    OfflineBuildDocumentRecord,
    OfflineBuildManifest,
    OfflineBuildMetadata,
    OfflineBuildQualityGate,
    OfflineBuildResult,
    OfflineBuildStatistics,
    compute_content_hash,
    now_utc_iso,
)
from app.rag.retrieval.vector_store import BaseVectorStore


class KnowledgeIngestionPipeline:
    """Ingest documents into vector index with deterministic steps."""

    def __init__(
        self,
        *,
        parser: DocumentParser,
        cleaner: DocumentCleaner,
        chunker: StructuredTokenChunker,
        embedding_provider: BaseEmbeddingProvider,
        vector_store: BaseVectorStore,
        embedding_model: str,
        chunk_token_size: int,
        overlap_token_size: int,
        embedding_batch_size: int = 16,
        chunk_strategy_version: str = "structure-token-overlap-v1",
        embedding_model_version: str | None = None,
    ) -> None:
        self._parser = parser
        self._cleaner = cleaner
        self._chunker = chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._embedding_model = embedding_model
        self._chunk_token_size = chunk_token_size
        self._overlap_token_size = overlap_token_size
        self._embedding_batch_size = embedding_batch_size
        self._chunk_strategy_version = chunk_strategy_version
        self._embedding_model_version = embedding_model_version or embedding_model

    def ingest_text(self, *, content: str, **document_kwargs) -> IngestionResult:
        document = self._parser.parse_text(content=content, **document_kwargs)
        return self.ingest_document(document)

    def ingest_file(self, file_path: str | Path, **document_kwargs) -> IngestionResult:
        document = self._parser.parse_file(file_path, **document_kwargs)
        return self.ingest_document(document)

    def ingest_document(
        self,
        document: KnowledgeDocument,
        *,
        build_metadata: dict[str, str] | None = None,
    ) -> IngestionResult:
        started_at = perf_counter()
        log_report("KnowledgeIngestionPipeline.ingest_document.document", document)

        # 数据清洗
        cleaned_content = self._cleaner.clean(document.content)
        log_report("KnowledgeIngestionPipeline.ingest_document.cleaned_content", cleaned_content)

        # 数据分块
        document.content = cleaned_content
        chunks = self._chunker.chunk_document(
            document,
            chunk_token_size=self._chunk_token_size,
            overlap_token_size=self._overlap_token_size,
            embedding_model=self._embedding_model,
        )
        if build_metadata:
            for chunk in chunks:
                chunk.metadata.update(build_metadata)
        log_report("KnowledgeIngestionPipeline.ingest_document.chunks", chunks)

        vectors: list[list[float]] = []
        embedding_batch_count = 0
        embedding_dimension = 0
        for offset in range(0, len(chunks), self._embedding_batch_size):
            batch = chunks[offset: offset + self._embedding_batch_size]
            batch_texts = [chunk.chunk_text for chunk in batch]
            embedding_result = self._embedding_provider.embed_texts(
                batch_texts,
                model=self._embedding_model,
            )
            embedding_batch_count += 1
            embedding_dimension = embedding_result.dimensions
            vectors.extend(embedding_result.vectors)

        upserted_count = self._vector_store.upsert(
            document=document,
            chunks=chunks,
            vectors=vectors,
        )

        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        trace = IngestionTrace(
            status="succeeded",
            document_count=1,
            chunk_count=len(chunks),
            embedding_batch_count=embedding_batch_count,
            embedding_dimension=embedding_dimension,
            upserted_count=upserted_count,
            latency_ms=latency_ms,
        )
        log_report(
            "KnowledgeIngestionPipeline.ingest_document.completed_data",
            {
                "document_id": document.document_id,
                "document_count": trace.document_count,
                "chunk_count": trace.chunk_count,
                "embedding_batch_count": trace.embedding_batch_count,
                "embedding_dimension": trace.embedding_dimension,
                "upserted_count": trace.upserted_count,
                "latency_ms": trace.latency_ms,
            },
        )
        return IngestionResult(document=document, chunks=chunks, trace=trace)

    def build_documents(
        self,
        *,
        documents: Iterable[KnowledgeDocument],
        version_id: str,
        previous_manifest: OfflineBuildManifest | None = None,
        force_rebuild_document_ids: Iterable[str] | None = None,
        max_failure_ratio: float = 0.0,
        max_empty_chunk_ratio: float = 0.0,
    ) -> OfflineBuildResult:
        started_at = perf_counter()
        started_at_iso = now_utc_iso()
        forced_document_ids = {
            str(document_id).strip()
            for document_id in list(force_rebuild_document_ids or [])
            if str(document_id).strip()
        }
        build_mode = self._resolve_build_mode(
            previous_manifest=previous_manifest,
            forced_document_ids=forced_document_ids,
        )
        metadata = OfflineBuildMetadata(
            build_id="",
            version_id=version_id,
            chunk_strategy_version=self._chunk_strategy_version,
            embedding_model_version=self._embedding_model_version,
            build_mode=build_mode,
            started_at=started_at_iso,
            completed_at=started_at_iso,
        )
        build_metadata = {
            "build_id": metadata.build_id,
            "version_id": metadata.version_id,
            "chunk_strategy_version": metadata.chunk_strategy_version,
            "embedding_model_version": metadata.embedding_model_version,
        }
        log_report(
            "rag.offline_build.started",
            {
                "build_id": metadata.build_id,
                "version_id": metadata.version_id,
                "build_mode": metadata.build_mode,
                "chunk_strategy_version": metadata.chunk_strategy_version,
                "embedding_model_version": metadata.embedding_model_version,
            },
        )

        requested_document_count = 0
        processed_document_count = 0
        skipped_document_count = 0
        failed_document_count = 0
        chunk_count = 0
        upserted_count = 0
        embedding_batch_count = 0
        empty_chunk_document_count = 0
        ingestion_results: list[IngestionResult] = []
        next_manifest_records: dict[str, OfflineBuildDocumentRecord] = {}

        for document in list(documents):
            requested_document_count += 1
            current_content_hash = self._compute_document_content_hash(document)
            if self._should_skip_document(
                document=document,
                content_hash=current_content_hash,
                previous_manifest=previous_manifest,
                forced_document_ids=forced_document_ids,
            ):
                skipped_document_count += 1
                previous_record = (
                    previous_manifest.records.get(document.document_id)
                    if previous_manifest is not None
                    else None
                )
                if previous_record is not None:
                    next_manifest_records[document.document_id] = previous_record
                else:
                    next_manifest_records[document.document_id] = OfflineBuildDocumentRecord(
                        document_id=document.document_id,
                        content_hash=current_content_hash,
                        built_at=now_utc_iso(),
                    )
                continue

            try:
                ingestion_result = self.ingest_document(
                    document,
                    build_metadata=build_metadata,
                )
                ingestion_results.append(ingestion_result)
                processed_document_count += 1
                chunk_count += ingestion_result.trace.chunk_count
                upserted_count += ingestion_result.trace.upserted_count
                embedding_batch_count += ingestion_result.trace.embedding_batch_count
                if ingestion_result.trace.chunk_count == 0:
                    empty_chunk_document_count += 1
                next_manifest_records[document.document_id] = OfflineBuildDocumentRecord(
                    document_id=document.document_id,
                    content_hash=self._compute_document_content_hash(ingestion_result.document),
                    built_at=now_utc_iso(),
                )
                log_report(
                    "rag.offline_build.document.succeeded",
                    {
                        "build_id": metadata.build_id,
                        "version_id": metadata.version_id,
                        "document_id": document.document_id,
                        "chunk_count": ingestion_result.trace.chunk_count,
                        "upserted_count": ingestion_result.trace.upserted_count,
                    },
                )
            except Exception as exc:
                failed_document_count += 1
                log_report(
                    "rag.offline_build.document.failed",
                    {
                        "build_id": metadata.build_id,
                        "version_id": metadata.version_id,
                        "document_id": document.document_id,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                )

        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        statistics = OfflineBuildStatistics(
            requested_document_count=requested_document_count,
            processed_document_count=processed_document_count,
            skipped_document_count=skipped_document_count,
            failed_document_count=failed_document_count,
            chunk_count=chunk_count,
            upserted_count=upserted_count,
            embedding_batch_count=embedding_batch_count,
            latency_ms=latency_ms,
        )
        quality_gate = self._evaluate_quality_gate(
            statistics=statistics,
            empty_chunk_document_count=empty_chunk_document_count,
            max_failure_ratio=max_failure_ratio,
            max_empty_chunk_ratio=max_empty_chunk_ratio,
        )
        if not quality_gate.passed:
            log_report(
                "rag.offline_build.quality_gate.failed",
                {
                    "build_id": metadata.build_id,
                    "version_id": metadata.version_id,
                    "failed_rules": quality_gate.failed_rules,
                    "failure_ratio": quality_gate.failure_ratio,
                    "empty_chunk_ratio": quality_gate.empty_chunk_ratio,
                },
            )
        manifest = OfflineBuildManifest(
            version_id=version_id,
            records=next_manifest_records,
            generated_at=now_utc_iso(),
        )
        metadata.completed_at = now_utc_iso()
        build_result = OfflineBuildResult(
            metadata=metadata,
            statistics=statistics,
            quality_gate=quality_gate,
            manifest=manifest,
            ingestion_results=ingestion_results,
        )
        log_report("rag.offline_build.completed", build_result.to_dict())
        return build_result

    @staticmethod
    def _resolve_build_mode(
        *,
        previous_manifest: OfflineBuildManifest | None,
        forced_document_ids: set[str],
    ) -> str:
        if previous_manifest is None:
            return "full"
        if forced_document_ids:
            return "partial"
        return "incremental"

    def _compute_document_content_hash(self, document: KnowledgeDocument) -> str:
        normalized_content = self._cleaner.clean(document.content)
        return compute_content_hash(normalized_content)

    def _should_skip_document(
        self,
        *,
        document: KnowledgeDocument,
        content_hash: str,
        previous_manifest: OfflineBuildManifest | None,
        forced_document_ids: set[str],
    ) -> bool:
        if previous_manifest is None:
            return False
        if document.document_id in forced_document_ids:
            return False
        previous_record = previous_manifest.records.get(document.document_id)
        if previous_record is None:
            return False
        return previous_record.content_hash == content_hash

    @staticmethod
    def _evaluate_quality_gate(
        *,
        statistics: OfflineBuildStatistics,
        empty_chunk_document_count: int,
        max_failure_ratio: float,
        max_empty_chunk_ratio: float,
    ) -> OfflineBuildQualityGate:
        requested_count = max(statistics.requested_document_count, 1)
        processed_count = max(statistics.processed_document_count, 1)
        failure_ratio = statistics.failed_document_count / requested_count
        empty_chunk_ratio = empty_chunk_document_count / processed_count
        failed_rules: list[str] = []
        if failure_ratio > max_failure_ratio:
            failed_rules.append("failure_ratio_exceeded")
        if empty_chunk_ratio > max_empty_chunk_ratio:
            failed_rules.append("empty_chunk_ratio_exceeded")
        if statistics.chunk_count != statistics.upserted_count:
            failed_rules.append("upserted_count_mismatch")
        return OfflineBuildQualityGate(
            passed=not failed_rules,
            failed_rules=failed_rules,
            failure_ratio=failure_ratio,
            empty_chunk_ratio=empty_chunk_ratio,
            max_failure_ratio=max_failure_ratio,
            max_empty_chunk_ratio=max_empty_chunk_ratio,
        )
