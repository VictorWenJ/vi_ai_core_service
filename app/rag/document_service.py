"""Knowledge document domain service."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.observability.log_until import log_report
from app.rag.content_store.local_store import LocalRAGContentStore
from app.rag.ingestion.cleaner import DocumentCleaner
from app.rag.ingestion.parser import DocumentParser
from app.rag.models import KnowledgeDocument, compute_content_hash
from app.rag.repository.document_repository import DocumentRepository
from app.rag.repository.document_version_repository import DocumentVersionRepository


class RAGDocumentService:
    """负责文档上传、解析、清洗与持久化。"""

    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        document_version_repository: DocumentVersionRepository,
        content_store: LocalRAGContentStore,
        parser: DocumentParser | None = None,
        cleaner: DocumentCleaner | None = None,
    ) -> None:
        self._document_repository = document_repository
        self._document_version_repository = document_version_repository
        self._content_store = content_store
        self._parser = parser or DocumentParser()
        self._cleaner = cleaner or DocumentCleaner()

    def upload_document(
        self,
        *,
        content: str,
        file_name: str,
        origin_uri: str | None = None,
        title: str | None = None,
        document_id: str | None = None,
        source_type: str | None = None,
        jurisdiction: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        raw_content = content.strip()
        if not raw_content:
            raise ValueError("上传文档内容不能为空。")

        resolved_source_type = source_type or self._resolve_source_type_from_file_name(file_name)
        resolved_title = (title or "").strip() or file_name.rsplit(".", 1)[0] or "untitled"

        parsed_document = self._parser.parse_text(
            content=raw_content,
            title=resolved_title,
            source_type=resolved_source_type,
            document_id=document_id,
            origin_uri=origin_uri,
            file_name=file_name,
            jurisdiction=jurisdiction,
            domain=domain,
            tags=tags or [],
            metadata=dict(metadata or {}),
        )
        normalized_text = self._cleaner.clean(parsed_document.content)
        if not normalized_text.strip():
            raise ValueError("清洗后的文档内容为空，无法入库。")
        parsed_document.content = normalized_text

        resolved_document_id = parsed_document.document_id
        content_hash = compute_content_hash(raw_content)
        normalized_text_hash = compute_content_hash(normalized_text)
        hash_algorithm = "sha1"

        # 同一逻辑文档内容 hash 一致时，直接复用已有版本，不重复创建。
        existing_version = self._document_version_repository.find_version_by_content_hash(
            document_id=resolved_document_id,
            content_hash=content_hash,
            hash_algorithm=hash_algorithm,
        )
        log_report("RAGDocumentService.upload_document.existing_version", existing_version)

        if existing_version is not None:
            reused_version_id = str(existing_version["version_id"])
            self._document_repository.upsert_document(
                document_id=resolved_document_id,
                title=parsed_document.title,
                source_type=parsed_document.source_type,
                origin_uri=parsed_document.origin_uri,
                file_name=parsed_document.file_name,
                jurisdiction=parsed_document.jurisdiction,
                domain=parsed_document.domain,
                visibility=parsed_document.visibility,
                tags_details=list(parsed_document.tags),
                status="active",
                latest_version_id=reused_version_id,
            )
            log_report(
                "knowledge.document.version_reused",
                {
                    "document_id": resolved_document_id,
                    "version_id": reused_version_id,
                    "content_hash": content_hash,
                    "hash_algorithm": hash_algorithm,
                },
            )
            return parsed_document

        version_no = self._document_version_repository.next_version_no(
            document_id=resolved_document_id
        )
        version_id = f"ver_{uuid4().hex}"
        raw_bytes = raw_content.encode("utf-8")
        raw_storage_path = ""
        normalized_storage_path = ""

        try:
            raw_storage_path = self._content_store.save_raw_file(
                document_id=resolved_document_id,
                version_id=version_id,
                raw_bytes=raw_bytes,
            )
            normalized_storage_path = self._content_store.save_normalized_text(
                document_id=resolved_document_id,
                version_id=version_id,
                normalized_text=normalized_text,
            )

            self._document_version_repository.create_version(
                version_id=version_id,
                document_id=resolved_document_id,
                version_no=version_no,
                content_hash=content_hash,
                normalized_text_hash=normalized_text_hash,
                hash_algorithm=hash_algorithm,
                raw_storage_path=raw_storage_path,
                normalized_storage_path=normalized_storage_path,
                raw_file_size=len(raw_bytes),
                normalized_char_count=len(normalized_text),
                parser_name=type(self._parser).__name__,
                cleaner_name=type(self._cleaner).__name__,
                metadata_details={
                    "uploaded_via": "knowledge_api",
                    "source_file_name": file_name,
                },
            )
            self._document_repository.upsert_document(
                document_id=resolved_document_id,
                title=parsed_document.title,
                source_type=parsed_document.source_type,
                origin_uri=parsed_document.origin_uri,
                file_name=parsed_document.file_name,
                jurisdiction=parsed_document.jurisdiction,
                domain=parsed_document.domain,
                visibility=parsed_document.visibility,
                tags_details=list(parsed_document.tags),
                status="active",
                latest_version_id=version_id,
            )
        except Exception:
            if raw_storage_path or normalized_storage_path:
                self._content_store.delete_version_files(
                    document_id=resolved_document_id,
                    version_id=version_id,
                )
            raise

        log_report(
            "knowledge.document.uploaded",
            {
                "document_id": resolved_document_id,
                "version_id": version_id,
                "version_no": version_no,
                "title": parsed_document.title,
                "source_type": parsed_document.source_type,
                "file_name": parsed_document.file_name,
                "raw_storage_path": raw_storage_path,
                "normalized_storage_path": normalized_storage_path,
            },
        )
        return parsed_document

    def count_documents(self) -> int:
        """返回文档总数。"""
        return self._document_repository.count_documents()

    def list_document_entities(self) -> list[KnowledgeDocument]:
        """返回最新版本文档实体（供 build / evaluation 读取）。"""
        latest_versions = self._document_version_repository.list_latest_versions_for_build()
        entities: list[KnowledgeDocument] = []
        for item in latest_versions:
            document_payload = dict(item["document"])
            version_payload = dict(item["version"])
            normalized_text = self._content_store.read_normalized_text(
                storage_path=version_payload["normalized_storage_path"]
            )
            entities.append(
                KnowledgeDocument(
                    document_id=document_payload["document_id"],
                    title=document_payload["title"],
                    source_type=document_payload["source_type"],
                    content=normalized_text,
                    origin_uri=document_payload.get("origin_uri"),
                    file_name=document_payload.get("file_name"),
                    jurisdiction=document_payload.get("jurisdiction"),
                    domain=document_payload.get("domain"),
                    tags=list(document_payload.get("tags_details") or []),
                    updated_at=document_payload.get("updated_at"),
                    visibility=document_payload.get("visibility") or "internal",
                    metadata=dict(version_payload.get("metadata_details") or {}),
                )
            )
        return entities

    @staticmethod
    def _resolve_source_type_from_file_name(file_name: str) -> str:
        lower_name = file_name.lower()
        if lower_name.endswith(".md"):
            return "markdown_file"
        if lower_name.endswith(".txt"):
            return "text_file"
        if lower_name.endswith(".pdf"):
            return "pdf_file"
        return "raw_text"
