from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.rag.models import KnowledgeDocument
from app.server import app


class _FakeSummary:
    def to_dict(self) -> dict[str, float]:
        return {
            "sample_count": 1,
            "retrieval_pass_count": 1,
            "citation_pass_count": 1,
            "answer_pass_count": 1,
            "overall_pass_count": 1,
            "retrieval_pass_rate": 1.0,
            "citation_pass_rate": 1.0,
            "answer_pass_rate": 1.0,
            "overall_pass_rate": 1.0,
            "average_retrieval_recall": 1.0,
            "average_citation_recall": 1.0,
            "average_answer_hit_ratio": 1.0,
        }


class _FakeCase:
    def to_dict(self) -> dict[str, object]:
        return {
            "sample_id": "sample-1",
            "retrieval": {"recall": 1.0, "passed": True},
            "citation": {"recall": 1.0, "precision": 1.0, "passed": True},
            "answer": {"required_term_hit_ratio": 1.0, "passed": True},
            "retrieval_status": "succeeded",
            "passed": True,
            "resolved_top_k": 4,
        }


class _FakeRunResult:
    def __init__(self) -> None:
        self.run_id = "run-1"
        self.dataset_id = "dataset-1"
        self.dataset_version_id = "v1"
        self.started_at = "2026-04-12T00:00:00+00:00"
        self.completed_at = "2026-04-12T00:01:00+00:00"
        self.summary = _FakeSummary()
        self.metadata = {"trigger": "test"}
        self.cases = [_FakeCase()]


class _FakeBuildResult:
    def __init__(self) -> None:
        self._payload = {
            "metadata": {
                "build_id": "build-1",
                "version_id": "v1",
                "chunk_strategy_version": "structure-token-overlap-v1",
                "embedding_model_version": "deterministic-v1",
                "build_mode": "full",
                "started_at": "2026-04-12T00:00:00+00:00",
                "completed_at": "2026-04-12T00:01:00+00:00",
            },
            "statistics": {
                "requested_document_count": 1,
                "processed_document_count": 1,
                "skipped_document_count": 0,
                "failed_document_count": 0,
                "chunk_count": 2,
                "upserted_count": 2,
                "embedding_batch_count": 1,
                "latency_ms": 12.3,
            },
            "quality_gate": {
                "passed": True,
                "failed_rules": [],
                "failure_ratio": 0.0,
                "empty_chunk_ratio": 0.0,
                "max_failure_ratio": 0.0,
                "max_empty_chunk_ratio": 0.0,
            },
            "manifest": {
                "version_id": "v1",
                "generated_at": "2026-04-12T00:01:00+00:00",
                "records": {
                    "doc-1": {
                        "document_id": "doc-1",
                        "content_hash": "abc",
                        "built_at": "2026-04-12T00:01:00+00:00",
                    }
                },
            },
            "ingestion_results": [
                {
                    "document_id": "doc-1",
                    "chunk_count": 2,
                    "trace": {"status": "succeeded"},
                }
            ],
        }

    def to_dict(self) -> dict[str, object]:
        return self._payload


class FakeInternalConsoleService:
    def __init__(self) -> None:
        self.document = KnowledgeDocument(
            document_id="doc-1",
            title="Law Baseline",
            source_type="markdown_file",
            content="# Law\n\nbaseline",
            file_name="law.md",
            metadata={"uploaded_via": "test"},
        )
        self.build_result = _FakeBuildResult()
        self.run_result = _FakeRunResult()

    def upload_document(self, **kwargs):
        del kwargs
        return self.document

    def create_build(self, **kwargs):
        del kwargs
        return self.build_result

    def list_builds(self):
        return [self.build_result]

    def get_build(self, build_id: str):
        return self.build_result if build_id == "build-1" else None

    def list_documents(self):
        return [
            {
                "document_id": "doc-1",
                "title": "Law Baseline",
                "source_type": "markdown_file",
                "origin_uri": "law.md",
                "file_name": "law.md",
                "jurisdiction": None,
                "domain": None,
                "tags": [],
                "effective_at": None,
                "updated_at": self.document.updated_at,
                "visibility": "internal",
                "metadata": {"uploaded_via": "test"},
                "chunk_count": 2,
            }
        ]

    def get_document(self, document_id: str):
        if document_id != "doc-1":
            return None
        return {
            "document_id": "doc-1",
            "title": "Law Baseline",
            "source_type": "markdown_file",
            "content": "# Law\n\nbaseline",
            "origin_uri": "law.md",
            "file_name": "law.md",
            "jurisdiction": None,
            "domain": None,
            "tags": [],
            "effective_at": None,
            "updated_at": self.document.updated_at,
            "visibility": "internal",
            "metadata": {"uploaded_via": "test"},
            "chunk_count": 2,
        }

    def list_document_chunks(self, document_id: str):
        if document_id != "doc-1":
            return None
        return [
            {
                "chunk_id": "chk-1",
                "document_id": "doc-1",
                "chunk_index": 0,
                "token_count": 10,
                "embedding_model": "deterministic-v1",
                "chunk_text_preview": "preview",
                "metadata": {},
            }
        ]

    def get_chunk(self, chunk_id: str):
        if chunk_id != "chk-1":
            return None
        return {
            "chunk_id": "chk-1",
            "document_id": "doc-1",
            "chunk_index": 0,
            "token_count": 10,
            "embedding_model": "deterministic-v1",
            "chunk_text": "chunk full text",
            "metadata": {},
        }

    def get_chunk_vector_detail(self, *, chunk_id: str):
        if chunk_id != "chk-1":
            return None
        return {
            "chunk_id": "chk-1",
            "vector_point_id": "chk-1",
            "vector_collection": "vi_ai_knowledge_chunks",
            "found": True,
            "vector": [0.1, 0.2, 0.3],
            "vector_dimension": 3,
            "payload": {"document_id": "doc-1"},
        }

    def retrieval_debug(self, **kwargs):
        del kwargs
        return {
            "query_text": "law",
            "top_k": 4,
            "status": "succeeded",
            "hits": [
                {
                    "chunk_id": "chk-1",
                    "document_id": "doc-1",
                    "score": 0.9,
                    "title": "Law Baseline",
                    "source_type": "markdown_file",
                    "origin_uri": "law.md",
                    "snippet": "snippet",
                    "metadata": {},
                }
            ],
            "citations": [
                {
                    "citation_id": "c-1",
                    "document_id": "doc-1",
                    "chunk_id": "chk-1",
                    "title": "Law Baseline",
                    "snippet": "snippet",
                    "origin_uri": "law.md",
                    "source_type": "markdown_file",
                    "updated_at": "2026-04-12T00:00:00+00:00",
                    "metadata": {},
                }
            ],
            "trace": {"status": "succeeded", "hit_count": 1},
        }

    def create_evaluation_run(self, **kwargs):
        del kwargs
        return self.run_result

    def list_evaluation_runs(self):
        return [self.run_result]

    def get_evaluation_run(self, run_id: str):
        return self.run_result if run_id == "run-1" else None

    def get_runtime_summary(self):
        return {
            "service": "vi_ai_core_service",
            "default_provider": "openai",
            "rag_enabled": True,
            "embedding_provider": "deterministic",
            "embedding_model": "deterministic-v1",
            "retrieval_top_k": 4,
            "score_threshold": None,
            "chunk_token_size": 300,
            "chunk_overlap_token_size": 50,
            "document_count": 1,
            "chunk_count": 2,
            "build_count": 1,
            "evaluation_run_count": 1,
        }

    def get_runtime_config_summary(self):
        return {
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "default_model": "gpt-test",
                    "base_url": "https://api.openai.com/v1",
                    "timeout_seconds": 60.0,
                    "api_key_configured": True,
                }
            },
            "streaming": {"enabled": True},
            "rag": {"enabled": True, "qdrant_collection": "vi_ai_knowledge_chunks"},
        }

    def get_runtime_health(self):
        return {
            "status": "ok",
            "service": "vi_ai_core_service",
            "checked_at": "2026-04-12T00:02:00+00:00",
            "summary": self.get_runtime_summary(),
        }


class ConsoleAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.fake_service = FakeInternalConsoleService()
        self._patchers = [
            patch(
                "app.api.knowledge._get_document_service",
                return_value=self.fake_service,
            ),
            patch(
                "app.api.knowledge._get_build_service",
                return_value=self.fake_service,
            ),
            patch(
                "app.api.knowledge._get_inspector_service",
                return_value=self.fake_service,
            ),
            patch(
                "app.api.evaluation._get_evaluation_service",
                return_value=self.fake_service,
            ),
            patch(
                "app.api.runtime._get_runtime_service",
                return_value=self.fake_service,
            ),
        ]
        for patcher in self._patchers:
            patcher.start()

    def tearDown(self) -> None:
        for patcher in reversed(self._patchers):
            patcher.stop()

    def test_knowledge_ingest_and_build_apis(self) -> None:
        upload_response = self.client.post(
            "/knowledge/documents/upload",
            files={"file": ("law.md", "# Law\n\nbaseline", "text/markdown")},
        )
        self.assertEqual(upload_response.status_code, 200)
        self.assertEqual(upload_response.json()["document_id"], "doc-1")

        create_build_response = self.client.post("/knowledge/builds", json={})
        self.assertEqual(create_build_response.status_code, 200)
        self.assertEqual(
            create_build_response.json()["metadata"]["build_id"],
            "build-1",
        )

        list_builds_response = self.client.get("/knowledge/builds")
        self.assertEqual(list_builds_response.status_code, 200)
        self.assertEqual(len(list_builds_response.json()), 1)

        get_build_response = self.client.get("/knowledge/builds/build-1")
        self.assertEqual(get_build_response.status_code, 200)
        self.assertTrue(get_build_response.json()["quality_gate"]["passed"])

    def test_inspector_apis(self) -> None:
        list_docs_response = self.client.get("/knowledge/documents")
        self.assertEqual(list_docs_response.status_code, 200)
        self.assertEqual(list_docs_response.json()[0]["document_id"], "doc-1")

        get_doc_response = self.client.get("/knowledge/documents/doc-1")
        self.assertEqual(get_doc_response.status_code, 200)
        self.assertEqual(get_doc_response.json()["chunk_count"], 2)

        list_chunks_response = self.client.get("/knowledge/documents/doc-1/chunks")
        self.assertEqual(list_chunks_response.status_code, 200)
        self.assertEqual(list_chunks_response.json()[0]["chunk_id"], "chk-1")

        get_chunk_response = self.client.get("/knowledge/chunks/chk-1")
        self.assertEqual(get_chunk_response.status_code, 200)
        self.assertEqual(get_chunk_response.json()["document_id"], "doc-1")

        get_vector_response = self.client.get("/knowledge/chunks/chk-1/vector")
        self.assertEqual(get_vector_response.status_code, 200)
        self.assertTrue(get_vector_response.json()["found"])
        self.assertEqual(get_vector_response.json()["vector_point_id"], "chk-1")

        retrieval_debug_response = self.client.post(
            "/knowledge/retrieval/debug",
            json={"query_text": "law"},
        )
        self.assertEqual(retrieval_debug_response.status_code, 200)
        self.assertEqual(retrieval_debug_response.json()["status"], "succeeded")
        self.assertEqual(len(retrieval_debug_response.json()["hits"]), 1)

    def test_evaluation_apis(self) -> None:
        create_run_response = self.client.post(
            "/evaluation/rag/runs",
            json={"dataset_id": "dataset-1", "version_id": "v1", "samples": []},
        )
        self.assertEqual(create_run_response.status_code, 200)
        self.assertEqual(create_run_response.json()["run_id"], "run-1")

        list_runs_response = self.client.get("/evaluation/rag/runs")
        self.assertEqual(list_runs_response.status_code, 200)
        self.assertEqual(len(list_runs_response.json()), 1)

        get_run_response = self.client.get("/evaluation/rag/runs/run-1")
        self.assertEqual(get_run_response.status_code, 200)
        self.assertEqual(get_run_response.json()["case_count"], 1)

        list_cases_response = self.client.get("/evaluation/rag/runs/run-1/cases")
        self.assertEqual(list_cases_response.status_code, 200)
        self.assertEqual(len(list_cases_response.json()), 1)
        self.assertTrue(list_cases_response.json()[0]["passed"])

    def test_runtime_apis(self) -> None:
        summary_response = self.client.get("/runtime/summary")
        self.assertEqual(summary_response.status_code, 200)
        self.assertEqual(summary_response.json()["service"], "vi_ai_core_service")

        config_response = self.client.get("/runtime/config-summary")
        self.assertEqual(config_response.status_code, 200)
        self.assertEqual(config_response.json()["default_provider"], "openai")

        health_response = self.client.get("/runtime/health")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
