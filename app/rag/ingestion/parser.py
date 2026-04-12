"""Document parser for ingestion pipeline."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.rag.ingestion.loaders.base import BaseDocumentLoader
from app.rag.ingestion.loaders.markdown_loader import MarkdownDocumentLoader
from app.rag.ingestion.loaders.pymupdf_loader import PyMuPDFDocumentLoader
from app.rag.ingestion.loaders.text_loader import TextDocumentLoader
from app.rag.models import KnowledgeDocument


class DocumentParser:
    """Parse raw text or local files into knowledge documents."""

    SUPPORTED_FILE_EXTENSIONS = {".txt", ".md", ".pdf"}

    def __init__(
        self,
        *,
        text_loader: BaseDocumentLoader | None = None,
        markdown_loader: BaseDocumentLoader | None = None,
        pdf_loader: BaseDocumentLoader | None = None,
    ) -> None:
        self._text_loader = text_loader or TextDocumentLoader()
        self._markdown_loader = markdown_loader or MarkdownDocumentLoader()
        self._pdf_loader = pdf_loader or PyMuPDFDocumentLoader()

    @staticmethod
    def parse_text(
            *,
        content: str,
        title: str | None = None,
        source_type: str = "raw_text",
        document_id: str | None = None,
        origin_uri: str | None = None,
        file_name: str | None = None,
        jurisdiction: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        effective_at: str | None = None,
        updated_at: str | None = None,
        visibility: str = "internal",
        metadata: dict | None = None,
    ) -> KnowledgeDocument:
        return KnowledgeDocument(
            document_id=document_id or f"doc_{uuid4().hex}",
            title=title or "untitled",
            source_type=source_type,
            content=content,
            origin_uri=origin_uri,
            file_name=file_name,
            jurisdiction=jurisdiction,
            domain=domain,
            tags=tags or [],
            effective_at=effective_at,
            updated_at=updated_at,
            visibility=visibility,
            metadata=dict(metadata or {}),
        )

    def parse_file(
        self,
        file_path: str | Path,
        *,
        source_type: str | None = None,
        document_id: str | None = None,
        title: str | None = None,
        jurisdiction: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        effective_at: str | None = None,
        updated_at: str | None = None,
        visibility: str = "internal",
        metadata: dict | None = None,
    ) -> KnowledgeDocument:
        path = Path(file_path).expanduser().resolve()
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FILE_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension '{suffix}'. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_FILE_EXTENSIONS))}."
            )
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        loader = self._resolve_loader(suffix)
        loaded_document = loader.load(path)
        resolved_source_type = source_type or loaded_document.source_type
        merged_metadata = {
            **dict(loaded_document.metadata or {}),
            **dict(metadata or {}),
        }
        return self.parse_text(
            content=loaded_document.text,
            title=title or loaded_document.title or path.stem,
            source_type=resolved_source_type,
            document_id=document_id,
            origin_uri=loaded_document.origin_uri or str(path),
            file_name=loaded_document.file_name or path.name,
            jurisdiction=jurisdiction,
            domain=domain,
            tags=tags,
            effective_at=effective_at,
            updated_at=updated_at,
            visibility=visibility,
            metadata=merged_metadata,
        )

    def _resolve_loader(self, suffix: str) -> BaseDocumentLoader:
        if suffix == ".txt":
            return self._text_loader
        if suffix == ".md":
            return self._markdown_loader
        if suffix == ".pdf":
            return self._pdf_loader
        raise ValueError(
            f"Unsupported file extension '{suffix}'. "
            f"Supported: {', '.join(sorted(self.SUPPORTED_FILE_EXTENSIONS))}."
        )
