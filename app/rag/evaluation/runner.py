"""Phase 7 RAG evaluation runner."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any
from typing import Callable
from typing import Protocol

from app.observability.log_until import log_report
from app.rag.evaluation.models import (
    AnswerEvaluationResult,
    AnswerLabel,
    CitationEvaluationResult,
    CitationLabel,
    EvaluationCaseResult,
    EvaluationDataset,
    EvaluationRunResult,
    EvaluationSummary,
    EvaluationSample,
    RetrievalEvaluationResult,
    RetrievalLabel,
)
from app.rag.models import RetrievalResult, now_utc_iso


AnswerGenerator = Callable[[EvaluationSample, RetrievalResult], str]


class RetrievalRuntimeLike(Protocol):
    """评估运行器依赖的最小检索运行时协议。"""

    def retrieve_for_chat(
        self,
        *,
        query_text: str,
        metadata_filter: dict[str, Any] | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """执行单次检索。"""


class RAGEvaluationRunner:
    """Run retrieval/citation/answer benchmark against current RAG runtime."""

    def __init__(
        self,
        *,
        rag_runtime: RetrievalRuntimeLike,
        answer_generator: AnswerGenerator | None = None,
    ) -> None:
        self._rag_runtime = rag_runtime
        self._answer_generator = answer_generator or self._default_answer_generator

    def run(
        self,
        dataset: EvaluationDataset,
        *,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        result_output_path: str | Path | None = None,
    ) -> EvaluationRunResult:
        started_at = now_utc_iso()
        started_perf_counter = perf_counter()
        log_report(
            "rag.evaluation.run.started",
            {
                "dataset_id": dataset.dataset_id,
                "dataset_version_id": dataset.version_id,
                "sample_count": len(dataset.samples),
            },
        )

        cases: list[EvaluationCaseResult] = []
        for sample in dataset.samples:
            retrieval_result = self._rag_runtime.retrieve_for_chat(
                query_text=sample.query_text,
                metadata_filter=sample.metadata_filter,
                top_k=sample.top_k,
            )
            retrieval_eval = self.evaluate_retrieval(sample.retrieval_label, retrieval_result)
            citation_eval = self.evaluate_citation(sample.citation_label, retrieval_result)
            answer_text = self._answer_generator(sample, retrieval_result)
            answer_eval = self.evaluate_answer(sample.answer_label, answer_text)
            case_passed = retrieval_eval.passed and citation_eval.passed and answer_eval.passed
            resolved_top_k = retrieval_result.trace.top_k
            cases.append(
                EvaluationCaseResult(
                    sample_id=sample.sample_id,
                    retrieval=retrieval_eval,
                    citation=citation_eval,
                    answer=answer_eval,
                    retrieval_status=retrieval_result.trace.status,
                    passed=case_passed,
                    resolved_top_k=resolved_top_k,
                )
            )

        summary = self._build_summary(cases)
        completed_at = now_utc_iso()
        run_result = EvaluationRunResult.new(
            run_id=run_id,
            dataset_id=dataset.dataset_id,
            dataset_version_id=dataset.version_id,
            started_at=started_at,
            completed_at=completed_at,
            cases=cases,
            summary=summary,
            metadata={
                **dict(metadata or {}),
                "latency_ms": round((perf_counter() - started_perf_counter) * 1000, 2),
            },
        )
        if result_output_path is not None:
            run_result.save_json(result_output_path)
        log_report("rag.evaluation.run.completed", run_result.to_dict())
        return run_result

    @staticmethod
    def evaluate_retrieval(
        label: RetrievalLabel,
        retrieval_result: RetrievalResult,
    ) -> RetrievalEvaluationResult:
        retrieved_document_ids = {
            chunk.document_id for chunk in retrieval_result.retrieved_chunks if chunk.document_id
        }
        retrieved_chunk_ids = {
            chunk.chunk_id for chunk in retrieval_result.retrieved_chunks if chunk.chunk_id
        }
        expected_document_ids = set(label.expected_document_ids)
        expected_chunk_ids = set(label.expected_chunk_ids)

        matched_document_ids = sorted(expected_document_ids.intersection(retrieved_document_ids))
        matched_chunk_ids = sorted(expected_chunk_ids.intersection(retrieved_chunk_ids))

        document_recall = (
            len(matched_document_ids) / len(expected_document_ids)
            if expected_document_ids
            else 1.0
        )
        chunk_recall = (
            len(matched_chunk_ids) / len(expected_chunk_ids)
            if expected_chunk_ids
            else 1.0
        )
        recall = min(document_recall, chunk_recall)
        passed = recall >= label.min_recall
        return RetrievalEvaluationResult(
            document_recall=document_recall,
            chunk_recall=chunk_recall,
            recall=recall,
            matched_document_ids=matched_document_ids,
            matched_chunk_ids=matched_chunk_ids,
            passed=passed,
        )

    @staticmethod
    def evaluate_citation(
        label: CitationLabel,
        retrieval_result: RetrievalResult,
    ) -> CitationEvaluationResult:
        retrieved_citation_ids = {
            citation.citation_id for citation in retrieval_result.citations if citation.citation_id
        }
        retrieved_document_ids = {
            citation.document_id for citation in retrieval_result.citations if citation.document_id
        }
        expected_citation_ids = set(label.expected_citation_ids)
        expected_document_ids = set(label.expected_document_ids)
        matched_citation_ids = sorted(expected_citation_ids.intersection(retrieved_citation_ids))
        matched_document_ids = sorted(expected_document_ids.intersection(retrieved_document_ids))

        expected_total = len(expected_citation_ids) + len(expected_document_ids)
        matched_total = len(matched_citation_ids) + len(matched_document_ids)
        predicted_total = len(retrieved_citation_ids) + len(retrieved_document_ids)
        recall = (matched_total / expected_total) if expected_total else 1.0
        if predicted_total == 0:
            precision = 1.0 if expected_total == 0 else 0.0
        else:
            precision = matched_total / predicted_total
        passed = recall >= label.min_recall and precision >= label.min_precision
        return CitationEvaluationResult(
            recall=recall,
            precision=precision,
            matched_citation_ids=matched_citation_ids,
            matched_document_ids=matched_document_ids,
            passed=passed,
        )

    @staticmethod
    def evaluate_answer(
        label: AnswerLabel,
        answer_text: str,
    ) -> AnswerEvaluationResult:
        lowered_answer_text = answer_text.lower()
        required_term_hit_count = sum(
            1
            for term in label.required_terms
            if term.lower() in lowered_answer_text
        )
        forbidden_term_hit_count = sum(
            1
            for term in label.forbidden_terms
            if term.lower() in lowered_answer_text
        )
        required_term_total = len(label.required_terms)
        required_term_hit_ratio = (
            required_term_hit_count / required_term_total
            if required_term_total > 0
            else 1.0
        )
        passed = (
            required_term_hit_ratio >= label.min_required_term_hit_ratio
            and forbidden_term_hit_count <= label.max_forbidden_term_hit_count
        )
        return AnswerEvaluationResult(
            required_term_hit_count=required_term_hit_count,
            required_term_total=required_term_total,
            forbidden_term_hit_count=forbidden_term_hit_count,
            required_term_hit_ratio=required_term_hit_ratio,
            passed=passed,
        )

    @staticmethod
    def _default_answer_generator(sample: EvaluationSample, retrieval_result: RetrievalResult) -> str:
        del sample
        if retrieval_result.citations:
            return "\n".join(citation.snippet for citation in retrieval_result.citations)
        return retrieval_result.knowledge_block or ""

    @staticmethod
    def _build_summary(cases: list[EvaluationCaseResult]) -> EvaluationSummary:
        sample_count = len(cases)
        retrieval_pass_count = sum(1 for case in cases if case.retrieval.passed)
        citation_pass_count = sum(1 for case in cases if case.citation.passed)
        answer_pass_count = sum(1 for case in cases if case.answer.passed)
        overall_pass_count = sum(1 for case in cases if case.passed)
        if sample_count == 0:
            return EvaluationSummary(
                sample_count=0,
                retrieval_pass_count=0,
                citation_pass_count=0,
                answer_pass_count=0,
                overall_pass_count=0,
                average_retrieval_recall=0.0,
                average_citation_recall=0.0,
                average_answer_hit_ratio=0.0,
            )

        return EvaluationSummary(
            sample_count=sample_count,
            retrieval_pass_count=retrieval_pass_count,
            citation_pass_count=citation_pass_count,
            answer_pass_count=answer_pass_count,
            overall_pass_count=overall_pass_count,
            average_retrieval_recall=sum(case.retrieval.recall for case in cases) / sample_count,
            average_citation_recall=sum(case.citation.recall for case in cases) / sample_count,
            average_answer_hit_ratio=sum(case.answer.required_term_hit_ratio for case in cases) / sample_count,
        )
