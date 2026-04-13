"""document_versions 持久化访问。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, select

from app.db.session import DatabaseRuntime
from app.rag.repository.mappers import (
    map_document_version_entity_to_record,
    map_latest_document_version_record,
)
from app.rag.repository.models import DocumentEntity, DocumentVersionEntity
from app.rag.repository.read_models import DocumentVersionRecord, LatestDocumentVersionRecord


class DocumentVersionRepository:
    """文档版本访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def next_version_no(self, *, document_id: str) -> int:
        with self._database_runtime.session_scope() as session:
            value = session.scalar(
                select(func.max(DocumentVersionEntity.version_no)).where(
                    DocumentVersionEntity.document_id == document_id
                )
            )
            return int(value or 0) + 1

    def create_version(
        self,
        *,
        version_id: str,
        document_id: str,
        version_no: int,
        content_hash: str,
        normalized_text_hash: str,
        hash_algorithm: str,
        raw_storage_path: str,
        normalized_storage_path: str,
        raw_file_size: int,
        normalized_char_count: int,
        parser_name: str,
        cleaner_name: str,
        metadata_details: dict[str, Any],
    ) -> DocumentVersionRecord:
        with self._database_runtime.session_scope() as session:
            entity = DocumentVersionEntity(
                version_id=version_id,
                document_id=document_id,
                version_no=version_no,
                content_hash=content_hash,
                normalized_text_hash=normalized_text_hash,
                hash_algorithm=hash_algorithm,
                raw_storage_path=raw_storage_path,
                normalized_storage_path=normalized_storage_path,
                raw_file_size=raw_file_size,
                normalized_char_count=normalized_char_count,
                parser_name=parser_name,
                cleaner_name=cleaner_name,
                metadata_details=dict(metadata_details),
            )
            session.add(entity)
            session.flush()
            return map_document_version_entity_to_record(entity)

    def find_version_by_content_hash(
        self,
        *,
        document_id: str,
        content_hash: str,
        hash_algorithm: str,
    ) -> DocumentVersionRecord | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(DocumentVersionEntity).where(
                    DocumentVersionEntity.document_id == document_id,
                    DocumentVersionEntity.content_hash == content_hash,
                    DocumentVersionEntity.hash_algorithm == hash_algorithm,
                )
            )
            if entity is None:
                return None
            return map_document_version_entity_to_record(entity)

    def count_versions(self, *, document_id: str | None = None) -> int:
        with self._database_runtime.session_scope() as session:
            statement = select(func.count()).select_from(DocumentVersionEntity)
            if document_id is not None:
                statement = statement.where(DocumentVersionEntity.document_id == document_id)
            value = session.scalar(statement)
            return int(value or 0)

    def get_version(self, *, version_id: str) -> DocumentVersionRecord | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(DocumentVersionEntity).where(
                    DocumentVersionEntity.version_id == version_id
                )
            )
            if entity is None:
                return None
            return map_document_version_entity_to_record(entity)

    def get_latest_version(self, *, document_id: str) -> DocumentVersionRecord | None:
        with self._database_runtime.session_scope() as session:
            document = session.scalar(
                select(DocumentEntity).where(DocumentEntity.document_id == document_id)
            )
            if document is None or not document.latest_version_id:
                return None
            version = session.scalar(
                select(DocumentVersionEntity).where(
                    DocumentVersionEntity.version_id == document.latest_version_id
                )
            )
            if version is None:
                return None
            return map_document_version_entity_to_record(version)

    def list_latest_versions_for_build(
        self,
        *,
        document_ids: list[str] | None = None,
    ) -> list[LatestDocumentVersionRecord]:
        with self._database_runtime.session_scope() as session:
            statement: Select[tuple[DocumentEntity, DocumentVersionEntity]] = select(
                DocumentEntity,
                DocumentVersionEntity,
            ).join(
                DocumentVersionEntity,
                DocumentEntity.latest_version_id == DocumentVersionEntity.version_id,
            )
            if document_ids:
                statement = statement.where(DocumentEntity.document_id.in_(document_ids))
            statement = statement.order_by(DocumentEntity.updated_at.desc())
            rows = session.execute(statement).all()
            payloads: list[LatestDocumentVersionRecord] = []
            for document_entity, version_entity in rows:
                payloads.append(
                    map_latest_document_version_record(document_entity, version_entity)
                )
            return payloads
