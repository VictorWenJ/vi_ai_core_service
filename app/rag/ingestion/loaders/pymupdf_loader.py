"""基于 LangChain PyMuPDFLoader 的 PDF 加载器。"""

from __future__ import annotations

from pathlib import Path

from app.rag.ingestion.loaders.base import LoadedDocument
from app.rag.ingestion.loaders.langchain_loader_adapter import LangChainLoaderAdapter


class PyMuPDFDocumentLoader:
    """通过 LangChain 社区 loader 读取 PDF。"""

    def __init__(self) -> None:
        self._adapter = LangChainLoaderAdapter()

    def load(self, file_path: str | Path) -> LoadedDocument:
        def _factory(resolved_file_path: str):
            try:
                from langchain_community.document_loaders import PyMuPDFLoader
            except ImportError as exc:  # pragma: no cover - 由环境依赖决定
                raise RuntimeError(
                    "PDF loader requires 'langchain-community' and 'pymupdf'."
                ) from exc
            return PyMuPDFLoader(resolved_file_path)

        return self._adapter.load(
            file_path=file_path,
            loader_factory=_factory,
            source_type="pdf_file",
        )

