"""document_versions 持久化访问。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, select

from app.db.session import DatabaseRuntime
from app.rag.repository._utils import copy_json_dict, datetime_to_iso
from app.rag.repository.models import DocumentEntity, DocumentVersionEntity


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
    ) -> dict[str, Any]:
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
            return self._to_payload(entity)

    def get_version(self, *, version_id: str) -> dict[str, Any] | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(DocumentVersionEntity).where(
                    DocumentVersionEntity.version_id == version_id
                )
            )
            if entity is None:
                return None
            return self._to_payload(entity)

    def get_latest_version(self, *, document_id: str) -> dict[str, Any] | None:
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
            return self._to_payload(version)

    def list_latest_versions_for_build(
        self,
        *,
        document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
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
            payloads: list[dict[str, Any]] = []
            for document_entity, version_entity in rows:
                payloads.append(
                    {
                        "document": {
                            "document_id": document_entity.document_id,
                            "title": document_entity.title,
                            "source_type": document_entity.source_type,
                            "origin_uri": document_entity.origin_uri,
                            "file_name": document_entity.file_name,
                            "jurisdiction": document_entity.jurisdiction,
                            "domain": document_entity.domain,
                            "visibility": document_entity.visibility,
                            "tags_details": list(document_entity.tags_details or []),
                            "status": document_entity.status,
                            "latest_version_id": document_entity.latest_version_id,
                            "created_at": datetime_to_iso(document_entity.created_at),
                            "updated_at": datetime_to_iso(document_entity.updated_at),
                        },
                        "version": self._to_payload(version_entity),
                    }
                )
            return payloads

    @staticmethod
    def _to_payload(entity: DocumentVersionEntity) -> dict[str, Any]:
        return {
            "version_id": entity.version_id,
            "document_id": entity.document_id,
            "version_no": entity.version_no,
            "content_hash": entity.content_hash,
            "normalized_text_hash": entity.normalized_text_hash,
            "hash_algorithm": entity.hash_algorithm,
            "raw_storage_path": entity.raw_storage_path,
            "normalized_storage_path": entity.normalized_storage_path,
            "raw_file_size": entity.raw_file_size,
            "normalized_char_count": entity.normalized_char_count,
            "parser_name": entity.parser_name,
            "cleaner_name": entity.cleaner_name,
            "metadata_details": copy_json_dict(entity.metadata_details),
            "created_at": datetime_to_iso(entity.created_at),
        }

