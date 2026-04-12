"""Docling loader 预留扩展点。"""

from __future__ import annotations

from pathlib import Path

from app.rag.ingestion.loaders.base import LoadedDocument


class DoclingDocumentLoader:
    """预留 Docling 接入点，当前阶段不作为默认 loader。"""

    def load(self, file_path: str | Path) -> LoadedDocument:
        del file_path
        raise NotImplementedError(
            "Docling loader is reserved for future extension and not enabled in current phase."
        )

