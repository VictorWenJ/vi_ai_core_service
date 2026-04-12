"""build_tasks 持久化访问。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select

from app.db.session import DatabaseRuntime
from app.rag.repository._utils import copy_json_dict, datetime_to_iso, utcnow
from app.rag.repository.models import BuildTaskEntity


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
    ) -> dict[str, Any]:
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
            return self._to_payload(entity)

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
    ) -> dict[str, Any] | None:
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
            return self._to_payload(entity)

    def touch_failed(
        self,
        *,
        build_id: str,
        error_message: str,
        statistics_details: dict[str, Any] | None = None,
        quality_gate_details: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return self.update_task(
            build_id=build_id,
            status="failed",
            error_message=error_message,
            statistics_details=statistics_details,
            quality_gate_details=quality_gate_details,
            completed_at=utcnow(),
        )

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(BuildTaskEntity).order_by(BuildTaskEntity.created_at.desc())
            ).all()
            return [self._to_payload(entity) for entity in entities]

    def get_task(self, *, build_id: str) -> dict[str, Any] | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(BuildTaskEntity).where(BuildTaskEntity.build_id == build_id)
            )
            if entity is None:
                return None
            return self._to_payload(entity)

    def count_tasks(self) -> int:
        with self._database_runtime.session_scope() as session:
            value = session.scalar(select(func.count()).select_from(BuildTaskEntity))
            return int(value or 0)

    def list_recent_statuses(self, *, limit: int = 5) -> list[dict[str, Any]]:
        with self._database_runtime.session_scope() as session:
            statement: Select[BuildTaskEntity] = (
                select(BuildTaskEntity)
                .order_by(BuildTaskEntity.created_at.desc())
                .limit(limit)
            )
            entities = session.scalars(statement).all()
            return [
                {
                    "build_id": entity.build_id,
                    "status": entity.status,
                    "created_at": datetime_to_iso(entity.created_at),
                    "completed_at": datetime_to_iso(entity.completed_at),
                }
                for entity in entities
            ]

    @staticmethod
    def _to_payload(entity: BuildTaskEntity) -> dict[str, Any]:
        return {
            "build_id": entity.build_id,
            "build_version_id": entity.build_version_id,
            "status": entity.status,
            "chunk_strategy_name": entity.chunk_strategy_name,
            "chunk_strategy_details": copy_json_dict(entity.chunk_strategy_details),
            "embedding_model_name": entity.embedding_model_name,
            "manifest_details": copy_json_dict(entity.manifest_details),
            "statistics_details": copy_json_dict(entity.statistics_details),
            "quality_gate_details": copy_json_dict(entity.quality_gate_details),
            "error_message": entity.error_message,
            "started_at": datetime_to_iso(entity.started_at),
            "completed_at": datetime_to_iso(entity.completed_at),
            "created_at": datetime_to_iso(entity.created_at),
        }

