"""RAG 控制面持久化 ORM 模型。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import DBModelBase


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_AUTO_ID_TYPE = Integer().with_variant(BigInteger, "mysql")


class DocumentEntity(DBModelBase):
    """逻辑文档主表。"""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    origin_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    visibility: Mapped[str] = mapped_column(String(64), nullable=False, default="internal")
    tags_details: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    latest_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )


class DocumentVersionEntity(DBModelBase):
    """文档版本表。"""

    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    version_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    document_id: Mapped[str] = mapped_column(String(64), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    normalized_text_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    raw_file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    normalized_char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    parser_name: Mapped[str] = mapped_column(String(128), nullable=False)
    cleaner_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    __table_args__ = (
        Index("idx_document_versions_document_id", "document_id"),
    )


class BuildTaskEntity(DBModelBase):
    """离线构建任务表。"""

    __tablename__ = "build_tasks"

    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    build_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    build_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    chunk_strategy_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    embedding_model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    statistics_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    quality_gate_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )


class BuildDocumentEntity(DBModelBase):
    """构建任务与文档版本关系表。"""

    __tablename__ = "build_documents"

    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    build_id: Mapped[str] = mapped_column(String(64), nullable=False)
    document_id: Mapped[str] = mapped_column(String(64), nullable=False)
    document_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vector_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    __table_args__ = (
        Index("idx_build_documents_build_id", "build_id"),
        Index("idx_build_documents_document_id", "document_id"),
    )


class ChunkEntity(DBModelBase):
    """chunk 元数据表。"""

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    build_id: Mapped[str] = mapped_column(String(64), nullable=False)
    document_id: Mapped[str] = mapped_column(String(64), nullable=False)
    document_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_text_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    chunk_preview: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    vector_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_collection: Mapped[str] = mapped_column(String(128), nullable=False)
    vector_point_id: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    __table_args__ = (
        Index("idx_chunks_document_id", "document_id"),
        Index("idx_chunks_build_id", "build_id"),
        Index("idx_chunks_vector_point_id", "vector_point_id"),
    )


class EvaluationRunEntity(DBModelBase):
    """评测运行任务表。"""

    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    build_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dataset_version_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(128), nullable=False)
    summary_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    metadata_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )


class EvaluationCaseEntity(DBModelBase):
    """评测样本结果表。"""

    __tablename__ = "evaluation_cases"

    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sample_id: Mapped[str] = mapped_column(String(128), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_filter_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    top_k: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retrieval_label_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    citation_label_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    answer_label_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    retrieved_chunk_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    retrieved_document_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    generated_citation_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    generated_citation_document_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    case_result_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    __table_args__ = (
        Index("idx_evaluation_cases_run_id", "run_id"),
    )
