"""Repository 层对外读模型定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentRecord:
    # 逻辑文档唯一标识。
    document_id: str
    # 文档标题。
    title: str
    # 文档来源类型。
    source_type: str
    # 文档来源 URI。
    origin_uri: str | None
    # 原始文件名。
    file_name: str | None
    # 法域标签。
    jurisdiction: str | None
    # 业务域标签。
    domain: str | None
    # 可见性范围。
    visibility: str
    # 文档标签详情列表。
    tags_details: list[str] = field(default_factory=list)
    # 文档状态。
    status: str = "active"
    # 最新版本标识。
    latest_version_id: str | None = None
    # 文档创建时间（UTC ISO 字符串）。
    created_at: str | None = None
    # 文档更新时间（UTC ISO 字符串）。
    updated_at: str | None = None


@dataclass(frozen=True)
class DocumentVersionRecord:
    # 版本唯一标识。
    version_id: str
    # 所属文档标识。
    document_id: str
    # 文档版本号（从 1 开始递增）。
    version_no: int
    # 原始内容哈希。
    content_hash: str
    # 规范化文本哈希。
    normalized_text_hash: str
    # 哈希算法名称。
    hash_algorithm: str
    # 原始文件存储路径。
    raw_storage_path: str
    # 规范化文本存储路径。
    normalized_storage_path: str
    # 原始文件大小（字节）。
    raw_file_size: int
    # 规范化文本字符数。
    normalized_char_count: int
    # 解析器名称。
    parser_name: str
    # 清洗器名称。
    cleaner_name: str
    # 版本元数据详情。
    metadata_details: dict[str, Any] = field(default_factory=dict)
    # 版本创建时间（UTC ISO 字符串）。
    created_at: str | None = None


@dataclass(frozen=True)
class LatestDocumentVersionRecord:
    # 文档主记录。
    document: DocumentRecord
    # 对应最新版本记录。
    version: DocumentVersionRecord


@dataclass(frozen=True)
class BuildTaskRecord:
    # 构建任务唯一标识。
    build_id: str
    # 构建版本标识。
    build_version_id: str
    # 构建任务状态。
    status: str
    # 分块策略名称。
    chunk_strategy_name: str
    # 分块策略详情。
    chunk_strategy_details: dict[str, Any] = field(default_factory=dict)
    # 向量模型名称。
    embedding_model_name: str = ""
    # 构建输入快照详情。
    manifest_details: dict[str, Any] = field(default_factory=dict)
    # 构建统计详情。
    statistics_details: dict[str, Any] = field(default_factory=dict)
    # 质量门禁详情。
    quality_gate_details: dict[str, Any] = field(default_factory=dict)
    # 错误信息。
    error_message: str | None = None
    # 构建开始时间（UTC ISO 字符串）。
    started_at: str | None = None
    # 构建完成时间（UTC ISO 字符串）。
    completed_at: str | None = None
    # 任务创建时间（UTC ISO 字符串）。
    created_at: str | None = None


@dataclass(frozen=True)
class BuildTaskStatusSummary:
    # 构建任务唯一标识。
    build_id: str
    # 构建任务状态。
    status: str
    # 任务创建时间（UTC ISO 字符串）。
    created_at: str | None = None
    # 任务完成时间（UTC ISO 字符串）。
    completed_at: str | None = None


@dataclass(frozen=True)
class BuildDocumentRecord:
    # 所属构建任务标识。
    build_id: str
    # 文档标识。
    document_id: str
    # 文档版本标识。
    document_version_id: str
    # 文档内容哈希。
    content_hash: str
    # 本次动作类型（如 upsert/failed）。
    action: str
    # 产出 chunk 数。
    chunk_count: int = 0
    # 写入向量数。
    vector_count: int = 0
    # 错误信息。
    error_message: str | None = None
    # 记录创建时间（UTC ISO 字符串）。
    created_at: str | None = None


@dataclass(frozen=True)
class ChunkRecord:
    # chunk 唯一标识。
    chunk_id: str
    # 所属构建任务标识。
    build_id: str
    # 所属文档标识。
    document_id: str
    # 所属文档版本标识。
    document_version_id: str
    # chunk 序号。
    chunk_index: int
    # token 数量。
    token_count: int
    # 起始偏移量。
    start_offset: int | None = None
    # 结束偏移量。
    end_offset: int | None = None
    # chunk 文本哈希。
    chunk_text_hash: str = ""
    # chunk 预览文本。
    chunk_preview: str = ""
    # 向量模型名称。
    embedding_model_name: str = ""
    # 向量维度。
    vector_dimension: int = 0
    # 向量集合名称。
    vector_collection: str = ""
    # 向量点 ID。
    vector_point_id: str = ""
    # chunk 元数据详情。
    metadata_details: dict[str, Any] = field(default_factory=dict)
    # 记录创建时间（UTC ISO 字符串）。
    created_at: str | None = None


@dataclass(frozen=True)
class EvaluationRunRecord:
    # 评测运行标识。
    run_id: str
    # 关联构建任务标识。
    build_id: str | None
    # 数据集标识，可为空。
    dataset_id: str | None
    # 数据集版本标识，可为空。
    dataset_version_id: str | None
    # 运行状态。
    status: str
    # 触发类型。
    trigger_type: str
    # 触发来源。
    triggered_by: str
    # 汇总详情。
    summary_details: dict[str, Any] = field(default_factory=dict)
    # 元数据详情。
    metadata_details: dict[str, Any] = field(default_factory=dict)
    # 错误信息。
    error_message: str | None = None
    # 开始时间（UTC ISO 字符串）。
    started_at: str | None = None
    # 完成时间（UTC ISO 字符串）。
    completed_at: str | None = None
    # 创建时间（UTC ISO 字符串）。
    created_at: str | None = None


@dataclass(frozen=True)
class EvaluationRunStatusSummary:
    # 评测运行标识。
    run_id: str
    # 运行状态。
    status: str
    # 创建时间（UTC ISO 字符串）。
    created_at: str | None = None
    # 完成时间（UTC ISO 字符串）。
    completed_at: str | None = None


@dataclass(frozen=True)
class EvaluationCaseRecord:
    # case 唯一标识。
    case_id: str
    # 所属运行标识。
    run_id: str
    # 样本标识。
    sample_id: str
    # 查询文本。
    query_text: str
    # 元数据过滤详情。
    metadata_filter_details: dict[str, Any] = field(default_factory=dict)
    # 检索 top-k。
    top_k: int | None = None
    # 检索标签详情。
    retrieval_label_details: dict[str, Any] = field(default_factory=dict)
    # 引用标签详情。
    citation_label_details: dict[str, Any] = field(default_factory=dict)
    # 回答标签详情。
    answer_label_details: dict[str, Any] = field(default_factory=dict)
    # 检索命中的 chunk ID 列表。
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    # 检索命中的文档 ID 列表。
    retrieved_document_ids: list[str] = field(default_factory=list)
    # 生成引用 ID 列表。
    generated_citation_ids: list[str] = field(default_factory=list)
    # 生成引用文档 ID 列表。
    generated_citation_document_ids: list[str] = field(default_factory=list)
    # 生成回答文本。
    answer_text: str = ""
    # case 结果详情。
    case_result_details: dict[str, Any] = field(default_factory=dict)
    # case 是否通过。
    passed: bool = False
    # 错误信息。
    error_message: str | None = None
    # 创建时间（UTC ISO 字符串）。
    created_at: str | None = None
