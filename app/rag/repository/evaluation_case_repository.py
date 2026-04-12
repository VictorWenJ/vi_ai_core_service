"""evaluation_cases 持久化访问。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.db.session import DatabaseRuntime
from app.rag.repository._utils import copy_json_dict, copy_json_list, datetime_to_iso
from app.rag.repository.models import EvaluationCaseEntity


class EvaluationCaseRepository:
    """评测样本结果访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def add_cases(self, *, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not cases:
            return []
        with self._database_runtime.session_scope() as session:
            entities: list[EvaluationCaseEntity] = []
            for case in cases:
                entity = EvaluationCaseEntity(
                    case_id=str(case["case_id"]),
                    run_id=str(case["run_id"]),
                    sample_id=str(case["sample_id"]),
                    query_text=str(case["query_text"]),
                    metadata_filter_details=dict(case.get("metadata_filter_details") or {}),
                    top_k=case.get("top_k"),
                    retrieval_label_details=dict(case.get("retrieval_label_details") or {}),
                    citation_label_details=dict(case.get("citation_label_details") or {}),
                    answer_label_details=dict(case.get("answer_label_details") or {}),
                    retrieved_chunk_ids=list(case.get("retrieved_chunk_ids") or []),
                    retrieved_document_ids=list(case.get("retrieved_document_ids") or []),
                    generated_citation_ids=list(case.get("generated_citation_ids") or []),
                    generated_citation_document_ids=list(
                        case.get("generated_citation_document_ids") or []
                    ),
                    answer_text=str(case.get("answer_text") or ""),
                    case_result_details=dict(case.get("case_result_details") or {}),
                    passed=bool(case.get("passed", False)),
                    error_message=case.get("error_message"),
                )
                entities.append(entity)
            session.add_all(entities)
            session.flush()
            return [self._to_payload(entity) for entity in entities]

    def list_cases_by_run_id(self, *, run_id: str) -> list[dict[str, Any]]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(EvaluationCaseEntity)
                .where(EvaluationCaseEntity.run_id == run_id)
                .order_by(EvaluationCaseEntity.created_at.asc())
            ).all()
            return [self._to_payload(entity) for entity in entities]

    @staticmethod
    def _to_payload(entity: EvaluationCaseEntity) -> dict[str, Any]:
        return {
            "case_id": entity.case_id,
            "run_id": entity.run_id,
            "sample_id": entity.sample_id,
            "query_text": entity.query_text,
            "metadata_filter_details": copy_json_dict(entity.metadata_filter_details),
            "top_k": entity.top_k,
            "retrieval_label_details": copy_json_dict(entity.retrieval_label_details),
            "citation_label_details": copy_json_dict(entity.citation_label_details),
            "answer_label_details": copy_json_dict(entity.answer_label_details),
            "retrieved_chunk_ids": copy_json_list(entity.retrieved_chunk_ids),
            "retrieved_document_ids": copy_json_list(entity.retrieved_document_ids),
            "generated_citation_ids": copy_json_list(entity.generated_citation_ids),
            "generated_citation_document_ids": copy_json_list(
                entity.generated_citation_document_ids
            ),
            "answer_text": entity.answer_text,
            "case_result_details": copy_json_dict(entity.case_result_details),
            "passed": entity.passed,
            "error_message": entity.error_message,
            "created_at": datetime_to_iso(entity.created_at),
        }

