"""RAG 控制面持久化 ORM 模型。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import DBModelBase


def _utcnow() -> datetime:
    """返回当前 UTC 时间，用于 ORM 默认时间字段。"""
    return datetime.now(timezone.utc)


# 自增主键列类型：MySQL 使用 BIGINT，其它数据库使用 INTEGER。
_AUTO_ID_TYPE = Integer().with_variant(BigInteger, "mysql")


class DocumentEntity(DBModelBase):
    """逻辑文档主表。"""

    # 表名：逻辑文档主表。
    __tablename__ = "documents"

    # 自增主键，仅用于数据库内部关联。
    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    # 逻辑文档唯一标识（业务 ID）。
    document_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # 文档标题。
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # 文档来源类型（如 markdown_file / pdf_file）。
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # 文档来源 URI，可为空。
    origin_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 原始文件名，可为空。
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 法域标识，可为空。
    jurisdiction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 业务域标识，可为空。
    domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 可见性范围（默认 internal）。
    visibility: Mapped[str] = mapped_column(String(64), nullable=False, default="internal")
    # 文档标签详情列表（半结构化字段）。
    tags_details: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # 文档状态（默认 active）。
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    # 最新版本业务 ID，可为空。
    latest_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 记录创建时间（UTC）。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    # 记录更新时间（UTC，更新时自动刷新）。
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )


class DocumentVersionEntity(DBModelBase):
    """文档版本表。"""

    # 表名：文档版本表。
    __tablename__ = "document_versions"

    # 自增主键，仅用于数据库内部关联。
    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    # 文档版本唯一标识（业务 ID）。
    version_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # 所属逻辑文档业务 ID。
    document_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 文档版本号（从 1 开始递增）。
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # 原始内容哈希值。
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # 清洗后文本哈希值。
    normalized_text_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # 哈希算法名称（如 sha1）。
    hash_algorithm: Mapped[str] = mapped_column(String(32), nullable=False)
    # 原始文件存储路径。
    raw_storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    # 规范化文本存储路径。
    normalized_storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    # 原始文件大小（字节）。
    raw_file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # 规范化文本字符数。
    normalized_char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # 解析器名称。
    parser_name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 清洗器名称。
    cleaner_name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 版本元数据详情（半结构化字段）。
    metadata_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 记录创建时间（UTC）。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    # 表级索引：按 document_id 查询版本列表。
    __table_args__ = (
        Index("idx_document_versions_document_id", "document_id"),
    )


class BuildTaskEntity(DBModelBase):
    """离线构建任务表。"""

    # 表名：离线构建任务表。
    __tablename__ = "build_tasks"

    # 自增主键，仅用于数据库内部关联。
    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    # 构建任务唯一标识（业务 ID）。
    build_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # 构建版本标识（用于区分批次策略版本）。
    build_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    # 构建任务状态（running/succeeded/failed）。
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    # 分块策略名称。
    chunk_strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 分块策略详情（半结构化字段）。
    chunk_strategy_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # embedding 模型名称。
    embedding_model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 构建输入快照详情（半结构化字段）。
    manifest_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 构建统计信息（半结构化字段）。
    statistics_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 质量门禁信息（半结构化字段）。
    quality_gate_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 失败或异常信息，可为空。
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 任务开始时间（UTC），可为空。
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 任务完成时间（UTC），可为空。
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 记录创建时间（UTC）。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )


class BuildDocumentEntity(DBModelBase):
    """构建任务与文档版本关系表。"""

    # 表名：构建任务与文档版本关系表。
    __tablename__ = "build_documents"

    # 自增主键，仅用于数据库内部关联。
    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    # 所属构建任务业务 ID。
    build_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 文档业务 ID。
    document_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 文档版本业务 ID。
    document_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 文档内容哈希值。
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # 本次构建动作（如 upsert/failed）。
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    # 该文档产出的 chunk 数量。
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 该文档写入向量数量。
    vector_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 处理错误信息，可为空。
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 记录创建时间（UTC）。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    # 表级索引：按 build_id / document_id 查询构建明细。
    __table_args__ = (
        Index("idx_build_documents_build_id", "build_id"),
        Index("idx_build_documents_document_id", "document_id"),
    )


class ChunkEntity(DBModelBase):
    """chunk 元数据表。"""

    # 表名：chunk 元数据表。
    __tablename__ = "chunks"

    # 自增主键，仅用于数据库内部关联。
    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    # chunk 唯一标识（业务 ID，通常与向量点 ID 对齐）。
    chunk_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # 所属构建任务业务 ID。
    build_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 所属文档业务 ID。
    document_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 所属文档版本业务 ID。
    document_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # chunk 序号。
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # chunk token 数量。
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # chunk 起始偏移量，可为空。
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # chunk 结束偏移量，可为空。
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # chunk 文本哈希值。
    chunk_text_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # chunk 文本预览。
    chunk_preview: Mapped[str] = mapped_column(Text, nullable=False)
    # embedding 模型名称。
    embedding_model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 向量维度。
    vector_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    # 向量集合名称。
    vector_collection: Mapped[str] = mapped_column(String(128), nullable=False)
    # 向量点 ID（用于回读 Qdrant 详情）。
    vector_point_id: Mapped[str] = mapped_column(String(128), nullable=False)
    # chunk 元数据详情（半结构化字段）。
    metadata_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 记录创建时间（UTC）。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    # 表级索引：按文档/构建/向量点查询 chunk。
    __table_args__ = (
        Index("idx_chunks_document_id", "document_id"),
        Index("idx_chunks_build_id", "build_id"),
        Index("idx_chunks_vector_point_id", "vector_point_id"),
    )


class EvaluationRunEntity(DBModelBase):
    """评测运行任务表。"""

    # 表名：评测运行任务表。
    __tablename__ = "evaluation_runs"

    # 自增主键，仅用于数据库内部关联。
    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    # 评测运行唯一标识（业务 ID）。
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # 关联构建任务业务 ID，可为空。
    build_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 数据集业务 ID，可为空（本阶段允许无数据集资产）。
    dataset_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 数据集版本业务 ID，可为空。
    dataset_version_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 评测运行状态（running/succeeded/failed）。
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    # 触发类型（manual/api 等）。
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # 触发来源（如 internal_console）。
    triggered_by: Mapped[str] = mapped_column(String(128), nullable=False)
    # 评测汇总详情（半结构化字段）。
    summary_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 评测元数据详情（半结构化字段）。
    metadata_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 失败或异常信息，可为空。
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 运行开始时间（UTC），可为空。
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 运行完成时间（UTC），可为空。
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 记录创建时间（UTC）。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )


class EvaluationCaseEntity(DBModelBase):
    """评测样本结果表。"""

    # 表名：评测样本结果表。
    __tablename__ = "evaluation_cases"

    # 自增主键，仅用于数据库内部关联。
    id: Mapped[int] = mapped_column(_AUTO_ID_TYPE, primary_key=True, autoincrement=True)
    # case 唯一标识（业务 ID）。
    case_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # 所属运行业务 ID。
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 样本业务 ID。
    sample_id: Mapped[str] = mapped_column(String(128), nullable=False)
    # 样本查询文本。
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    # 元数据过滤详情（半结构化字段）。
    metadata_filter_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 检索 top-k，可为空。
    top_k: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 检索标签详情（半结构化字段）。
    retrieval_label_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 引用标签详情（半结构化字段）。
    citation_label_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 回答标签详情（半结构化字段）。
    answer_label_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # 检索命中的 chunk ID 列表。
    retrieved_chunk_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # 检索命中的文档 ID 列表。
    retrieved_document_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    # 生成的引用 ID 列表。
    generated_citation_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    # 生成的引用文档 ID 列表。
    generated_citation_document_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    # 生成的回答文本。
    answer_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # case 结果详情（半结构化字段）。
    case_result_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    # case 是否通过。
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # case 错误信息，可为空。
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 记录创建时间（UTC）。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    # 表级索引：按 run_id 查询 case 列表。
    __table_args__ = (
        Index("idx_evaluation_cases_run_id", "run_id"),
    )
