"""Phase 7 RAG evaluation dataset and result models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.rag.models import generate_run_id, now_utc_iso


def _normalize_terms(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            normalized.append(text)
    return normalized


@dataclass
class RetrievalLabel:
    # 期望命中的文档 ID 列表。
    expected_document_ids: list[str] = field(default_factory=list)
    # 期望命中的 chunk ID 列表。
    expected_chunk_ids: list[str] = field(default_factory=list)
    # 检索召回率最小阈值，取值区间 [0, 1]。
    min_recall: float = 1.0

    def __post_init__(self) -> None:
        self.expected_document_ids = _normalize_terms(self.expected_document_ids)
        self.expected_chunk_ids = _normalize_terms(self.expected_chunk_ids)
        if self.min_recall < 0 or self.min_recall > 1:
            raise ValueError("RetrievalLabel.min_recall must be in [0, 1].")


@dataclass
class CitationLabel:
    # 期望命中的 citation ID 列表。
    expected_citation_ids: list[str] = field(default_factory=list)
    # 期望命中的 citation 文档 ID 列表。
    expected_document_ids: list[str] = field(default_factory=list)
    # citation 召回率最小阈值，取值区间 [0, 1]。
    min_recall: float = 1.0
    # citation 精确率最小阈值，取值区间 [0, 1]。
    min_precision: float = 0.0

    def __post_init__(self) -> None:
        self.expected_citation_ids = _normalize_terms(self.expected_citation_ids)
        self.expected_document_ids = _normalize_terms(self.expected_document_ids)
        if self.min_recall < 0 or self.min_recall > 1:
            raise ValueError("CitationLabel.min_recall must be in [0, 1].")
        if self.min_precision < 0 or self.min_precision > 1:
            raise ValueError("CitationLabel.min_precision must be in [0, 1].")


@dataclass
class AnswerLabel:
    # 回答中必须命中的关键词列表。
    required_terms: list[str] = field(default_factory=list)
    # 回答中禁止出现的关键词列表。
    forbidden_terms: list[str] = field(default_factory=list)
    # required_terms 最小命中比例，取值区间 [0, 1]。
    min_required_term_hit_ratio: float = 1.0
    # forbidden_terms 允许命中最大数量，单位为条（count）。
    max_forbidden_term_hit_count: int = 0

    def __post_init__(self) -> None:
        self.required_terms = _normalize_terms(self.required_terms)
        self.forbidden_terms = _normalize_terms(self.forbidden_terms)
        if self.min_required_term_hit_ratio < 0 or self.min_required_term_hit_ratio > 1:
            raise ValueError("AnswerLabel.min_required_term_hit_ratio must be in [0, 1].")
        if self.max_forbidden_term_hit_count < 0:
            raise ValueError("AnswerLabel.max_forbidden_term_hit_count must be >= 0.")


@dataclass
class EvaluationSample:
    # 样本唯一标识。
    sample_id: str
    # 评估查询文本。
    query_text: str
    # 评估查询 metadata filter 快照。
    metadata_filter: dict[str, Any] = field(default_factory=dict)
    # 样本级 top-k 覆盖值；为空时使用运行器默认值。
    top_k: int | None = None
    # 检索层标签。
    retrieval_label: RetrievalLabel = field(default_factory=RetrievalLabel)
    # 引用层标签。
    citation_label: CitationLabel = field(default_factory=CitationLabel)
    # 回答层标签。
    answer_label: AnswerLabel = field(default_factory=AnswerLabel)
    # 样本扩展元数据。
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.sample_id = self.sample_id.strip()
        self.query_text = self.query_text.strip()
        if not self.sample_id:
            raise ValueError("EvaluationSample.sample_id cannot be empty.")
        if not self.query_text:
            raise ValueError("EvaluationSample.query_text cannot be empty.")
        if self.top_k is not None and self.top_k <= 0:
            raise ValueError("EvaluationSample.top_k must be > 0 when provided.")
        self.metadata_filter = dict(self.metadata_filter or {})
        self.metadata = dict(self.metadata or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "query_text": self.query_text,
            "metadata_filter": dict(self.metadata_filter),
            "top_k": self.top_k,
            "retrieval_label": {
                "expected_document_ids": list(self.retrieval_label.expected_document_ids),
                "expected_chunk_ids": list(self.retrieval_label.expected_chunk_ids),
                "min_recall": self.retrieval_label.min_recall,
            },
            "citation_label": {
                "expected_citation_ids": list(self.citation_label.expected_citation_ids),
                "expected_document_ids": list(self.citation_label.expected_document_ids),
                "min_recall": self.citation_label.min_recall,
                "min_precision": self.citation_label.min_precision,
            },
            "answer_label": {
                "required_terms": list(self.answer_label.required_terms),
                "forbidden_terms": list(self.answer_label.forbidden_terms),
                "min_required_term_hit_ratio": self.answer_label.min_required_term_hit_ratio,
                "max_forbidden_term_hit_count": self.answer_label.max_forbidden_term_hit_count,
            },
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvaluationSample":
        return cls(
            sample_id=str(payload["sample_id"]),
            query_text=str(payload["query_text"]),
            metadata_filter=dict(payload.get("metadata_filter") or {}),
            top_k=payload.get("top_k"),
            retrieval_label=RetrievalLabel(**dict(payload.get("retrieval_label") or {})),
            citation_label=CitationLabel(**dict(payload.get("citation_label") or {})),
            answer_label=AnswerLabel(**dict(payload.get("answer_label") or {})),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass
class EvaluationDataset:
    # 评估数据集唯一标识。
    dataset_id: str
    # 数据集版本号，用于回归比较。
    version_id: str
    # 样本列表。
    samples: list[EvaluationSample]
    # 数据集创建时间，UTC ISO 字符串。
    created_at: str = field(default_factory=now_utc_iso)
    # 数据集扩展元数据。
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.dataset_id = self.dataset_id.strip()
        self.version_id = self.version_id.strip()
        if not self.dataset_id:
            raise ValueError("EvaluationDataset.dataset_id cannot be empty.")
        if not self.version_id:
            raise ValueError("EvaluationDataset.version_id cannot be empty.")
        self.metadata = dict(self.metadata or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version_id": self.version_id,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "samples": [sample.to_dict() for sample in self.samples],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvaluationDataset":
        return cls(
            dataset_id=str(payload["dataset_id"]),
            version_id=str(payload["version_id"]),
            created_at=str(payload.get("created_at") or now_utc_iso()),
            metadata=dict(payload.get("metadata") or {}),
            samples=[
                EvaluationSample.from_dict(sample_payload)
                for sample_payload in list(payload.get("samples") or [])
            ],
        )

    def save_json(self, file_path: str | Path) -> None:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_json(cls, file_path: str | Path) -> "EvaluationDataset":
        path = Path(file_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("EvaluationDataset JSON payload must be an object.")
        return cls.from_dict(payload)


@dataclass
class RetrievalEvaluationResult:
    # 文档层召回率。
    document_recall: float
    # chunk 层召回率。
    chunk_recall: float
    # 综合召回率分值。
    recall: float
    # 命中的期望文档 ID 列表。
    matched_document_ids: list[str] = field(default_factory=list)
    # 命中的期望 chunk ID 列表。
    matched_chunk_ids: list[str] = field(default_factory=list)
    # 是否通过 retrieval 标签判定。
    passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_recall": self.document_recall,
            "chunk_recall": self.chunk_recall,
            "recall": self.recall,
            "matched_document_ids": list(self.matched_document_ids),
            "matched_chunk_ids": list(self.matched_chunk_ids),
            "passed": self.passed,
        }


@dataclass
class CitationEvaluationResult:
    # citation 召回率。
    recall: float
    # citation 精确率。
    precision: float
    # 命中的期望 citation ID 列表。
    matched_citation_ids: list[str] = field(default_factory=list)
    # 命中的期望 citation 文档 ID 列表。
    matched_document_ids: list[str] = field(default_factory=list)
    # 是否通过 citation 标签判定。
    passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "recall": self.recall,
            "precision": self.precision,
            "matched_citation_ids": list(self.matched_citation_ids),
            "matched_document_ids": list(self.matched_document_ids),
            "passed": self.passed,
        }


@dataclass
class AnswerEvaluationResult:
    # required_terms 实际命中数，单位为条（count）。
    required_term_hit_count: int
    # required_terms 总数，单位为条（count）。
    required_term_total: int
    # forbidden_terms 实际命中数，单位为条（count）。
    forbidden_term_hit_count: int
    # required_terms 命中比例，取值区间 [0, 1]。
    required_term_hit_ratio: float
    # 是否通过 answer 标签判定。
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_term_hit_count": self.required_term_hit_count,
            "required_term_total": self.required_term_total,
            "forbidden_term_hit_count": self.forbidden_term_hit_count,
            "required_term_hit_ratio": self.required_term_hit_ratio,
            "passed": self.passed,
        }


@dataclass
class EvaluationCaseResult:
    # 样本 ID。
    sample_id: str
    # retrieval 层评估结果。
    retrieval: RetrievalEvaluationResult
    # citation 层评估结果。
    citation: CitationEvaluationResult
    # answer 层评估结果。
    answer: AnswerEvaluationResult
    # 本样本检索状态快照。
    retrieval_status: str
    # 本样本是否整体通过。
    passed: bool
    # 本样本 top-k 实际值。
    resolved_top_k: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "retrieval": self.retrieval.to_dict(),
            "citation": self.citation.to_dict(),
            "answer": self.answer.to_dict(),
            "retrieval_status": self.retrieval_status,
            "passed": self.passed,
            "resolved_top_k": self.resolved_top_k,
        }


@dataclass
class EvaluationSummary:
    # 样本总数，单位为条（count）。
    sample_count: int
    # retrieval 通过样本数，单位为条（count）。
    retrieval_pass_count: int
    # citation 通过样本数，单位为条（count）。
    citation_pass_count: int
    # answer 通过样本数，单位为条（count）。
    answer_pass_count: int
    # 综合通过样本数，单位为条（count）。
    overall_pass_count: int
    # retrieval 平均召回率。
    average_retrieval_recall: float
    # citation 平均召回率。
    average_citation_recall: float
    # answer 平均命中率。
    average_answer_hit_ratio: float

    def to_dict(self) -> dict[str, Any]:
        sample_count = max(self.sample_count, 1)
        return {
            "sample_count": self.sample_count,
            "retrieval_pass_count": self.retrieval_pass_count,
            "citation_pass_count": self.citation_pass_count,
            "answer_pass_count": self.answer_pass_count,
            "overall_pass_count": self.overall_pass_count,
            "retrieval_pass_rate": self.retrieval_pass_count / sample_count,
            "citation_pass_rate": self.citation_pass_count / sample_count,
            "answer_pass_rate": self.answer_pass_count / sample_count,
            "overall_pass_rate": self.overall_pass_count / sample_count,
            "average_retrieval_recall": self.average_retrieval_recall,
            "average_citation_recall": self.average_citation_recall,
            "average_answer_hit_ratio": self.average_answer_hit_ratio,
        }


@dataclass
class EvaluationRunResult:
    # 评估运行批次 ID。
    run_id: str
    # 评估数据集 ID（可空）。
    dataset_id: str | None
    # 评估数据集版本号（可空）。
    dataset_version_id: str | None
    # 运行开始时间，UTC ISO 字符串。
    started_at: str
    # 运行完成时间，UTC ISO 字符串。
    completed_at: str
    # 逐样本评估结果。
    cases: list[EvaluationCaseResult]
    # 汇总评估指标。
    summary: EvaluationSummary
    # 运行扩展元数据。
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        *,
        dataset_id: str | None,
        dataset_version_id: str | None,
        started_at: str,
        completed_at: str,
        cases: list[EvaluationCaseResult],
        summary: EvaluationSummary,
        metadata: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> "EvaluationRunResult":
        return cls(
            run_id=(run_id or "").strip() or generate_run_id(),
            dataset_id=(dataset_id or "").strip() or None,
            dataset_version_id=(dataset_version_id or "").strip() or None,
            started_at=started_at,
            completed_at=completed_at,
            cases=cases,
            summary=summary,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset_id": self.dataset_id,
            "dataset_version_id": self.dataset_version_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "summary": self.summary.to_dict(),
            "cases": [case.to_dict() for case in self.cases],
            "metadata": dict(self.metadata),
        }

    def save_json(self, file_path: str | Path) -> None:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
