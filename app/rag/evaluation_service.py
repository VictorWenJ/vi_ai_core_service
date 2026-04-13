"""RAG evaluation 应用服务。"""

from __future__ import annotations

from typing import Any

from app.rag.document_service import RAGDocumentService
from app.rag.evaluation.models import (
    AnswerEvaluationResult,
    AnswerLabel,
    CitationEvaluationResult,
    CitationLabel,
    EvaluationCaseResult,
    EvaluationDataset,
    EvaluationRunResult,
    EvaluationSample,
    EvaluationSummary,
    RetrievalEvaluationResult,
    RetrievalLabel,
)
from app.rag.evaluation.runner import RAGEvaluationRunner
from app.rag.inspector_service import RAGInspectorService
from app.rag.models import generate_run_id, now_utc_iso
from app.rag.repository.evaluation_case_repository import EvaluationCaseRepository
from app.rag.repository.evaluation_run_repository import EvaluationRunRepository
from app.rag.repository.read_models import EvaluationCaseRecord, EvaluationRunRecord
from app.rag.repository._utils import utcnow


def _utc_version_suffix() -> str:
    return utcnow().strftime("%Y%m%dT%H%M%SZ")


class RAGEvaluationService:
    """负责评测运行、结果持久化与查询。"""

    def __init__(
        self,
        *,
        evaluation_run_repository: EvaluationRunRepository,
        evaluation_case_repository: EvaluationCaseRepository,
        inspector_service: RAGInspectorService,
        document_service: RAGDocumentService,
    ) -> None:
        self._evaluation_run_repository = evaluation_run_repository
        self._evaluation_case_repository = evaluation_case_repository
        self._inspector_service = inspector_service
        self._document_service = document_service
        self._runner = RAGEvaluationRunner(rag_runtime=inspector_service)

    def create_evaluation_run(
        self,
        *,
        dataset_id: str | None = None,
        version_id: str | None = None,
        build_id: str | None = None,
        samples: list[dict[str, Any]] | None = None,
        run_metadata: dict[str, Any] | None = None,
        trigger_type: str = "manual",
        triggered_by: str = "internal_console",
    ) -> EvaluationRunResult:
        persisted_dataset_id = (dataset_id or "").strip() or None
        persisted_dataset_version_id = (version_id or "").strip() or None
        dataset = self._build_dataset(
            dataset_id=persisted_dataset_id,
            version_id=persisted_dataset_version_id,
            samples=samples or [],
        )
        run_id = generate_run_id()
        started_at = now_utc_iso()
        self._evaluation_run_repository.create_run(
            run_id=run_id,
            build_id=build_id,
            dataset_id=persisted_dataset_id,
            dataset_version_id=persisted_dataset_version_id,
            status="running",
            trigger_type=trigger_type,
            triggered_by=triggered_by,
            summary_details={},
            metadata_details=dict(run_metadata or {}),
            started_at=utcnow(),
        )
        try:
            cases: list[EvaluationCaseResult] = []
            case_records: list[dict[str, Any]] = []
            for sample in dataset.samples:
                retrieval_result = self._inspector_service.retrieve_for_chat(
                    query_text=sample.query_text,
                    metadata_filter=sample.metadata_filter,
                    top_k=sample.top_k,
                )
                retrieval_eval = self._runner.evaluate_retrieval(
                    sample.retrieval_label,
                    retrieval_result,
                )
                citation_eval = self._runner.evaluate_citation(
                    sample.citation_label,
                    retrieval_result,
                )
                answer_text = self._runner._answer_generator(sample, retrieval_result)  # noqa: SLF001
                answer_eval = self._runner.evaluate_answer(sample.answer_label, answer_text)
                case_passed = (
                    retrieval_eval.passed
                    and citation_eval.passed
                    and answer_eval.passed
                )
                resolved_top_k = retrieval_result.trace.top_k
                case_result = EvaluationCaseResult(
                    sample_id=sample.sample_id,
                    retrieval=retrieval_eval,
                    citation=citation_eval,
                    answer=answer_eval,
                    retrieval_status=retrieval_result.trace.status,
                    passed=case_passed,
                    resolved_top_k=resolved_top_k,
                )
                cases.append(case_result)
                case_records.append(
                    {
                        "case_id": f"{run_id}_{sample.sample_id}",
                        "run_id": run_id,
                        "sample_id": sample.sample_id,
                        "query_text": sample.query_text,
                        "metadata_filter_details": dict(sample.metadata_filter or {}),
                        "top_k": sample.top_k or resolved_top_k,
                        "retrieval_label_details": {
                            "expected_document_ids": list(
                                sample.retrieval_label.expected_document_ids
                            ),
                            "expected_chunk_ids": list(
                                sample.retrieval_label.expected_chunk_ids
                            ),
                            "min_recall": sample.retrieval_label.min_recall,
                        },
                        "citation_label_details": {
                            "expected_citation_ids": list(
                                sample.citation_label.expected_citation_ids
                            ),
                            "expected_document_ids": list(
                                sample.citation_label.expected_document_ids
                            ),
                            "min_recall": sample.citation_label.min_recall,
                            "min_precision": sample.citation_label.min_precision,
                        },
                        "answer_label_details": {
                            "required_terms": list(sample.answer_label.required_terms),
                            "forbidden_terms": list(sample.answer_label.forbidden_terms),
                            "min_required_term_hit_ratio": sample.answer_label.min_required_term_hit_ratio,
                            "max_forbidden_term_hit_count": sample.answer_label.max_forbidden_term_hit_count,
                        },
                        "retrieved_chunk_ids": [
                            chunk.chunk_id for chunk in retrieval_result.retrieved_chunks
                        ],
                        "retrieved_document_ids": [
                            chunk.document_id for chunk in retrieval_result.retrieved_chunks
                        ],
                        "generated_citation_ids": [
                            citation.citation_id for citation in retrieval_result.citations
                        ],
                        "generated_citation_document_ids": [
                            citation.document_id for citation in retrieval_result.citations
                        ],
                        "answer_text": answer_text,
                        "case_result_details": case_result.to_dict(),
                        "passed": case_passed,
                        "error_message": None,
                    }
                )

            self._evaluation_case_repository.add_cases(cases=case_records)
            summary = self._runner._build_summary(cases)  # noqa: SLF001
            completed_at = now_utc_iso()
            metadata_details = {
                **dict(run_metadata or {}),
                "case_count": len(cases),
                "build_id": build_id,
                "status": "succeeded",
                "trigger_type": trigger_type,
                "triggered_by": triggered_by,
            }
            self._evaluation_run_repository.update_run(
                run_id=run_id,
                status="succeeded",
                summary_details=summary.to_dict(),
                metadata_details=metadata_details,
                completed_at=utcnow(),
            )
            return EvaluationRunResult.new(
                run_id=run_id,
                dataset_id=persisted_dataset_id,
                dataset_version_id=persisted_dataset_version_id,
                started_at=started_at,
                completed_at=completed_at,
                cases=cases,
                summary=summary,
                metadata=metadata_details,
            )
        except Exception as exc:
            self._evaluation_run_repository.mark_failed(
                run_id=run_id,
                error_message=str(exc),
                metadata_details={
                    **dict(run_metadata or {}),
                    "build_id": build_id,
                    "status": "failed",
                    "trigger_type": trigger_type,
                    "triggered_by": triggered_by,
                },
            )
            raise

    def list_evaluation_runs(self) -> list[EvaluationRunResult]:
        run_payloads = self._evaluation_run_repository.list_runs()
        return [self._to_run_result(run_payload) for run_payload in run_payloads]

    def get_evaluation_run(self, run_id: str) -> EvaluationRunResult | None:
        run_payload = self._evaluation_run_repository.get_run(run_id=run_id)
        if run_payload is None:
            return None
        return self._to_run_result(run_payload)

    def count_evaluation_runs(self) -> int:
        return self._evaluation_run_repository.count_runs()

    def _to_run_result(self, run_payload: EvaluationRunRecord) -> EvaluationRunResult:
        summary = self._summary_from_dict(dict(run_payload.summary_details or {}))
        case_payloads = self._evaluation_case_repository.list_cases_by_run_id(
            run_id=run_payload.run_id
        )
        cases = [self._case_from_payload(payload) for payload in case_payloads]
        return EvaluationRunResult.new(
            run_id=run_payload.run_id,
            dataset_id=run_payload.dataset_id,
            dataset_version_id=run_payload.dataset_version_id,
            started_at=run_payload.started_at or now_utc_iso(),
            completed_at=run_payload.completed_at or now_utc_iso(),
            cases=cases,
            summary=summary,
            metadata={
                **dict(run_payload.metadata_details or {}),
                "status": run_payload.status,
                "build_id": run_payload.build_id,
                "trigger_type": run_payload.trigger_type,
                "triggered_by": run_payload.triggered_by,
            },
        )

    @staticmethod
    def _summary_from_dict(payload: dict[str, Any]) -> EvaluationSummary:
        return EvaluationSummary(
            sample_count=int(payload.get("sample_count", 0)),
            retrieval_pass_count=int(payload.get("retrieval_pass_count", 0)),
            citation_pass_count=int(payload.get("citation_pass_count", 0)),
            answer_pass_count=int(payload.get("answer_pass_count", 0)),
            overall_pass_count=int(payload.get("overall_pass_count", 0)),
            average_retrieval_recall=float(payload.get("average_retrieval_recall", 0.0)),
            average_citation_recall=float(payload.get("average_citation_recall", 0.0)),
            average_answer_hit_ratio=float(payload.get("average_answer_hit_ratio", 0.0)),
        )

    @staticmethod
    def _case_from_payload(payload: EvaluationCaseRecord) -> EvaluationCaseResult:
        details = dict(payload.case_result_details or {})
        retrieval_details = dict(details.get("retrieval") or {})
        citation_details = dict(details.get("citation") or {})
        answer_details = dict(details.get("answer") or {})
        return EvaluationCaseResult(
            sample_id=payload.sample_id,
            retrieval=RetrievalEvaluationResult(
                document_recall=float(retrieval_details.get("document_recall", 0.0)),
                chunk_recall=float(retrieval_details.get("chunk_recall", 0.0)),
                recall=float(retrieval_details.get("recall", 0.0)),
                matched_document_ids=list(retrieval_details.get("matched_document_ids") or []),
                matched_chunk_ids=list(retrieval_details.get("matched_chunk_ids") or []),
                passed=bool(retrieval_details.get("passed", False)),
            ),
            citation=CitationEvaluationResult(
                recall=float(citation_details.get("recall", 0.0)),
                precision=float(citation_details.get("precision", 0.0)),
                matched_citation_ids=list(citation_details.get("matched_citation_ids") or []),
                matched_document_ids=list(citation_details.get("matched_document_ids") or []),
                passed=bool(citation_details.get("passed", False)),
            ),
            answer=AnswerEvaluationResult(
                required_term_hit_count=int(answer_details.get("required_term_hit_count", 0)),
                required_term_total=int(answer_details.get("required_term_total", 0)),
                forbidden_term_hit_count=int(answer_details.get("forbidden_term_hit_count", 0)),
                required_term_hit_ratio=float(answer_details.get("required_term_hit_ratio", 0.0)),
                passed=bool(answer_details.get("passed", False)),
            ),
            retrieval_status=str(details.get("retrieval_status") or "unknown"),
            passed=bool(details.get("passed", payload.passed)),
            resolved_top_k=int(details.get("resolved_top_k", payload.top_k or 0)),
        )

    def _build_dataset(
        self,
        *,
        dataset_id: str | None,
        version_id: str | None,
        samples: list[dict[str, Any]],
    ) -> EvaluationDataset:
        normalized_dataset_id = (dataset_id or "").strip() or "runtime-generated-dataset"
        normalized_version_id = (version_id or "").strip() or f"runtime-{_utc_version_suffix()}"
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
