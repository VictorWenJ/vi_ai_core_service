"""Knowledge document domain service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.observability.log_until import log_report
from app.rag.ingestion.parser import DocumentParser
from app.rag.models import KnowledgeChunk, KnowledgeDocument, OfflineBuildResult
from app.rag.state import RAGControlState


class RAGDocumentService:
    """Manage uploaded documents and chunk snapshots for control-plane APIs."""

    def __init__(
        self,
        *,
        state: RAGControlState,
        parser: DocumentParser | None = None,
    ) -> None:
        self._state = state
        self._parser = parser or DocumentParser()

    def upload_document(
        self,
        *,
        content: str,
        file_name: str,
        title: str | None = None,
        document_id: str | None = None,
        source_type: str | None = None,
        jurisdiction: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("上传文档内容不能为空。")
        resolved_source_type = source_type or self._resolve_source_type_from_file_name(file_name)
        resolved_title = (title or "").strip() or Path(file_name).stem or "untitled"
        document = DocumentParser.parse_text(
            content=normalized_content,
            title=resolved_title,
            source_type=resolved_source_type,
            document_id=document_id,
            origin_uri=file_name,
            file_name=file_name,
            jurisdiction=jurisdiction,
            domain=domain,
            tags=tags or [],
            metadata=dict(metadata or {}),
        )
        with self._state.lock:
            self._state.documents[document.document_id] = document
            self._state.document_chunk_ids.setdefault(document.document_id, [])
        log_report(
            "knowledge.document.uploaded",
            {
                "document_id": document.document_id,
                "title": document.title,
                "source_type": document.source_type,
                "file_name": document.file_name,
            },
        )
        return document

    def list_documents(self) -> list[dict[str, Any]]:
        with self._state.lock:
            items = []
            for document in self._state.documents.values():
                chunk_ids = self._state.document_chunk_ids.get(document.document_id, [])
                items.append(
                    {
                        "document_id": document.document_id,
                        "title": document.title,
                        "source_type": document.source_type,
                        "origin_uri": document.origin_uri,
                        "file_name": document.file_name,
                        "jurisdiction": document.jurisdiction,
                        "domain": document.domain,
                        "tags": list(document.tags),
                        "effective_at": document.effective_at,
                        "updated_at": document.updated_at,
                        "visibility": document.visibility,
                        "metadata": dict(document.metadata),
                        "chunk_count": len(chunk_ids),
                    }
                )
            return sorted(items, key=lambda item: item["updated_at"] or "", reverse=True)

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        with self._state.lock:
            document = self._state.documents.get(document_id)
            if document is None:
                return None
            chunk_ids = self._state.document_chunk_ids.get(document.document_id, [])
            return {
                "document_id": document.document_id,
                "title": document.title,
                "source_type": document.source_type,
                "content": document.content,
                "origin_uri": document.origin_uri,
                "file_name": document.file_name,
                "jurisdiction": document.jurisdiction,
                "domain": document.domain,
                "tags": list(document.tags),
                "effective_at": document.effective_at,
                "updated_at": document.updated_at,
                "visibility": document.visibility,
                "metadata": dict(document.metadata),
                "chunk_count": len(chunk_ids),
            }

    def list_document_chunks(self, document_id: str) -> list[dict[str, Any]] | None:
        with self._state.lock:
            if document_id not in self._state.documents:
                return None
            chunk_ids = self._state.document_chunk_ids.get(document_id, [])
            chunks = [
                self._state.chunks[chunk_id]
                for chunk_id in chunk_ids
                if chunk_id in self._state.chunks
            ]
            return [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "embedding_model": chunk.embedding_model,
                    "chunk_text_preview": self.snippet(chunk.chunk_text, max_chars=220),
                    "metadata": dict(chunk.metadata),
                }
                for chunk in sorted(chunks, key=lambda item: item.chunk_index)
            ]

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        with self._state.lock:
            chunk = self._state.chunks.get(chunk_id)
            if chunk is None:
                return None
            return {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "embedding_model": chunk.embedding_model,
                "chunk_text": chunk.chunk_text,
                "metadata": dict(chunk.metadata),
            }

    def clone_documents_for_build(self) -> list[KnowledgeDocument]:
        with self._state.lock:
            return [self.clone_document(document) for document in self._state.documents.values()]

    def sync_from_build_result(self, build_result: OfflineBuildResult) -> None:
        with self._state.lock:
            for ingestion_result in build_result.ingestion_results:
                document = ingestion_result.document
                self._state.documents[document.document_id] = document
                old_chunk_ids = self._state.document_chunk_ids.get(document.document_id, [])
                for chunk_id in old_chunk_ids:
                    self._state.chunks.pop(chunk_id, None)
                new_chunk_ids: list[str] = []
                for chunk in ingestion_result.chunks:
                    self._state.chunks[chunk.chunk_id] = chunk
                    new_chunk_ids.append(chunk.chunk_id)
                self._state.document_chunk_ids[document.document_id] = new_chunk_ids

    def list_document_entities(self) -> list[KnowledgeDocument]:
        with self._state.lock:
            return [self.clone_document(document) for document in self._state.documents.values()]

    def count_documents(self) -> int:
        with self._state.lock:
            return len(self._state.documents)

    def count_chunks(self) -> int:
        with self._state.lock:
            return len(self._state.chunks)

    @staticmethod
    def _resolve_source_type_from_file_name(file_name: str) -> str:
        suffix = Path(file_name).suffix.lower()
        if suffix == ".md":
            return "markdown_file"
        if suffix == ".txt":
            return "text_file"
        if suffix == ".pdf":
            return "pdf_file"
        return "raw_text"

    @staticmethod
    def snippet(text: str, *, max_chars: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= max_chars:
            return normalized
        if max_chars <= 3:
            return normalized[:max_chars]
        return f"{normalized[: max_chars - 3]}..."

    @staticmethod
    def clone_document(document: KnowledgeDocument) -> KnowledgeDocument:
        return KnowledgeDocument(
            document_id=document.document_id,
            title=document.title,
            source_type=document.source_type,
            content=document.content,
            origin_uri=document.origin_uri,
            file_name=document.file_name,
            jurisdiction=document.jurisdiction,
            domain=document.domain,
            tags=list(document.tags),
            effective_at=document.effective_at,
            updated_at=document.updated_at,
            visibility=document.visibility,
            metadata=dict(document.metadata),
        )

    @staticmethod
    def clone_chunk(chunk: KnowledgeChunk) -> KnowledgeChunk:
        return KnowledgeChunk(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            chunk_text=chunk.chunk_text,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            embedding_model=chunk.embedding_model,
            metadata=dict(chunk.metadata),
        )

