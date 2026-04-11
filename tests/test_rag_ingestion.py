from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.context.policies.tokenizer import CharacterTokenCounter
from app.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResult
from app.rag.ingestion.chunker import StructuredTokenChunker
from app.rag.ingestion.cleaner import DocumentCleaner
from app.rag.ingestion.parser import DocumentParser
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline
from app.rag.models import KnowledgeDocument
from app.rag.retrieval.vector_store import InMemoryVectorStore


class StubEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "stub"

    def __init__(self, dimension: int = 4) -> None:
        self.dimension = dimension
        self.calls: list[list[str]] = []

    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        self.calls.append(list(texts))
        vectors: list[list[float]] = []
        for text in texts:
            text_len = float(len(text.strip()))
            vectors.append(
                [
                    text_len,
                    float(text.lower().count("law")),
                    float(text.lower().count("finance")),
                    1.0,
                ][: self.dimension]
            )
        return EmbeddingResult(
            vectors=vectors,
            model=model or "stub-embedding",
            dimensions=self.dimension,
        )


class RAGIngestionTests(unittest.TestCase):
    def test_document_parser_supports_text_and_local_files(self) -> None:
        parser = DocumentParser()

        from_text = parser.parse_text(
            content="hello world",
            title="inline-doc",
            source_type="raw_text",
        )
        self.assertEqual(from_text.title, "inline-doc")
        self.assertEqual(from_text.source_type, "raw_text")

        with tempfile.TemporaryDirectory() as temp_dir:
            txt_path = Path(temp_dir) / "a.txt"
            md_path = Path(temp_dir) / "b.md"
            txt_path.write_text("txt-content", encoding="utf-8")
            md_path.write_text("# heading\n\nmd-content", encoding="utf-8")

            from_txt = parser.parse_file(str(txt_path))
            from_md = parser.parse_file(str(md_path))

        self.assertEqual(from_txt.source_type, "text_file")
        self.assertEqual(from_md.source_type, "markdown_file")
        self.assertEqual(from_md.file_name, "b.md")

    def test_document_cleaner_normalizes_whitespace(self) -> None:
        cleaner = DocumentCleaner()
        cleaned = cleaner.clean("line-1   \r\n\r\n\r\nline-2\t \r\n")
        self.assertEqual(cleaned, "line-1\n\nline-2")

    def test_chunker_produces_overlap_and_document_metadata(self) -> None:
        chunker = StructuredTokenChunker(token_counter=CharacterTokenCounter())
        document = KnowledgeDocument(
            document_id="doc-1",
            title="Doc One",
            source_type="raw_text",
            content=(
                "This is a very long paragraph for chunk overlap validation. "
                "It should be split into multiple parts with repeated overlap."
            ),
            origin_uri="file:///doc-1.md",
            domain="policy",
            tags=["phase6"],
        )

        chunks = chunker.chunk_document(
            document,
            chunk_token_size=40,
            overlap_token_size=8,
            embedding_model="deterministic-text-v1",
        )

        self.assertGreater(len(chunks), 1)
        first_chunk_tail = chunks[0].chunk_text[-8:].strip()
        self.assertTrue(first_chunk_tail)
        self.assertIn(first_chunk_tail, chunks[1].chunk_text)
        self.assertEqual(chunks[0].metadata["title"], "Doc One")
        self.assertEqual(chunks[0].metadata["domain"], "policy")
        self.assertEqual(chunks[0].embedding_model, "deterministic-text-v1")

    def test_ingestion_pipeline_runs_parser_cleaner_chunk_embedding_and_upsert(self) -> None:
        embedding_provider = StubEmbeddingProvider(dimension=4)
        vector_store = InMemoryVectorStore()
        pipeline = KnowledgeIngestionPipeline(
            parser=DocumentParser(),
            cleaner=DocumentCleaner(),
            chunker=StructuredTokenChunker(token_counter=CharacterTokenCounter()),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            embedding_model="stub-embedding",
            chunk_token_size=35,
            overlap_token_size=6,
            embedding_batch_size=2,
        )

        result = pipeline.ingest_text(
            content="# Law\n\nlaw policy baseline\n\n# Finance\n\nfinance baseline",
            title="Policy Doc",
            source_type="raw_text",
            document_id="doc-policy",
            domain="law",
        )

        self.assertEqual(result.document.document_id, "doc-policy")
        self.assertEqual(result.trace.status, "succeeded")
        self.assertGreater(result.trace.chunk_count, 0)
        self.assertEqual(result.trace.upserted_count, result.trace.chunk_count)
        self.assertGreater(result.trace.embedding_batch_count, 0)
        self.assertEqual(result.trace.embedding_dimension, 4)
        self.assertGreater(len(embedding_provider.calls), 0)
