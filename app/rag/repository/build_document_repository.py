"""build_documents 持久化访问。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.db.session import DatabaseRuntime
from app.rag.repository._utils import datetime_to_iso
from app.rag.repository.models import BuildDocumentEntity


class BuildDocumentRepository:
    """构建任务文档关系访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def add_records(self, *, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not records:
            return []
        with self._database_runtime.session_scope() as session:
            entities: list[BuildDocumentEntity] = []
            for record in records:
                entity = BuildDocumentEntity(
                    build_id=str(record["build_id"]),
                    document_id=str(record["document_id"]),
                    document_version_id=str(record["document_version_id"]),
                    content_hash=str(record["content_hash"]),
                    action=str(record["action"]),
                    chunk_count=int(record.get("chunk_count", 0)),
                    vector_count=int(record.get("vector_count", 0)),
                    error_message=record.get("error_message"),
                )
                entities.append(entity)
            session.add_all(entities)
            session.flush()
            return [self._to_payload(entity) for entity in entities]

    def list_by_build_id(self, *, build_id: str) -> list[dict[str, Any]]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(BuildDocumentEntity)
                .where(BuildDocumentEntity.build_id == build_id)
                .order_by(BuildDocumentEntity.created_at.asc())
            ).all()
            return [self._to_payload(entity) for entity in entities]

    @staticmethod
    def _to_payload(entity: BuildDocumentEntity) -> dict[str, Any]:
        return {
            "build_id": entity.build_id,
            "document_id": entity.document_id,
            "document_version_id": entity.document_version_id,
            "content_hash": entity.content_hash,
            "action": entity.action,
            "chunk_count": entity.chunk_count,
            "vector_count": entity.vector_count,
            "error_message": entity.error_message,
            "created_at": datetime_to_iso(entity.created_at),
        }

