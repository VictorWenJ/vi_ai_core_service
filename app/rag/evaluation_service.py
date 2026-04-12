"""RAG evaluation domain service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.rag.document_service import RAGDocumentService
from app.rag.evaluation.models import (
    AnswerLabel,
    CitationLabel,
    EvaluationDataset,
    EvaluationRunResult,
    EvaluationSample,
    RetrievalLabel,
)
from app.rag.evaluation.runner import RAGEvaluationRunner
from app.rag.inspector_service import RAGInspectorService
from app.rag.state import RAGControlState


def _utc_version_suffix() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class RAGEvaluationService:
    """Create/list/get evaluation runs and dataset conversion for control-plane APIs."""

    def __init__(
        self,
        *,
        state: RAGControlState,
        inspector_service: RAGInspectorService,
        document_service: RAGDocumentService,
    ) -> None:
        self._state = state
        self._inspector_service = inspector_service
        self._document_service = document_service
        self._runner = RAGEvaluationRunner(rag_runtime=inspector_service)

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
        run_result = self._runner.run(
            dataset,
            metadata=run_metadata or {"trigger": "internal_console"},
        )
        with self._state.lock:
            self._state.evaluation_runs[run_result.run_id] = run_result
            if run_result.run_id not in self._state.evaluation_run_ids:
                self._state.evaluation_run_ids.insert(0, run_result.run_id)
        return run_result

    def list_evaluation_runs(self) -> list[EvaluationRunResult]:
        with self._state.lock:
            return [
                self._state.evaluation_runs[run_id]
                for run_id in self._state.evaluation_run_ids
                if run_id in self._state.evaluation_runs
            ]

    def get_evaluation_run(self, run_id: str) -> EvaluationRunResult | None:
        with self._state.lock:
            return self._state.evaluation_runs.get(run_id)

    def count_evaluation_runs(self) -> int:
        with self._state.lock:
            return len(self._state.evaluation_runs)

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
            dataset_samples = [
                self._sample_from_payload(index, sample)
                for index, sample in enumerate(samples)
            ]
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
        documents = self._document_service.list_document_entities()
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

