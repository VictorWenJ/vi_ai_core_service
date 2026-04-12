from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

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
from app.server import app
from app.services.runtime_service import RuntimeService


class RAGPersistenceAPIIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self._temp_dir.name) / "rag_control_plane_api.db"
        content_store_root = Path(self._temp_dir.name) / "storage"
        database_runtime = DatabaseRuntime(
            database_url=f"sqlite+pysqlite:///{db_path.as_posix()}",
        )
        ensure_database_schema(database_runtime)
        self._database_runtime = database_runtime

        document_repository = DocumentRepository(database_runtime=database_runtime)
        document_version_repository = DocumentVersionRepository(
            database_runtime=database_runtime
        )
        build_task_repository = BuildTaskRepository(database_runtime=database_runtime)
        build_document_repository = BuildDocumentRepository(database_runtime=database_runtime)
        chunk_repository = ChunkRepository(database_runtime=database_runtime)
        evaluation_run_repository = EvaluationRunRepository(database_runtime=database_runtime)
        evaluation_case_repository = EvaluationCaseRepository(database_runtime=database_runtime)
        content_store = LocalRAGContentStore(root_path=content_store_root)

        vector_store = InMemoryVectorStore()
        embedding_provider = DeterministicEmbeddingProvider(dimension=64)
        pipeline = KnowledgeIngestionPipeline(
            parser=DocumentParser(),
            cleaner=DocumentCleaner(),
            chunker=StructuredTokenChunker(token_counter=CharacterTokenCounter()),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            embedding_model="deterministic-text-v1",
            chunk_token_size=80,
            overlap_token_size=16,
            chunk_strategy_version="structure-token-overlap-v1",
            embedding_model_version="deterministic-text-v1",
        )
        retrieval_service = KnowledgeRetrievalService(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            embedding_model="deterministic-text-v1",
            default_top_k=4,
        )
        rag_runtime = RAGRuntime(
            enabled=True,
            retrieval_service=retrieval_service,
            default_top_k=4,
        )
        app_config = AppConfig.from_env(load_dotenv_file=False)

        self.document_service = RAGDocumentService(
            document_repository=document_repository,
            document_version_repository=document_version_repository,
            content_store=content_store,
            parser=DocumentParser(),
            cleaner=DocumentCleaner(),
        )
        self.build_service = RAGBuildService(
            document_version_repository=document_version_repository,
            build_task_repository=build_task_repository,
            build_document_repository=build_document_repository,
            chunk_repository=chunk_repository,
            content_store=content_store,
            pipeline=pipeline,
            vector_store=vector_store,
        )
        inspector_service = RAGInspectorService(
            app_config=app_config,
            rag_runtime=rag_runtime,
            retrieval_service=retrieval_service,
            document_repository=document_repository,
            document_version_repository=document_version_repository,
            build_task_repository=build_task_repository,
            build_document_repository=build_document_repository,
            chunk_repository=chunk_repository,
            content_store=content_store,
            vector_store=vector_store,
        )
        self.inspector_service = inspector_service
        self.evaluation_service = RAGEvaluationService(
            evaluation_run_repository=evaluation_run_repository,
            evaluation_case_repository=evaluation_case_repository,
            inspector_service=inspector_service,
            document_service=self.document_service,
        )
        self.runtime_service = RuntimeService(
            app_config=app_config,
            document_repository=document_repository,
            chunk_repository=chunk_repository,
            build_task_repository=build_task_repository,
            evaluation_run_repository=evaluation_run_repository,
        )

        self.client = TestClient(app)
        self._patchers = [
            patch("app.api.knowledge._get_document_service", return_value=self.document_service),
            patch("app.api.knowledge._get_build_service", return_value=self.build_service),
            patch("app.api.knowledge._get_inspector_service", return_value=self.inspector_service),
            patch(
                "app.api.evaluation._get_evaluation_service",
                return_value=self.evaluation_service,
            ),
            patch("app.api.runtime._get_runtime_service", return_value=self.runtime_service),
        ]
        for patcher in self._patchers:
            patcher.start()

    def tearDown(self) -> None:
        for patcher in reversed(self._patchers):
            patcher.stop()
        self._database_runtime.dispose()
        self._temp_dir.cleanup()

    def test_knowledge_evaluation_runtime_api_paths_with_persistence_backend(self) -> None:
        upload_response = self.client.post(
            "/knowledge/documents/upload",
            files={"file": ("law.md", "# Law\n\npersistence baseline", "text/markdown")},
        )
        self.assertEqual(upload_response.status_code, 200)
        document_id = upload_response.json()["document_id"]

        create_build_response = self.client.post("/knowledge/builds", json={})
        self.assertEqual(create_build_response.status_code, 200)
        build_id = create_build_response.json()["metadata"]["build_id"]
        self.assertEqual(create_build_response.json()["metadata"]["status"], "succeeded")

        list_builds_response = self.client.get("/knowledge/builds")
        self.assertEqual(list_builds_response.status_code, 200)
        self.assertGreaterEqual(len(list_builds_response.json()), 1)

        get_build_response = self.client.get(f"/knowledge/builds/{build_id}")
        self.assertEqual(get_build_response.status_code, 200)
        self.assertEqual(get_build_response.json()["metadata"]["build_id"], build_id)

        list_documents_response = self.client.get("/knowledge/documents")
        self.assertEqual(list_documents_response.status_code, 200)
        self.assertGreaterEqual(len(list_documents_response.json()), 1)

        get_document_response = self.client.get(f"/knowledge/documents/{document_id}")
        self.assertEqual(get_document_response.status_code, 200)
        self.assertEqual(get_document_response.json()["document_id"], document_id)

        list_chunks_response = self.client.get(f"/knowledge/documents/{document_id}/chunks")
        self.assertEqual(list_chunks_response.status_code, 200)
        self.assertGreaterEqual(len(list_chunks_response.json()), 1)
        chunk_id = list_chunks_response.json()[0]["chunk_id"]

        get_chunk_response = self.client.get(f"/knowledge/chunks/{chunk_id}")
        self.assertEqual(get_chunk_response.status_code, 200)
        self.assertEqual(get_chunk_response.json()["chunk_id"], chunk_id)

        get_vector_response = self.client.get(f"/knowledge/chunks/{chunk_id}/vector")
        self.assertEqual(get_vector_response.status_code, 200)
        self.assertTrue(get_vector_response.json()["found"])
        self.assertEqual(get_vector_response.json()["vector_point_id"], chunk_id)

        retrieval_debug_response = self.client.post(
            "/knowledge/retrieval/debug",
            json={"query_text": "law persistence", "top_k": 4},
        )
        self.assertEqual(retrieval_debug_response.status_code, 200)
        self.assertEqual(retrieval_debug_response.json()["status"], "succeeded")

        create_run_response = self.client.post(
            "/evaluation/rag/runs",
            json={
                "dataset_id": "rag-eval",
                "version_id": "v1",
                "build_id": build_id,
                "samples": [
                    {
                        "sample_id": "sample-1",
                        "query_text": "law persistence",
                        "top_k": 4,
                        "retrieval_label": {
                            "expected_document_ids": [document_id],
                            "min_recall": 0.0,
                        },
                        "citation_label": {
                            "expected_document_ids": [document_id],
                            "min_recall": 0.0,
                            "min_precision": 0.0,
                        },
                        "answer_label": {
                            "required_terms": [],
                            "forbidden_terms": [],
                            "min_required_term_hit_ratio": 0.0,
                            "max_forbidden_term_hit_count": 0,
                        },
                        "metadata": {"source": "api-integration-test"},
                    }
                ],
            },
        )
        self.assertEqual(create_run_response.status_code, 200)
        run_id = create_run_response.json()["run_id"]
        self.assertEqual(create_run_response.json()["build_id"], build_id)

        list_runs_response = self.client.get("/evaluation/rag/runs")
        self.assertEqual(list_runs_response.status_code, 200)
        self.assertGreaterEqual(len(list_runs_response.json()), 1)

        get_run_response = self.client.get(f"/evaluation/rag/runs/{run_id}")
        self.assertEqual(get_run_response.status_code, 200)
        self.assertEqual(get_run_response.json()["run_id"], run_id)

        list_cases_response = self.client.get(f"/evaluation/rag/runs/{run_id}/cases")
        self.assertEqual(list_cases_response.status_code, 200)
        self.assertEqual(len(list_cases_response.json()), 1)

        runtime_summary_response = self.client.get("/runtime/summary")
        self.assertEqual(runtime_summary_response.status_code, 200)
        summary_payload = runtime_summary_response.json()
        self.assertEqual(summary_payload["document_count"], 1)
        self.assertEqual(summary_payload["build_count"], 1)
        self.assertEqual(summary_payload["evaluation_run_count"], 1)

        runtime_config_response = self.client.get("/runtime/config-summary")
        self.assertEqual(runtime_config_response.status_code, 200)
        self.assertIn("database", runtime_config_response.json())

        runtime_health_response = self.client.get("/runtime/health")
        self.assertEqual(runtime_health_response.status_code, 200)
        self.assertEqual(runtime_health_response.json()["status"], "ok")

