"""evaluation_runs 持久化访问。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select

from app.db.session import DatabaseRuntime
from app.rag.repository._utils import utcnow
from app.rag.repository.mappers import (
    map_evaluation_run_entity_to_record,
    map_evaluation_run_entity_to_status_summary,
)
from app.rag.repository.models import EvaluationRunEntity
from app.rag.repository.read_models import EvaluationRunRecord, EvaluationRunStatusSummary


class EvaluationRunRepository:
    """评测运行任务访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def create_run(
        self,
        *,
        run_id: str,
        build_id: str | None,
        dataset_id: str | None,
        dataset_version_id: str | None,
        status: str,
        trigger_type: str,
        triggered_by: str,
        summary_details: dict[str, Any] | None = None,
        metadata_details: dict[str, Any] | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> EvaluationRunRecord:
        with self._database_runtime.session_scope() as session:
            entity = EvaluationRunEntity(
                run_id=run_id,
                build_id=build_id,
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                status=status,
                trigger_type=trigger_type,
                triggered_by=triggered_by,
                summary_details=dict(summary_details or {}),
                metadata_details=dict(metadata_details or {}),
                error_message=error_message,
                started_at=started_at,
                completed_at=completed_at,
            )
            session.add(entity)
            session.flush()
            return map_evaluation_run_entity_to_record(entity)

    def update_run(
        self,
        *,
        run_id: str,
        status: str | None = None,
        summary_details: dict[str, Any] | None = None,
        metadata_details: dict[str, Any] | None = None,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> EvaluationRunRecord | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(EvaluationRunEntity).where(EvaluationRunEntity.run_id == run_id)
            )
            if entity is None:
                return None
            if status is not None:
                entity.status = status
            if summary_details is not None:
                entity.summary_details = dict(summary_details)
            if metadata_details is not None:
                entity.metadata_details = dict(metadata_details)
            if error_message is not None:
                entity.error_message = error_message
            if completed_at is not None:
                entity.completed_at = completed_at
            session.add(entity)
            session.flush()
            return map_evaluation_run_entity_to_record(entity)

    def mark_failed(
        self,
        *,
        run_id: str,
        error_message: str,
        metadata_details: dict[str, Any] | None = None,
    ) -> EvaluationRunRecord | None:
        return self.update_run(
            run_id=run_id,
            status="failed",
            error_message=error_message,
            metadata_details=metadata_details,
            completed_at=utcnow(),
        )

    def list_runs(self) -> list[EvaluationRunRecord]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(EvaluationRunEntity).order_by(EvaluationRunEntity.created_at.desc())
            ).all()
            return [map_evaluation_run_entity_to_record(entity) for entity in entities]

    def get_run(self, *, run_id: str) -> EvaluationRunRecord | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(EvaluationRunEntity).where(EvaluationRunEntity.run_id == run_id)
            )
            if entity is None:
                return None
            return map_evaluation_run_entity_to_record(entity)

    def count_runs(self) -> int:
        with self._database_runtime.session_scope() as session:
            value = session.scalar(select(func.count()).select_from(EvaluationRunEntity))
            return int(value or 0)

    def list_recent_statuses(self, *, limit: int = 5) -> list[EvaluationRunStatusSummary]:
        with self._database_runtime.session_scope() as session:
            statement: Select[EvaluationRunEntity] = (
                select(EvaluationRunEntity)
                .order_by(EvaluationRunEntity.created_at.desc())
                .limit(limit)
            )
            entities = session.scalars(statement).all()
            return [map_evaluation_run_entity_to_status_summary(entity) for entity in entities]
