"""build_tasks 持久化访问。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select

from app.db.session import DatabaseRuntime
from app.rag.repository._utils import utcnow
from app.rag.repository.mappers import (
    map_build_task_entity_to_record,
    map_build_task_entity_to_status_summary,
)
from app.rag.repository.models import BuildTaskEntity
from app.rag.repository.read_models import BuildTaskRecord, BuildTaskStatusSummary


class BuildTaskRepository:
    """离线构建任务访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def create_task(
        self,
        *,
        build_id: str,
        build_version_id: str,
        status: str,
        chunk_strategy_name: str,
        chunk_strategy_details: dict[str, Any],
        embedding_model_name: str,
        manifest_details: dict[str, Any],
        statistics_details: dict[str, Any] | None = None,
        quality_gate_details: dict[str, Any] | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> BuildTaskRecord:
        with self._database_runtime.session_scope() as session:
            entity = BuildTaskEntity(
                build_id=build_id,
                build_version_id=build_version_id,
                status=status,
                chunk_strategy_name=chunk_strategy_name,
                chunk_strategy_details=dict(chunk_strategy_details),
                embedding_model_name=embedding_model_name,
                manifest_details=dict(manifest_details),
                statistics_details=dict(statistics_details or {}),
                quality_gate_details=dict(quality_gate_details or {}),
                error_message=error_message,
                started_at=started_at,
                completed_at=completed_at,
            )
            session.add(entity)
            session.flush()
            return map_build_task_entity_to_record(entity)

    def update_task(
        self,
        *,
        build_id: str,
        status: str | None = None,
        manifest_details: dict[str, Any] | None = None,
        statistics_details: dict[str, Any] | None = None,
        quality_gate_details: dict[str, Any] | None = None,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> BuildTaskRecord | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(BuildTaskEntity).where(BuildTaskEntity.build_id == build_id)
            )
            if entity is None:
                return None
            if status is not None:
                entity.status = status
            if manifest_details is not None:
                entity.manifest_details = dict(manifest_details)
            if statistics_details is not None:
                entity.statistics_details = dict(statistics_details)
            if quality_gate_details is not None:
                entity.quality_gate_details = dict(quality_gate_details)
            if error_message is not None:
                entity.error_message = error_message
            if completed_at is not None:
                entity.completed_at = completed_at
            session.add(entity)
            session.flush()
            return map_build_task_entity_to_record(entity)

    def touch_failed(
        self,
        *,
        build_id: str,
        error_message: str,
        statistics_details: dict[str, Any] | None = None,
        quality_gate_details: dict[str, Any] | None = None,
    ) -> BuildTaskRecord | None:
        return self.update_task(
            build_id=build_id,
            status="failed",
            error_message=error_message,
            statistics_details=statistics_details,
            quality_gate_details=quality_gate_details,
            completed_at=utcnow(),
        )

    def list_tasks(self) -> list[BuildTaskRecord]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(BuildTaskEntity).order_by(BuildTaskEntity.created_at.desc())
            ).all()
            return [map_build_task_entity_to_record(entity) for entity in entities]

    def get_task(self, *, build_id: str) -> BuildTaskRecord | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(BuildTaskEntity).where(BuildTaskEntity.build_id == build_id)
            )
            if entity is None:
                return None
            return map_build_task_entity_to_record(entity)

    def count_tasks(self) -> int:
        with self._database_runtime.session_scope() as session:
            value = session.scalar(select(func.count()).select_from(BuildTaskEntity))
            return int(value or 0)

    def list_recent_statuses(self, *, limit: int = 5) -> list[BuildTaskStatusSummary]:
        with self._database_runtime.session_scope() as session:
            statement: Select[BuildTaskEntity] = (
                select(BuildTaskEntity)
                .order_by(BuildTaskEntity.created_at.desc())
                .limit(limit)
            )
            entities = session.scalars(statement).all()
            return [map_build_task_entity_to_status_summary(entity) for entity in entities]
