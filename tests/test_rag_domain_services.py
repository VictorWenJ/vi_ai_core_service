from __future__ import annotations

import unittest

from app.config import AppConfig
from app.context.policies.tokenizer import CharacterTokenCounter
from app.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResult
from app.rag.build_service import RAGBuildService
from app.rag.document_service import RAGDocumentService
from app.rag.evaluation_service import RAGEvaluationService
from app.rag.ingestion.chunker import StructuredTokenChunker
from app.rag.ingestion.cleaner import DocumentCleaner
from app.rag.ingestion.parser import DocumentParser
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline
from app.rag.inspector_service import RAGInspectorService
from app.rag.retrieval.service import KnowledgeRetrievalService
from app.rag.retrieval.vector_store import InMemoryVectorStore
from app.rag.runtime import RAGRuntime
from app.rag.state import RAGControlState
from app.services.runtime_service import RuntimeService


class _StubEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "stub"

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
            model=model or "stub-embedding",
            dimensions=4,
        )


class RAGDomainServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        app_config = AppConfig.from_env(load_dotenv_file=False)
        self.state = RAGControlState()
        self.document_service = RAGDocumentService(state=self.state, parser=DocumentParser())
        self.vector_store = InMemoryVectorStore()
        self.embedding_provider = _StubEmbeddingProvider()
        self.retrieval_service = KnowledgeRetrievalService(
            embedding_provider=self.embedding_provider,
            vector_store=self.vector_store,
            embedding_model=app_config.rag_config.embedding_model,
            default_top_k=app_config.rag_config.retrieval_top_k,
            default_score_threshold=app_config.rag_config.score_threshold,
        )
        self.pipeline = KnowledgeIngestionPipeline(
            parser=DocumentParser(),
            cleaner=DocumentCleaner(),
            chunker=StructuredTokenChunker(token_counter=CharacterTokenCounter()),
            embedding_provider=self.embedding_provider,
            vector_store=self.vector_store,
            embedding_model=app_config.rag_config.embedding_model,
            chunk_token_size=app_config.rag_config.chunk_token_size,
            overlap_token_size=app_config.rag_config.chunk_overlap_token_size,
            chunk_strategy_version="structure-token-overlap-v1",
            embedding_model_version=app_config.rag_config.embedding_model,
        )
        self.build_service = RAGBuildService(
            state=self.state,
            document_service=self.document_service,
            pipeline=self.pipeline,
        )
        self.inspector_service = RAGInspectorService(
            app_config=app_config,
            rag_runtime=RAGRuntime.disabled(default_top_k=app_config.rag_config.retrieval_top_k),
            retrieval_service=self.retrieval_service,
            document_service=self.document_service,
        )
        self.evaluation_service = RAGEvaluationService(
            state=self.state,
            inspector_service=self.inspector_service,
            document_service=self.document_service,
        )
        self.runtime_service = RuntimeService(
            app_config=app_config,
            document_service=self.document_service,
            build_service=self.build_service,
            evaluation_service=self.evaluation_service,
        )

    def test_document_and_build_services(self) -> None:
        uploaded = self.document_service.upload_document(
            content="# Law Policy\n\nThe policy baseline applies.",
            file_name="law.md",
            title="Law Policy",
        )
        self.assertEqual(uploaded.source_type, "markdown_file")

        build_result = self.build_service.create_build(version_id="v-domain-test")
        self.assertEqual(build_result.metadata.version_id, "v-domain-test")
        self.assertGreaterEqual(build_result.statistics.processed_document_count, 1)
        self.assertTrue(self.build_service.get_build(build_result.metadata.build_id))

    def test_inspector_service_retrieval_debug(self) -> None:
        self.document_service.upload_document(
            content="# Law Policy\n\nThe policy baseline applies.",
            file_name="law.md",
            title="Law Policy",
        )
        self.build_service.create_build(version_id="v-inspector")

        debug_payload = self.inspector_service.retrieval_debug(query_text="law policy")
        self.assertEqual(debug_payload["status"], "succeeded")
        self.assertGreaterEqual(len(debug_payload["hits"]), 1)
        self.assertGreaterEqual(len(debug_payload["citations"]), 1)

    def test_evaluation_and_runtime_services(self) -> None:
        self.document_service.upload_document(
            content="# Law Policy\n\nThe policy baseline applies.",
            file_name="law.md",
            title="Law Policy",
        )
        self.build_service.create_build(version_id="v-eval")

        run_result = self.evaluation_service.create_evaluation_run(
            dataset_id="dataset-domain",
            version_id="v1",
            samples=[],
            run_metadata={"trigger": "test"},
        )
        self.assertEqual(run_result.dataset_id, "dataset-domain")
        self.assertGreaterEqual(len(run_result.cases), 1)
        self.assertGreaterEqual(len(self.evaluation_service.list_evaluation_runs()), 1)
        self.assertIsNotNone(self.evaluation_service.get_evaluation_run(run_result.run_id))

        runtime_summary = self.runtime_service.get_runtime_summary()
        self.assertEqual(runtime_summary["service"], "vi_ai_core_service")
        self.assertGreaterEqual(runtime_summary["document_count"], 1)
        self.assertGreaterEqual(runtime_summary["build_count"], 1)
        self.assertGreaterEqual(runtime_summary["evaluation_run_count"], 1)


if __name__ == "__main__":
    unittest.main()

