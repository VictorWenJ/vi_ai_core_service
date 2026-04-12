"""Control-plane API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.api.schemas.chat import ChatCitation


class KnowledgeDocumentUploadResponse(BaseModel):
    document_id: str
    title: str
    source_type: str
    file_name: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BuildCreateRequest(BaseModel):
    version_id: str | None = None
    force_rebuild_document_ids: list[str] = Field(default_factory=list)
    max_failure_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    max_empty_chunk_ratio: float = Field(default=0.0, ge=0.0, le=1.0)


class BuildMetadataResponse(BaseModel):
    build_id: str
    version_id: str
    chunk_strategy_version: str
    embedding_model_version: str
    build_mode: str
    started_at: str
    completed_at: str


class BuildStatisticsResponse(BaseModel):
    requested_document_count: int
    processed_document_count: int
    skipped_document_count: int
    failed_document_count: int
    chunk_count: int
    upserted_count: int
    embedding_batch_count: int
    latency_ms: float


class BuildQualityGateResponse(BaseModel):
    passed: bool
    failed_rules: list[str] = Field(default_factory=list)
    failure_ratio: float
    empty_chunk_ratio: float
    max_failure_ratio: float
    max_empty_chunk_ratio: float


class BuildSummaryResponse(BaseModel):
    metadata: BuildMetadataResponse
    statistics: BuildStatisticsResponse
    quality_gate: BuildQualityGateResponse


class BuildDetailResponse(BuildSummaryResponse):
    manifest: dict[str, Any]
    ingestion_results: list[dict[str, Any]] = Field(default_factory=list)


class KnowledgeDocumentSummaryResponse(BaseModel):
    document_id: str
    title: str
    source_type: str
    origin_uri: str | None = None
    file_name: str | None = None
    jurisdiction: str | None = None
    domain: str | None = None
    tags: list[str] = Field(default_factory=list)
    effective_at: str | None = None
    updated_at: str | None = None
    visibility: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_count: int = 0


class KnowledgeDocumentDetailResponse(KnowledgeDocumentSummaryResponse):
    content: str


class KnowledgeChunkSummaryResponse(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    token_count: int
    embedding_model: str
    chunk_text_preview: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeChunkDetailResponse(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    token_count: int
    embedding_model: str
    chunk_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalDebugRequest(BaseModel):
    query_text: str = Field(min_length=1)
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    top_k: int | None = Field(default=None, gt=0)


class RetrievalDebugHitResponse(BaseModel):
    chunk_id: str
    document_id: str
    score: float
    title: str | None = None
    source_type: str | None = None
    origin_uri: str | None = None
    snippet: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalDebugResponse(BaseModel):
    query_text: str
    top_k: int
    status: str
    hits: list[RetrievalDebugHitResponse] = Field(default_factory=list)
    citations: list[ChatCitation] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)


class EvaluationRetrievalLabelPayload(BaseModel):
    expected_document_ids: list[str] = Field(default_factory=list)
    expected_chunk_ids: list[str] = Field(default_factory=list)
    min_recall: float = Field(default=1.0, ge=0.0, le=1.0)


class EvaluationCitationLabelPayload(BaseModel):
    expected_citation_ids: list[str] = Field(default_factory=list)
    expected_document_ids: list[str] = Field(default_factory=list)
    min_recall: float = Field(default=1.0, ge=0.0, le=1.0)
    min_precision: float = Field(default=0.0, ge=0.0, le=1.0)


class EvaluationAnswerLabelPayload(BaseModel):
    required_terms: list[str] = Field(default_factory=list)
    forbidden_terms: list[str] = Field(default_factory=list)
    min_required_term_hit_ratio: float = Field(default=1.0, ge=0.0, le=1.0)
    max_forbidden_term_hit_count: int = Field(default=0, ge=0)


class EvaluationSamplePayload(BaseModel):
    sample_id: str | None = None
    query_text: str = Field(min_length=1)
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    top_k: int | None = Field(default=None, gt=0)
    retrieval_label: EvaluationRetrievalLabelPayload = Field(
        default_factory=EvaluationRetrievalLabelPayload
    )
    citation_label: EvaluationCitationLabelPayload = Field(
        default_factory=EvaluationCitationLabelPayload
    )
    answer_label: EvaluationAnswerLabelPayload = Field(
        default_factory=EvaluationAnswerLabelPayload
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationRunCreateRequest(BaseModel):
    dataset_id: str | None = None
    version_id: str | None = None
    samples: list[EvaluationSamplePayload] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationRunSummaryResponse(BaseModel):
    run_id: str
    dataset_id: str
    dataset_version_id: str
    started_at: str
    completed_at: str
    summary: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    case_count: int


class EvaluationRunCaseResponse(BaseModel):
    sample_id: str
    retrieval: dict[str, Any]
    citation: dict[str, Any]
    answer: dict[str, Any]
    retrieval_status: str
    passed: bool
    resolved_top_k: int


class EvaluationRunDetailResponse(EvaluationRunSummaryResponse):
    pass


class RuntimeSummaryResponse(BaseModel):
    service: str
    default_provider: str
    rag_enabled: bool
    embedding_provider: str
    embedding_model: str
    retrieval_top_k: int
    score_threshold: float | None = None
    chunk_token_size: int
    chunk_overlap_token_size: int
    document_count: int
    chunk_count: int
    build_count: int
    evaluation_run_count: int


class RuntimeConfigSummaryResponse(BaseModel):
    default_provider: str
    providers: dict[str, Any]
    streaming: dict[str, Any]
    rag: dict[str, Any]


class RuntimeHealthResponse(BaseModel):
    status: str
    service: str
    checked_at: str
    summary: RuntimeSummaryResponse
