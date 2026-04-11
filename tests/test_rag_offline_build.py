from __future__ import annotations

import unittest
from unittest.mock import patch

from app.context.policies.tokenizer import CharacterTokenCounter
from app.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResult
from app.rag.ingestion.chunker import StructuredTokenChunker
from app.rag.ingestion.cleaner import DocumentCleaner
from app.rag.ingestion.parser import DocumentParser
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline
from app.rag.models import KnowledgeChunk, KnowledgeDocument
from app.rag.retrieval.vector_store import InMemoryVectorStore


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "deterministic-build-test"

    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            vectors.append(
                [
                    float(len(lowered)),
                    float(lowered.count("law")),
                    float(lowered.count("policy")),
                    1.0,
                ]
            )
        return EmbeddingResult(
            vectors=vectors,
            model=model or "build-test-model",
            dimensions=4,
        )


class FailingEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "failing-build-test"

    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        del texts, model
        raise RuntimeError("embedding unavailable")


class EmptyChunker:
    def chunk_document(
        self,
        document: KnowledgeDocument,
        *,
        chunk_token_size: int,
        overlap_token_size: int,
        embedding_model: str,
    ) -> list[KnowledgeChunk]:
        del document, chunk_token_size, overlap_token_size, embedding_model
        return []


class RAGOfflineBuildTests(unittest.TestCase):
    def _build_pipeline(
        self,
        *,
        embedding_provider: BaseEmbeddingProvider | None = None,
        chunker: StructuredTokenChunker | EmptyChunker | None = None,
    ) -> KnowledgeIngestionPipeline:
        return KnowledgeIngestionPipeline(
            parser=DocumentParser(),
            cleaner=DocumentCleaner(),
            chunker=chunker or StructuredTokenChunker(token_counter=CharacterTokenCounter()),
            embedding_provider=embedding_provider or DeterministicEmbeddingProvider(),
            vector_store=InMemoryVectorStore(),
            embedding_model="deterministic-v1",
            chunk_token_size=40,
            overlap_token_size=8,
            embedding_batch_size=2,
            chunk_strategy_version="structure-token-overlap-v1",
            embedding_model_version="deterministic-v1",
        )

    def test_build_generates_metadata_and_propagates_versions_to_chunks(self) -> None:
        pipeline = self._build_pipeline()
        document = DocumentParser.parse_text(
            content="# Law\n\nlaw policy baseline",
            document_id="doc-law-1",
            title="Law One",
            source_type="raw_text",
        )

        result = pipeline.build_documents(
            documents=[document],
            version_id="v1",
        )

        self.assertEqual(result.metadata.version_id, "v1")
        self.assertEqual(result.metadata.build_mode, "full")
        self.assertEqual(result.metadata.chunk_strategy_version, "structure-token-overlap-v1")
        self.assertEqual(result.metadata.embedding_model_version, "deterministic-v1")
        self.assertGreater(result.statistics.processed_document_count, 0)
        self.assertEqual(result.statistics.chunk_count, result.statistics.upserted_count)
        self.assertTrue(result.quality_gate.passed)
        first_chunk_metadata = result.ingestion_results[0].chunks[0].metadata
        self.assertEqual(first_chunk_metadata["version_id"], "v1")
        self.assertEqual(first_chunk_metadata["chunk_strategy_version"], "structure-token-overlap-v1")
        self.assertEqual(first_chunk_metadata["embedding_model_version"], "deterministic-v1")
        self.assertTrue(first_chunk_metadata["build_id"])

    def test_incremental_and_partial_rebuild_constraints(self) -> None:
        pipeline = self._build_pipeline()
        document_one = DocumentParser.parse_text(
            content="law baseline one",
            document_id="doc-1",
            title="Doc One",
            source_type="raw_text",
        )
        document_two = DocumentParser.parse_text(
            content="law baseline two",
            document_id="doc-2",
            title="Doc Two",
            source_type="raw_text",
        )

        first_build = pipeline.build_documents(
            documents=[document_one, document_two],
            version_id="v1",
        )
        second_build = pipeline.build_documents(
            documents=[document_one, document_two],
            version_id="v2",
            previous_manifest=first_build.manifest,
        )
        third_build = pipeline.build_documents(
            documents=[document_one, document_two],
            version_id="v3",
            previous_manifest=second_build.manifest,
            force_rebuild_document_ids=["doc-2"],
        )

        self.assertEqual(second_build.metadata.build_mode, "incremental")
        self.assertEqual(second_build.statistics.processed_document_count, 0)
        self.assertEqual(second_build.statistics.skipped_document_count, 2)
        self.assertEqual(third_build.metadata.build_mode, "partial")
        self.assertEqual(third_build.statistics.processed_document_count, 1)
        self.assertEqual(third_build.statistics.skipped_document_count, 1)
        self.assertEqual(third_build.ingestion_results[0].document.document_id, "doc-2")

    def test_build_quality_gate_catches_failure_and_reports_observability(self) -> None:
        pipeline = self._build_pipeline(embedding_provider=FailingEmbeddingProvider())
        document = DocumentParser.parse_text(
            content="law baseline",
            document_id="doc-fail",
            title="Doc Fail",
            source_type="raw_text",
        )

        with patch("app.rag.ingestion.pipeline.log_report") as mocked_log_report:
            result = pipeline.build_documents(
                documents=[document],
                version_id="v1",
                max_failure_ratio=0.0,
            )

        self.assertFalse(result.quality_gate.passed)
        self.assertIn("failure_ratio_exceeded", result.quality_gate.failed_rules)
        logged_events = [call.args[0] for call in mocked_log_report.call_args_list]
        self.assertIn("rag.offline_build.started", logged_events)
        self.assertIn("rag.offline_build.document.failed", logged_events)
        self.assertIn("rag.offline_build.quality_gate.failed", logged_events)
        self.assertIn("rag.offline_build.completed", logged_events)

    def test_build_quality_gate_catches_empty_chunk_ratio(self) -> None:
        pipeline = self._build_pipeline(chunker=EmptyChunker())
        document = DocumentParser.parse_text(
            content="law baseline",
            document_id="doc-empty",
            title="Doc Empty",
            source_type="raw_text",
        )

        result = pipeline.build_documents(
            documents=[document],
            version_id="v-empty",
            max_empty_chunk_ratio=0.0,
        )

        self.assertFalse(result.quality_gate.passed)
        self.assertIn("empty_chunk_ratio_exceeded", result.quality_gate.failed_rules)


if __name__ == "__main__":
    unittest.main()
