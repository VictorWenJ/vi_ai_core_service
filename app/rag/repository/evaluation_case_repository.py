"""evaluation_cases 持久化访问。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.db.session import DatabaseRuntime
from app.rag.repository.mappers import map_evaluation_case_entity_to_record
from app.rag.repository.models import EvaluationCaseEntity
from app.rag.repository.read_models import EvaluationCaseRecord


class EvaluationCaseRepository:
    """评测样本结果访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def add_cases(self, *, cases: list[dict[str, Any]]) -> list[EvaluationCaseRecord]:
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
            return [map_evaluation_case_entity_to_record(entity) for entity in entities]

    def list_cases_by_run_id(self, *, run_id: str) -> list[EvaluationCaseRecord]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(EvaluationCaseEntity)
                .where(EvaluationCaseEntity.run_id == run_id)
                .order_by(EvaluationCaseEntity.created_at.asc())
            ).all()
            return [map_evaluation_case_entity_to_record(entity) for entity in entities]
