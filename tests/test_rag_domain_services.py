from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.config import AppConfig
from app.context.policies.tokenizer import CharacterTokenCounter
from app.db import DatabaseRuntime, ensure_database_schema
from app.providers.embeddings.deterministic_provider import DeterministicEmbeddingProvider
from app.rag.build_service import RAGBuildService
from app.rag.content_store import LocalRAGContentStore
from app.rag.document_service import RAGDocumentService
from app.rag.evaluation_service import RAGEvaluationService
from app.rag.ingestion.chunker import StructuredTokenChunker
from app.rag.ingestion.cleaner import DocumentCleaner
from app.rag.ingestion.parser import DocumentParser
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline
from app.rag.inspector_service import RAGInspectorService
from app.rag.repository import (
    BuildDocumentRepository,
    BuildTaskRepository,
    ChunkRepository,
    DocumentRepository,
    DocumentVersionRepository,
    EvaluationCaseRepository,
    EvaluationRunRepository,
)
from app.rag.retrieval.service import KnowledgeRetrievalService
from app.rag.retrieval.vector_store import InMemoryVectorStore
from app.rag.runtime import RAGRuntime
from app.services.runtime_service import RuntimeService


class RAGDomainServicePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self._db_path = Path(self._temp_dir.name) / "rag_control_plane.db"
        self._content_store_root = Path(self._temp_dir.name) / "storage"
        self._database_url = f"sqlite+pysqlite:///{self._db_path.as_posix()}"

        self._database_runtime = DatabaseRuntime(database_url=self._database_url)
        ensure_database_schema(self._database_runtime)

        self._document_repository = DocumentRepository(database_runtime=self._database_runtime)
        self._document_version_repository = DocumentVersionRepository(
            database_runtime=self._database_runtime
        )
        self._build_task_repository = BuildTaskRepository(
            database_runtime=self._database_runtime
        )
        self._build_document_repository = BuildDocumentRepository(
            database_runtime=self._database_runtime
        )
        self._chunk_repository = ChunkRepository(database_runtime=self._database_runtime)
        self._evaluation_run_repository = EvaluationRunRepository(
            database_runtime=self._database_runtime
        )
        self._evaluation_case_repository = EvaluationCaseRepository(
            database_runtime=self._database_runtime
        )
        self._content_store = LocalRAGContentStore(root_path=self._content_store_root)

        self._vector_store = InMemoryVectorStore()
        self._embedding_provider = DeterministicEmbeddingProvider(dimension=64)
        self._pipeline = KnowledgeIngestionPipeline(
            parser=DocumentParser(),
            cleaner=DocumentCleaner(),
            chunker=StructuredTokenChunker(token_counter=CharacterTokenCounter()),
            embedding_provider=self._embedding_provider,
            vector_store=self._vector_store,
            embedding_model="deterministic-text-v1",
            chunk_token_size=80,
            overlap_token_size=16,
            chunk_strategy_version="structure-token-overlap-v1",
            embedding_model_version="deterministic-text-v1",
        )
        self._retrieval_service = KnowledgeRetrievalService(
            embedding_provider=self._embedding_provider,
            vector_store=self._vector_store,
            embedding_model="deterministic-text-v1",
            default_top_k=4,
        )
        self._rag_runtime = RAGRuntime(
            enabled=True,
            retrieval_service=self._retrieval_service,
            default_top_k=4,
        )
        self._app_config = AppConfig.from_env(load_dotenv_file=False)

        self.document_service = RAGDocumentService(
            document_repository=self._document_repository,
            document_version_repository=self._document_version_repository,
            content_store=self._content_store,
            parser=DocumentParser(),
            cleaner=DocumentCleaner(),
        )
        self.build_service = RAGBuildService(
            document_version_repository=self._document_version_repository,
            build_task_repository=self._build_task_repository,
            build_document_repository=self._build_document_repository,
            chunk_repository=self._chunk_repository,
            content_store=self._content_store,
            pipeline=self._pipeline,
            vector_store=self._vector_store,
        )
        self.inspector_service = RAGInspectorService(
            app_config=self._app_config,
            rag_runtime=self._rag_runtime,
            retrieval_service=self._retrieval_service,
            document_repository=self._document_repository,
            document_version_repository=self._document_version_repository,
            build_task_repository=self._build_task_repository,
            build_document_repository=self._build_document_repository,
            chunk_repository=self._chunk_repository,
            content_store=self._content_store,
            vector_store=self._vector_store,
        )
        self.evaluation_service = RAGEvaluationService(
            evaluation_run_repository=self._evaluation_run_repository,
            evaluation_case_repository=self._evaluation_case_repository,
            inspector_service=self.inspector_service,
            document_service=self.document_service,
        )
        self.runtime_service = RuntimeService(
            app_config=self._app_config,
            document_repository=self._document_repository,
            chunk_repository=self._chunk_repository,
            build_task_repository=self._build_task_repository,
            evaluation_run_repository=self._evaluation_run_repository,
        )

    def tearDown(self) -> None:
        self._database_runtime.dispose()
        self._temp_dir.cleanup()

    def test_control_plane_persistence_flow_and_restart(self) -> None:
        uploaded_document = self.document_service.upload_document(
            content="# Law Baseline\n\nLaw baseline policy for testing persistence.",
            file_name="law.md",
            title="Law Baseline",
            tags=["law", "baseline"],
        )
        document_payload = self._document_repository.get_document(
            document_id=uploaded_document.document_id
        )
        self.assertIsNotNone(document_payload)

        latest_version_id = str(document_payload["latest_version_id"])
        version_payload = self._document_version_repository.get_version(
            version_id=latest_version_id
        )
        self.assertIsNotNone(version_payload)
        raw_file_path = self._content_store.root_path / version_payload["raw_storage_path"]
        normalized_file_path = (
            self._content_store.root_path / version_payload["normalized_storage_path"]
        )
        self.assertTrue(raw_file_path.exists())
        self.assertTrue(normalized_file_path.exists())

        build_detail = self.build_service.create_build()
        self.assertEqual(build_detail["metadata"]["status"], "succeeded")
        build_id = str(build_detail["metadata"]["build_id"])

        persisted_build = self._build_task_repository.get_task(build_id=build_id)
        self.assertIsNotNone(persisted_build)
        self.assertEqual(persisted_build["status"], "succeeded")

        document_chunks = self.inspector_service.list_document_chunks(uploaded_document.document_id)
        self.assertIsNotNone(document_chunks)
        self.assertGreater(len(document_chunks), 0)
        chunk_id = str(document_chunks[0]["chunk_id"])
        vector_detail = self.inspector_service.get_chunk_vector_detail(chunk_id=chunk_id)
        self.assertIsNotNone(vector_detail)
        self.assertTrue(vector_detail["found"])
        self.assertEqual(vector_detail["vector_point_id"], chunk_id)
        self.assertGreater(vector_detail["vector_dimension"], 0)

        run_result = self.evaluation_service.create_evaluation_run(
            dataset_id="rag-eval",
            version_id="v1",
            build_id=build_id,
            samples=[
                {
                    "sample_id": "sample-1",
                    "query_text": "law baseline policy",
                    "top_k": 4,
                    "retrieval_label": {
                        "expected_document_ids": [uploaded_document.document_id],
                        "min_recall": 0.0,
                    },
                    "citation_label": {
                        "expected_document_ids": [uploaded_document.document_id],
                        "min_recall": 0.0,
                        "min_precision": 0.0,
                    },
                    "answer_label": {
                        "required_terms": [],
                        "forbidden_terms": [],
                        "min_required_term_hit_ratio": 0.0,
                        "max_forbidden_term_hit_count": 0,
                    },
                    "metadata": {"source": "integration_test"},
                }
            ],
            run_metadata={"source": "integration_test"},
        )
        self.assertEqual(run_result.metadata["status"], "succeeded")
        self.assertEqual(run_result.metadata["build_id"], build_id)
        self.assertEqual(self._evaluation_run_repository.count_runs(), 1)
        self.assertEqual(
            len(self._evaluation_case_repository.list_cases_by_run_id(run_id=run_result.run_id)),
            1,
        )

        runtime_summary = self.runtime_service.get_runtime_summary()
        self.assertEqual(runtime_summary["document_count"], 1)
        self.assertGreaterEqual(runtime_summary["chunk_count"], 1)
        self.assertEqual(runtime_summary["build_count"], 1)
        self.assertEqual(runtime_summary["evaluation_run_count"], 1)
        self.assertEqual(len(runtime_summary["recent_build_statuses"]), 1)
        self.assertEqual(len(runtime_summary["recent_evaluation_statuses"]), 1)

        restarted_runtime = DatabaseRuntime(database_url=self._database_url)
        ensure_database_schema(restarted_runtime)
        try:
            restarted_document_repository = DocumentRepository(
                database_runtime=restarted_runtime
            )
            restarted_chunk_repository = ChunkRepository(database_runtime=restarted_runtime)
            restarted_build_repository = BuildTaskRepository(database_runtime=restarted_runtime)
            restarted_run_repository = EvaluationRunRepository(
                database_runtime=restarted_runtime
            )
            restarted_runtime_service = RuntimeService(
                app_config=self._app_config,
                document_repository=restarted_document_repository,
                chunk_repository=restarted_chunk_repository,
                build_task_repository=restarted_build_repository,
                evaluation_run_repository=restarted_run_repository,
            )
            restarted_summary = restarted_runtime_service.get_runtime_summary()
            self.assertEqual(restarted_summary["document_count"], 1)
            self.assertEqual(restarted_summary["build_count"], 1)
            self.assertEqual(restarted_summary["evaluation_run_count"], 1)
        finally:
            restarted_runtime.dispose()

