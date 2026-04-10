"""Core models for Knowledge + Citation layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    normalized = []
    for tag in tags:
        stripped = str(tag).strip()
        if stripped:
            normalized.append(stripped)
    return normalized


@dataclass
class KnowledgeDocument:
    document_id: str
    title: str
    source_type: str
    content: str
    origin_uri: str | None = None
    file_name: str | None = None
    jurisdiction: str | None = None
    domain: str | None = None
    tags: list[str] = field(default_factory=list)
    effective_at: str | None = None
    updated_at: str | None = None
    visibility: str = "internal"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.document_id = _normalize_optional_text(self.document_id) or f"doc_{uuid4().hex}"
        self.title = _normalize_optional_text(self.title) or self.document_id
        self.source_type = _normalize_optional_text(self.source_type) or "text"
        self.content = self.content.strip()
        self.origin_uri = _normalize_optional_text(self.origin_uri)
        self.file_name = _normalize_optional_text(self.file_name)
        self.jurisdiction = _normalize_optional_text(self.jurisdiction)
        self.domain = _normalize_optional_text(self.domain)
        self.tags = _normalize_tags(self.tags)
        self.effective_at = _normalize_optional_text(self.effective_at)
        self.updated_at = _normalize_optional_text(self.updated_at) or now_utc_iso()
        self.visibility = _normalize_optional_text(self.visibility) or "internal"
        self.metadata = dict(self.metadata or {})
        if not self.content:
            raise ValueError("KnowledgeDocument.content cannot be empty.")


@dataclass
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    chunk_text: str
    chunk_index: int
    token_count: int
    embedding_model: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.chunk_id = _normalize_optional_text(self.chunk_id) or f"chk_{uuid4().hex}"
        self.document_id = _normalize_optional_text(self.document_id) or ""
        self.chunk_text = self.chunk_text.strip()
        if not self.chunk_text:
            raise ValueError("KnowledgeChunk.chunk_text cannot be empty.")
        if self.chunk_index < 0:
            raise ValueError("KnowledgeChunk.chunk_index must be >= 0.")
        if self.token_count < 0:
            raise ValueError("KnowledgeChunk.token_count must be >= 0.")
        self.embedding_model = _normalize_optional_text(self.embedding_model) or "unknown"
        self.metadata = dict(self.metadata or {})


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    score: float
    title: str | None
    origin_uri: str | None
    source_type: str | None
    jurisdiction: str | None
    domain: str | None
    effective_at: str | None
    updated_at: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.chunk_id = _normalize_optional_text(self.chunk_id) or ""
        self.document_id = _normalize_optional_text(self.document_id) or ""
        self.text = self.text.strip()
        self.title = _normalize_optional_text(self.title)
        self.origin_uri = _normalize_optional_text(self.origin_uri)
        self.source_type = _normalize_optional_text(self.source_type)
        self.jurisdiction = _normalize_optional_text(self.jurisdiction)
        self.domain = _normalize_optional_text(self.domain)
        self.effective_at = _normalize_optional_text(self.effective_at)
        self.updated_at = _normalize_optional_text(self.updated_at)
        self.metadata = dict(self.metadata or {})


@dataclass
class Citation:
    citation_id: str
    document_id: str
    chunk_id: str
    title: str | None
    snippet: str
    origin_uri: str | None
    source_type: str | None
    updated_at: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalTrace:
    status: str
    query_text: str
    top_k: int
    metadata_filter: dict[str, Any] = field(default_factory=dict)
    hit_count: int = 0
    citation_count: int = 0
    latency_ms: float = 0.0
    error_type: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalResult:
    knowledge_block: str | None
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    trace: RetrievalTrace = field(
        default_factory=lambda: RetrievalTrace(
            status="disabled",
            query_text="",
            top_k=0,
        )
    )

    @classmethod
    def disabled(
        cls,
        *,
        query_text: str,
        top_k: int,
        metadata_filter: dict[str, Any] | None = None,
    ) -> "RetrievalResult":
        return cls(
            knowledge_block=None,
            retrieved_chunks=[],
            citations=[],
            trace=RetrievalTrace(
                status="disabled",
                query_text=query_text,
                top_k=top_k,
                metadata_filter=dict(metadata_filter or {}),
            ),
        )

    @classmethod
    def degraded(
        cls,
        *,
        query_text: str,
        top_k: int,
        metadata_filter: dict[str, Any] | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        latency_ms: float = 0.0,
    ) -> "RetrievalResult":
        return cls(
            knowledge_block=None,
            retrieved_chunks=[],
            citations=[],
            trace=RetrievalTrace(
                status="degraded",
                query_text=query_text,
                top_k=top_k,
                metadata_filter=dict(metadata_filter or {}),
                hit_count=0,
                citation_count=0,
                latency_ms=latency_ms,
                error_type=error_type,
                error_message=error_message,
            ),
        )


@dataclass
class IngestionTrace:
    status: str
    document_count: int
    chunk_count: int
    embedding_batch_count: int
    embedding_dimension: int
    upserted_count: int
    latency_ms: float
    error_type: str | None = None
    error_message: str | None = None


@dataclass
class IngestionResult:
    document: KnowledgeDocument
    chunks: list[KnowledgeChunk]
    trace: IngestionTrace
