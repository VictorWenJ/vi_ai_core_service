from __future__ import annotations

import unittest

from app.providers.embedding_base import BaseEmbeddingProvider, EmbeddingResult
from app.rag.citation.formatter import build_citations
from app.rag.models import KnowledgeChunk, KnowledgeDocument, RetrievedChunk
from app.rag.retrieval.service import KnowledgeRetrievalService
from app.rag.retrieval.vector_store import InMemoryVectorStore
from app.rag.runtime import RAGRuntime


class KeywordEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "keyword"

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
                    float("law" in lowered),
                    float("finance" in lowered),
                    float(len(lowered) % 7),
                ]
            )
        return EmbeddingResult(
            vectors=vectors,
            model=model or "keyword-v1",
            dimensions=3,
        )


class FailingRetrievalService:
    def retrieve(self, *, query_text: str, top_k: int, metadata_filter=None):
        del query_text, top_k, metadata_filter
        raise RuntimeError("qdrant unavailable")


class RAGRetrievalTests(unittest.TestCase):
    def test_inmemory_index_upsert_and_query_with_metadata_filter(self) -> None:
        store = InMemoryVectorStore()
        document_law = KnowledgeDocument(
            document_id="doc-law",
            title="Law Doc",
            source_type="raw_text",
            content="law article",
            domain="law",
        )
        document_finance = KnowledgeDocument(
            document_id="doc-finance",
            title="Finance Doc",
            source_type="raw_text",
            content="finance article",
            domain="finance",
        )
        law_chunk = KnowledgeChunk(
            chunk_id="chk-law",
            document_id="doc-law",
            chunk_text="law section",
            chunk_index=0,
            token_count=10,
            embedding_model="keyword-v1",
        )
        finance_chunk = KnowledgeChunk(
            chunk_id="chk-fin",
            document_id="doc-finance",
            chunk_text="finance section",
            chunk_index=0,
            token_count=10,
            embedding_model="keyword-v1",
        )

        store.upsert(document=document_law, chunks=[law_chunk], vectors=[[1.0, 0.0, 1.0]])
        store.upsert(
            document=document_finance,
            chunks=[finance_chunk],
            vectors=[[0.0, 1.0, 1.0]],
        )

        law_results = store.query(
            query_vector=[1.0, 0.0, 1.0],
            top_k=5,
            metadata_filter={"domain": "law"},
        )
        finance_results = store.query(
            query_vector=[0.0, 1.0, 1.0],
            top_k=5,
            metadata_filter={"domain": "finance"},
        )

        self.assertEqual(len(law_results), 1)
        self.assertEqual(law_results[0].document_id, "doc-law")
        self.assertEqual(len(finance_results), 1)
        self.assertEqual(finance_results[0].document_id, "doc-finance")

    def test_retrieval_service_returns_citation_ready_result(self) -> None:
        embedding_provider = KeywordEmbeddingProvider()
        store = InMemoryVectorStore()
        retrieval_service = KnowledgeRetrievalService(
            embedding_provider=embedding_provider,
            vector_store=store,
            embedding_model="keyword-v1",
            default_top_k=4,
        )

        document = KnowledgeDocument(
            document_id="doc-law",
            title="Law Handbook",
            source_type="raw_text",
            content="law policy",
            origin_uri="file:///law.md",
            domain="law",
        )
        chunk = KnowledgeChunk(
            chunk_id="chk-1",
            document_id="doc-law",
            chunk_text="law policy baseline and obligations",
            chunk_index=0,
            token_count=34,
            embedding_model="keyword-v1",
        )
        vectors = embedding_provider.embed_texts([chunk.chunk_text], model="keyword-v1").vectors
        store.upsert(document=document, chunks=[chunk], vectors=vectors)

        result = retrieval_service.retrieve(
            query_text="law question",
            metadata_filter={"domain": "law"},
            top_k=3,
        )

        self.assertEqual(result.trace.status, "succeeded")
        self.assertEqual(result.trace.hit_count, 1)
        self.assertEqual(len(result.citations), 1)
        self.assertEqual(result.citations[0].document_id, "doc-law")
        self.assertIn("[knowledge_block]", result.knowledge_block or "")

    def test_citation_id_is_stable_for_same_document_chunk_pair(self) -> None:
        chunk = RetrievedChunk(
            chunk_id="chk-1",
            document_id="doc-1",
            text="citation snippet source text",
            score=0.88,
            title="Doc One",
            origin_uri="file:///doc-1.md",
            source_type="markdown_file",
            jurisdiction=None,
            domain=None,
            effective_at=None,
            updated_at="2026-04-10T00:00:00+00:00",
            metadata={},
        )
        first = build_citations([chunk])[0]
        second = build_citations([chunk])[0]
        self.assertEqual(first.citation_id, second.citation_id)
        self.assertEqual(first.snippet, second.snippet)

    def test_runtime_returns_degraded_when_retrieval_fails(self) -> None:
        runtime = RAGRuntime(
            enabled=True,
            retrieval_service=FailingRetrievalService(),  # type: ignore[arg-type]
            default_top_k=4,
        )

        result = runtime.retrieve_for_chat(
            query_text="law question",
            metadata_filter={"domain": "law"},
        )

        self.assertEqual(result.trace.status, "degraded")
        self.assertEqual(result.citations, [])
        self.assertIsNone(result.knowledge_block)

    def test_runtime_returns_disabled_when_feature_is_off(self) -> None:
        runtime = RAGRuntime.disabled(default_top_k=2)
        result = runtime.retrieve_for_chat(query_text="anything")
        self.assertEqual(result.trace.status, "disabled")
        self.assertEqual(result.trace.top_k, 2)
        self.assertEqual(result.citations, [])
