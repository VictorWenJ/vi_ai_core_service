from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.rag.ingestion.loaders.base import LoadedDocument
from app.rag.ingestion.loaders.langchain_loader_adapter import LangChainLoaderAdapter
from app.rag.ingestion.loaders.pymupdf_loader import PyMuPDFDocumentLoader


class _FakeLangChainDocument:
    def __init__(self, page_content: str, metadata: dict[str, object] | None = None) -> None:
        self.page_content = page_content
        self.metadata = dict(metadata or {})


class _FakeLangChainLoader:
    def __init__(self, documents: list[_FakeLangChainDocument]) -> None:
        self._documents = documents

    def load(self) -> list[_FakeLangChainDocument]:
        return list(self._documents)


class RAGLoaderAdapterTests(unittest.TestCase):
    def test_langchain_loader_adapter_converts_documents(self) -> None:
        adapter = LangChainLoaderAdapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%fake\n")
            loaded = adapter.load(
                file_path=pdf_path,
                loader_factory=lambda _: _FakeLangChainLoader(
                    [
                        _FakeLangChainDocument("page one", {"page": 1}),
                        _FakeLangChainDocument("page two", {"source": "stub"}),
                    ]
                ),
                source_type="pdf_file",
            )

        self.assertEqual(loaded.source_type, "pdf_file")
        self.assertEqual(loaded.file_name, "sample.pdf")
        self.assertEqual(loaded.text, "page one\n\npage two")
        self.assertEqual(loaded.metadata["page"], 1)
        self.assertEqual(loaded.metadata["source"], "stub")

    def test_pymupdf_loader_delegates_to_langchain_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "report.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%fake\n")
            with patch(
                "app.rag.ingestion.loaders.pymupdf_loader.LangChainLoaderAdapter.load",
                return_value=LoadedDocument(
                    text="pdf body",
                    title="report",
                    source_type="pdf_file",
                    origin_uri=str(pdf_path),
                    file_name="report.pdf",
                    metadata={"page_count": 1},
                ),
            ) as mocked_load:
                loader = PyMuPDFDocumentLoader()
                loaded = loader.load(pdf_path)

        self.assertEqual(loaded.text, "pdf body")
        self.assertEqual(loaded.source_type, "pdf_file")
        self.assertEqual(loaded.metadata["page_count"], 1)
        mocked_load.assert_called_once()


if __name__ == "__main__":
    unittest.main()

