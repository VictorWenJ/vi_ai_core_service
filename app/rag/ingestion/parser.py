"""Document parser for ingestion pipeline."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.rag.models import KnowledgeDocument


class DocumentParser:
    """Parse raw text or local files into knowledge documents."""

    SUPPORTED_FILE_EXTENSIONS = {".txt", ".md"}

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

        content = path.read_text(encoding="utf-8")
        resolved_source_type = source_type or ("markdown_file" if suffix == ".md" else "text_file")
        return self.parse_text(
            content=content,
            title=title or path.stem,
            source_type=resolved_source_type,
            document_id=document_id,
            origin_uri=str(path),
            file_name=path.name,
            jurisdiction=jurisdiction,
            domain=domain,
            tags=tags,
            effective_at=effective_at,
            updated_at=updated_at,
            visibility=visibility,
            metadata=metadata,
        )
