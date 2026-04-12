"""chunks 持久化访问。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from app.db.session import DatabaseRuntime
from app.rag.repository._utils import copy_json_dict, datetime_to_iso
from app.rag.repository.models import ChunkEntity


class ChunkRepository:
    """chunk 元数据访问仓储。"""

    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self._database_runtime = database_runtime

    def add_records(self, *, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not records:
            return []
        with self._database_runtime.session_scope() as session:
            entities: list[ChunkEntity] = []
            for record in records:
                entity = ChunkEntity(
                    chunk_id=str(record["chunk_id"]),
                    build_id=str(record["build_id"]),
                    document_id=str(record["document_id"]),
                    document_version_id=str(record["document_version_id"]),
                    chunk_index=int(record["chunk_index"]),
                    token_count=int(record["token_count"]),
                    start_offset=record.get("start_offset"),
                    end_offset=record.get("end_offset"),
                    chunk_text_hash=str(record["chunk_text_hash"]),
                    chunk_preview=str(record["chunk_preview"]),
                    embedding_model_name=str(record["embedding_model_name"]),
                    vector_dimension=int(record["vector_dimension"]),
                    vector_collection=str(record["vector_collection"]),
                    vector_point_id=str(record["vector_point_id"]),
                    metadata_details=dict(record.get("metadata_details") or {}),
                )
                entities.append(entity)
            session.add_all(entities)
            session.flush()
            return [self._to_payload(entity) for entity in entities]

    def list_by_document_id(self, *, document_id: str) -> list[dict[str, Any]]:
        with self._database_runtime.session_scope() as session:
            entities = session.scalars(
                select(ChunkEntity)
                .where(ChunkEntity.document_id == document_id)
                .order_by(ChunkEntity.chunk_index.asc())
            ).all()
            return [self._to_payload(entity) for entity in entities]

    def get_chunk(self, *, chunk_id: str) -> dict[str, Any] | None:
        with self._database_runtime.session_scope() as session:
            entity = session.scalar(
                select(ChunkEntity).where(ChunkEntity.chunk_id == chunk_id)
            )
            if entity is None:
                return None
            return self._to_payload(entity)

    def count_chunks(self) -> int:
        with self._database_runtime.session_scope() as session:
            value = session.scalar(select(func.count()).select_from(ChunkEntity))
            return int(value or 0)

    @staticmethod
    def _to_payload(entity: ChunkEntity) -> dict[str, Any]:
        return {
            "chunk_id": entity.chunk_id,
            "build_id": entity.build_id,
            "document_id": entity.document_id,
            "document_version_id": entity.document_version_id,
            "chunk_index": entity.chunk_index,
            "token_count": entity.token_count,
            "start_offset": entity.start_offset,
            "end_offset": entity.end_offset,
            "chunk_text_hash": entity.chunk_text_hash,
            "chunk_preview": entity.chunk_preview,
            "embedding_model_name": entity.embedding_model_name,
            "vector_dimension": entity.vector_dimension,
            "vector_collection": entity.vector_collection,
            "vector_point_id": entity.vector_point_id,
            "metadata_details": copy_json_dict(entity.metadata_details),
            "created_at": datetime_to_iso(entity.created_at),
        }

