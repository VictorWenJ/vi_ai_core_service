"""Core models for Knowledge + Citation layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import Any
from uuid import uuid4


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_prefixed_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def generate_run_id() -> str:
    return _generate_prefixed_id("run")


def generate_build_id() -> str:
    return _generate_prefixed_id("build")


def compute_content_hash(content: str) -> str:
    normalized_content = content.strip().encode("utf-8")
    return hashlib.sha1(normalized_content).hexdigest()


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
    # 文档在知识库中的稳定唯一标识。
    document_id: str
    # 文档标题，用于检索展示与引用输出。
    title: str
    # 文档来源类型，如 raw_text、text_file、markdown_file。
    source_type: str
    # 规范化后的完整正文文本。
    content: str
    # 原始来源 URI 或路径；不可用时为空。
    origin_uri: str | None = None
    # 文件导入场景下的文件名；非文件来源时为空。
    file_name: str | None = None
    # 可选法域标签，用于检索过滤。
    jurisdiction: str | None = None
    # 可选业务域标签，用于检索过滤。
    domain: str | None = None
    # 文档标签列表，用于分类与过滤。
    tags: list[str] = field(default_factory=list)
    # 文档生效时间，UTC ISO 字符串；不可用时为空。
    effective_at: str | None = None
    # 文档更新时间，UTC ISO 字符串；为空时在初始化阶段回填当前时间。
    updated_at: str | None = None
    # 可见性范围标识，默认 internal。
    visibility: str = "internal"
    # 扩展元数据字典，承载业务附加信息。
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
    # chunk 唯一标识。
    chunk_id: str
    # chunk 所属文档 ID。
    document_id: str
    # chunk 正文文本。
    chunk_text: str
    # chunk 在文档中的顺序索引，单位为序号（count）。
    chunk_index: int
    # chunk token 数，单位为 token。
    token_count: int
    # 生成向量时使用的 embedding 模型标识。
    embedding_model: str
    # chunk 级扩展元数据。
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
    # 命中 chunk ID。
    chunk_id: str
    # 命中 chunk 所属文档 ID。
    document_id: str
    # 命中 chunk 文本内容。
    text: str
    # 相似度分值（cosine）。
    score: float
    # 文档标题；缺失时为空。
    title: str | None
    # 文档来源 URI；缺失时为空。
    origin_uri: str | None
    # 文档来源类型；缺失时为空。
    source_type: str | None
    # 法域标签；缺失时为空。
    jurisdiction: str | None
    # 业务域标签；缺失时为空。
    domain: str | None
    # 文档生效时间；缺失时为空。
    effective_at: str | None
    # 文档更新时间；缺失时为空。
    updated_at: str | None
    # 命中结果扩展元数据。
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
    # 引用唯一标识。
    citation_id: str
    # 引用来源文档 ID。
    document_id: str
    # 引用来源 chunk ID。
    chunk_id: str
    # 引用标题；缺失时为空。
    title: str | None
    # 可展示的引用片段文本。
    snippet: str
    # 引用来源 URI；缺失时为空。
    origin_uri: str | None
    # 引用来源类型；缺失时为空。
    source_type: str | None
    # 引用对应文档更新时间；缺失时为空。
    updated_at: str | None
    # 引用扩展元数据。
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalTrace:
    # 检索状态，如 disabled/succeeded/degraded/failed。
    status: str
    # 检索查询文本。
    query_text: str
    # 检索 top-k 参数值，单位为条（count）。
    top_k: int
    # 检索元数据过滤条件快照。
    metadata_filter: dict[str, Any] = field(default_factory=dict)
    # 检索命中数量，单位为条（count）。
    hit_count: int = 0
    # 生成引用数量，单位为条（count）。
    citation_count: int = 0
    # 检索耗时，单位为毫秒（ms）。
    latency_ms: float = 0.0
    # 错误类型标识；成功场景为空。
    error_type: str | None = None
    # 错误信息；成功场景为空。
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalResult:
    # 供 request assembly 注入的知识块文本；无结果时为空。
    knowledge_block: str | None
    # 原始检索命中 chunk 列表。
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    # 基于命中结果生成的 citations。
    citations: list[Citation] = field(default_factory=list)
    # 检索链路追踪信息。
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
    # 导入状态，如 succeeded/failed/degraded。
    status: str
    # 本次导入文档数量，单位为篇（count）。
    document_count: int
    # 本次生成 chunk 数量，单位为块（count）。
    chunk_count: int
    # 本次 embedding 批次数，单位为批（count）。
    embedding_batch_count: int
    # 本次 embedding 向量维度，单位为维（dimension）。
    embedding_dimension: int
    # 本次向量索引 upsert 成功数量，单位为条（count）。
    upserted_count: int
    # 导入链路耗时，单位为毫秒（ms）。
    latency_ms: float
    # 错误类型标识；成功场景为空。
    error_type: str | None = None
    # 错误信息；成功场景为空。
    error_message: str | None = None


@dataclass
class IngestionResult:
    # 归一化后的导入文档对象。
    document: KnowledgeDocument
    # 导入阶段生成的 chunk 列表。
    chunks: list[KnowledgeChunk]
    # 导入链路追踪信息。
    trace: IngestionTrace


@dataclass
class OfflineBuildMetadata:
    # 构建批次唯一标识。
    build_id: str
    # 构建版本号，用于跨批次回归比较。
    version_id: str
    # chunk 策略版本标识。
    chunk_strategy_version: str
    # embedding 模型版本标识。
    embedding_model_version: str
    # 构建模式（full / incremental / partial）。
    build_mode: str
    # 构建开始时间，UTC ISO 字符串。
    started_at: str
    # 构建完成时间，UTC ISO 字符串。
    completed_at: str

    def __post_init__(self) -> None:
        self.build_id = _normalize_optional_text(self.build_id) or generate_build_id()
        self.version_id = _normalize_optional_text(self.version_id) or "v0"
        self.chunk_strategy_version = (
            _normalize_optional_text(self.chunk_strategy_version)
            or "chunk-unknown"
        )
        self.embedding_model_version = (
            _normalize_optional_text(self.embedding_model_version)
            or "embedding-unknown"
        )
        self.build_mode = (_normalize_optional_text(self.build_mode) or "full").lower()
        if self.build_mode not in {"full", "incremental", "partial"}:
            raise ValueError("OfflineBuildMetadata.build_mode must be full/incremental/partial.")
        self.started_at = _normalize_optional_text(self.started_at) or now_utc_iso()
        self.completed_at = _normalize_optional_text(self.completed_at) or now_utc_iso()


@dataclass
class OfflineBuildStatistics:
    # 请求构建的文档总数，单位为篇（count）。
    requested_document_count: int
    # 实际处理的文档数，单位为篇（count）。
    processed_document_count: int
    # 因增量判定被跳过的文档数，单位为篇（count）。
    skipped_document_count: int
    # 构建失败的文档数，单位为篇（count）。
    failed_document_count: int
    # 本次生成 chunk 总数，单位为块（count）。
    chunk_count: int
    # 本次写入向量索引条数，单位为条（count）。
    upserted_count: int
    # 本次 embedding 批次数，单位为批（count）。
    embedding_batch_count: int
    # 构建总耗时，单位为毫秒（ms）。
    latency_ms: float

    def __post_init__(self) -> None:
        integer_fields = (
            "requested_document_count",
            "processed_document_count",
            "skipped_document_count",
            "failed_document_count",
            "chunk_count",
            "upserted_count",
            "embedding_batch_count",
        )
        for field_name in integer_fields:
            if getattr(self, field_name) < 0:
                raise ValueError(f"OfflineBuildStatistics.{field_name} must be >= 0.")
        if self.latency_ms < 0:
            raise ValueError("OfflineBuildStatistics.latency_ms must be >= 0.")


@dataclass
class OfflineBuildQualityGate:
    # 构建质量门禁是否通过。
    passed: bool
    # 未通过的规则列表。
    failed_rules: list[str] = field(default_factory=list)
    # 文档失败率（failed / requested），取值区间 [0, 1]。
    failure_ratio: float = 0.0
    # 空 chunk 率（processed 但无 chunk 的文档占比），取值区间 [0, 1]。
    empty_chunk_ratio: float = 0.0
    # 允许的最大失败率阈值，取值区间 [0, 1]。
    max_failure_ratio: float = 0.0
    # 允许的最大空 chunk 率阈值，取值区间 [0, 1]。
    max_empty_chunk_ratio: float = 0.0

    def __post_init__(self) -> None:
        for field_name in (
            "failure_ratio",
            "empty_chunk_ratio",
            "max_failure_ratio",
            "max_empty_chunk_ratio",
        ):
            field_value = getattr(self, field_name)
            if field_value < 0 or field_value > 1:
                raise ValueError(f"OfflineBuildQualityGate.{field_name} must be in [0, 1].")
        self.failed_rules = [str(rule).strip() for rule in self.failed_rules if str(rule).strip()]


@dataclass
class OfflineBuildDocumentRecord:
    # 文档唯一标识。
    document_id: str
    # 文档内容哈希，用于增量构建判定。
    content_hash: str
    # 文档最近构建时间，UTC ISO 字符串。
    built_at: str

    def __post_init__(self) -> None:
        self.document_id = _normalize_optional_text(self.document_id) or ""
        self.content_hash = _normalize_optional_text(self.content_hash) or ""
        self.built_at = _normalize_optional_text(self.built_at) or now_utc_iso()
        if not self.document_id:
            raise ValueError("OfflineBuildDocumentRecord.document_id cannot be empty.")
        if not self.content_hash:
            raise ValueError("OfflineBuildDocumentRecord.content_hash cannot be empty.")


@dataclass
class OfflineBuildManifest:
    # manifest 关联的版本号。
    version_id: str
    # 文档构建记录映射，键为 document_id。
    records: dict[str, OfflineBuildDocumentRecord] = field(default_factory=dict)
    # manifest 生成时间，UTC ISO 字符串。
    generated_at: str = field(default_factory=now_utc_iso)

    def __post_init__(self) -> None:
        self.version_id = _normalize_optional_text(self.version_id) or "v0"
        self.records = {
            str(document_id): record
            for document_id, record in dict(self.records or {}).items()
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "generated_at": self.generated_at,
            "records": {
                document_id: asdict(record)
                for document_id, record in self.records.items()
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OfflineBuildManifest":
        records = {}
        for document_id, record_payload in dict(payload.get("records") or {}).items():
            record_dict = dict(record_payload or {})
            if "document_id" not in record_dict:
                record_dict["document_id"] = str(document_id)
            records[str(document_id)] = OfflineBuildDocumentRecord(**record_dict)
        return cls(
            version_id=str(payload.get("version_id") or "v0"),
            records=records,
            generated_at=str(payload.get("generated_at") or now_utc_iso()),
        )


@dataclass
class OfflineBuildResult:
    # 离线构建元数据。
    metadata: OfflineBuildMetadata
    # 离线构建统计信息。
    statistics: OfflineBuildStatistics
    # 质量门禁执行结果。
    quality_gate: OfflineBuildQualityGate
    # 本次构建后的 manifest 快照。
    manifest: OfflineBuildManifest
    # 本次成功处理的文档导入结果列表。
    ingestion_results: list[IngestionResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": asdict(self.metadata),
            "statistics": asdict(self.statistics),
            "quality_gate": asdict(self.quality_gate),
            "manifest": self.manifest.to_dict(),
            "ingestion_results": [
                {
                    "document_id": result.document.document_id,
                    "chunk_count": len(result.chunks),
                    "trace": asdict(result.trace),
                }
                for result in self.ingestion_results
            ],
        }
