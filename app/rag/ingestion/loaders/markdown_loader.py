"""Markdown 加载器。"""

from __future__ import annotations

from pathlib import Path

from app.rag.ingestion.loaders.base import LoadedDocument


class MarkdownDocumentLoader:
    """读取 UTF-8 markdown 文件。"""

    def load(self, file_path: str | Path) -> LoadedDocument:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        content = path.read_text(encoding="utf-8")
        return LoadedDocument(
            text=content,
            title=path.stem,
            source_type="markdown_file",
            origin_uri=str(path),
            file_name=path.name,
            metadata={},
        )

