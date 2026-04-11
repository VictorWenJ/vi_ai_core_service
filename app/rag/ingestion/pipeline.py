"""Minimal ingestion pipeline: parser -> cleaner -> chunker -> embedding -> index."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from app.observability.log_until import log_report
from app.providers.embedding_base import BaseEmbeddingProvider
from app.rag.ingestion.chunker import StructuredTokenChunker
from app.rag.ingestion.cleaner import DocumentCleaner
from app.rag.ingestion.parser import DocumentParser
from app.rag.models import IngestionResult, IngestionTrace
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

    def ingest_text(self, *, content: str, **document_kwargs) -> IngestionResult:
        document = self._parser.parse_text(content=content, **document_kwargs)
        return self.ingest_document(document)

    def ingest_file(self, file_path: str | Path, **document_kwargs) -> IngestionResult:
        document = self._parser.parse_file(file_path, **document_kwargs)
        return self.ingest_document(document)

    def ingest_document(self, document):
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
