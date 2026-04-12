"""documents 持久化访问。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, select

from app.db.session import DatabaseRuntime
from app.rag.repository._utils import copy_json_list, datetime_to_iso, utcnow
from app.rag.repository.models import ChunkEntity, DocumentEntity


class DocumentRepository:
    """文档主表访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def upsert_document(
        self,
        *,
        document_id: str,
        title: str,
        source_type: str,
        origin_uri: str | None,
        file_name: str | None,
        jurisdiction: str | None,
        domain: str | None,
        visibility: str,
        tags_details: list[str],
        status: str,
        latest_version_id: str | None,
    ) -> dict[str, Any]:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(DocumentEntity).where(DocumentEntity.document_id == document_id)
            )
            if entity is None:
                entity = DocumentEntity(
                    document_id=document_id,
                    title=title,
                    source_type=source_type,
                    origin_uri=origin_uri,
                    file_name=file_name,
                    jurisdiction=jurisdiction,
                    domain=domain,
                    visibility=visibility,
                    tags_details=list(tags_details),
                    status=status,
                    latest_version_id=latest_version_id,
                )
                session.add(entity)
            else:
                entity.title = title
                entity.source_type = source_type
                entity.origin_uri = origin_uri
                entity.file_name = file_name
                entity.jurisdiction = jurisdiction
                entity.domain = domain
                entity.visibility = visibility
                entity.tags_details = list(tags_details)
                entity.status = status
                entity.latest_version_id = latest_version_id
                entity.updated_at = utcnow()
            session.flush()
            return self._to_payload(entity)

    def set_latest_version_id(self, *, document_id: str, latest_version_id: str) -> None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(DocumentEntity).where(DocumentEntity.document_id == document_id)
            )
            if entity is None:
                return
            entity.latest_version_id = latest_version_id
            entity.updated_at = utcnow()
            session.add(entity)

    def list_documents(self) -> list[dict[str, Any]]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(DocumentEntity).order_by(DocumentEntity.updated_at.desc())
            ).all()
            return [self._to_payload(entity) for entity in entities]

    def get_document(self, *, document_id: str) -> dict[str, Any] | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(DocumentEntity).where(DocumentEntity.document_id == document_id)
            )
            if entity is None:
                return None
            return self._to_payload(entity)

    def count_documents(self) -> int:
        with self._database_runtime.session_scope() as session:
            value = session.scalar(select(func.count()).select_from(DocumentEntity))
            return int(value or 0)

    def count_chunks(self) -> int:
        with self._database_runtime.session_scope() as session:
            value = session.scalar(select(func.count()).select_from(ChunkEntity))
            return int(value or 0)

    def get_chunk_counts_by_document_ids(self, *, document_ids: list[str]) -> dict[str, int]:
        if not document_ids:
            return {}
        with self._database_runtime.session_scope() as session:
            statement: Select[tuple[str, int]] = (
                select(ChunkEntity.document_id, func.count())
                .where(ChunkEntity.document_id.in_(document_ids))
                .group_by(ChunkEntity.document_id)
            )
            rows = session.execute(statement).all()
            return {str(document_id): int(chunk_count) for document_id, chunk_count in rows}

    @staticmethod
    def _to_payload(entity: DocumentEntity) -> dict[str, Any]:
        return {
            "document_id": entity.document_id,
            "title": entity.title,
            "source_type": entity.source_type,
            "origin_uri": entity.origin_uri,
            "file_name": entity.file_name,
            "jurisdiction": entity.jurisdiction,
            "domain": entity.domain,
            "visibility": entity.visibility,
            "tags_details": copy_json_list(entity.tags_details),
            "status": entity.status,
            "latest_version_id": entity.latest_version_id,
            "created_at": datetime_to_iso(entity.created_at),
            "updated_at": datetime_to_iso(entity.updated_at),
        }

