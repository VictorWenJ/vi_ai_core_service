"""build_documents 持久化访问。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.db.session import DatabaseRuntime
from app.rag.repository.mappers import map_build_document_entity_to_record
from app.rag.repository.models import BuildDocumentEntity
from app.rag.repository.read_models import BuildDocumentRecord


class BuildDocumentRepository:
    """构建任务文档关系访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def add_records(self, *, records: list[dict[str, Any]]) -> list[BuildDocumentRecord]:
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
            return [map_build_document_entity_to_record(entity) for entity in entities]

    def list_by_build_id(self, *, build_id: str) -> list[BuildDocumentRecord]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(BuildDocumentEntity)
                .where(BuildDocumentEntity.build_id == build_id)
                .order_by(BuildDocumentEntity.created_at.asc())
            ).all()
            return [map_build_document_entity_to_record(entity) for entity in entities]
