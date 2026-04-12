from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.db import DatabaseRuntime, ensure_database_schema
from app.rag.repository import (
    BuildDocumentRepository,
    BuildTaskRepository,
    ChunkRepository,
    DocumentRepository,
    DocumentVersionRepository,
    EvaluationCaseRepository,
    EvaluationRunRepository,
)
from app.rag.repository._utils import utcnow


class RAGRepositoryPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self._db_path = Path(self._temp_dir.name) / "rag_control_plane.db"
        self._database_runtime = DatabaseRuntime(
            database_url=f"sqlite+pysqlite:///{self._db_path.as_posix()}",
        )
        ensure_database_schema(self._database_runtime)

        self.document_repository = DocumentRepository(
            database_runtime=self._database_runtime
        )
        self.document_version_repository = DocumentVersionRepository(
            database_runtime=self._database_runtime
        )
        self.build_task_repository = BuildTaskRepository(
            database_runtime=self._database_runtime
        )
        self.build_document_repository = BuildDocumentRepository(
            database_runtime=self._database_runtime
        )
        self.chunk_repository = ChunkRepository(database_runtime=self._database_runtime)
        self.evaluation_run_repository = EvaluationRunRepository(
            database_runtime=self._database_runtime
        )
        self.evaluation_case_repository = EvaluationCaseRepository(
            database_runtime=self._database_runtime
        )

    def tearDown(self) -> None:
        self._database_runtime.dispose()
        self._temp_dir.cleanup()

    def test_control_plane_repositories_persist_and_query_data(self) -> None:
        document_payload = self.document_repository.upsert_document(
            document_id="doc-1",
            title="Law Baseline",
            source_type="markdown_file",
            origin_uri="law.md",
            file_name="law.md",
            jurisdiction="CN",
            domain="law",
            visibility="internal",
            tags_details=["law", "baseline"],
            status="active",
            latest_version_id=None,
        )
        self.assertEqual(document_payload["document_id"], "doc-1")
        self.assertEqual(self.document_repository.count_documents(), 1)

        version_no = self.document_version_repository.next_version_no(document_id="doc-1")
        self.assertEqual(version_no, 1)
        version_payload = self.document_version_repository.create_version(
            version_id="ver-1",
            document_id="doc-1",
            version_no=version_no,
            content_hash="hash-raw",
            normalized_text_hash="hash-normalized",
            hash_algorithm="sha1",
            raw_storage_path="raw/doc-1/ver-1/source.bin",
            normalized_storage_path="normalized/doc-1/ver-1/normalized.txt",
            raw_file_size=128,
            normalized_char_count=64,
            parser_name="DocumentParser",
            cleaner_name="DocumentCleaner",
            metadata_details={"uploaded_via": "test"},
        )
        self.assertEqual(version_payload["version_id"], "ver-1")
        reused_version_payload = self.document_version_repository.find_version_by_content_hash(
            document_id="doc-1",
            content_hash="hash-raw",
            hash_algorithm="sha1",
        )
        self.assertIsNotNone(reused_version_payload)
        self.assertEqual(reused_version_payload["version_id"], "ver-1")
        self.assertEqual(
            self.document_version_repository.count_versions(document_id="doc-1"),
            1,
        )
        self.document_repository.set_latest_version_id(
            document_id="doc-1",
            latest_version_id="ver-1",
        )

        latest_version_payload = self.document_version_repository.get_latest_version(
            document_id="doc-1"
        )
        self.assertIsNotNone(latest_version_payload)
        self.assertEqual(latest_version_payload["version_id"], "ver-1")

        task_payload = self.build_task_repository.create_task(
            build_id="build-1",
            build_version_id="knowledge-20260413T000000Z",
            status="running",
            chunk_strategy_name="structure-token-overlap-v1",
            chunk_strategy_details={"chunk_token_size": 300, "overlap_token_size": 50},
            embedding_model_name="deterministic-text-v1",
            manifest_details={"document_ids": ["doc-1"]},
            started_at=utcnow(),
        )
        self.assertEqual(task_payload["status"], "running")
        updated_task_payload = self.build_task_repository.update_task(
            build_id="build-1",
            status="succeeded",
            statistics_details={"chunk_count": 2, "upserted_count": 2},
            quality_gate_details={"passed": True, "failed_rules": []},
            completed_at=utcnow(),
        )
        self.assertIsNotNone(updated_task_payload)
        self.assertEqual(updated_task_payload["status"], "succeeded")

        build_document_payloads = self.build_document_repository.add_records(
            records=[
                {
                    "build_id": "build-1",
                    "document_id": "doc-1",
                    "document_version_id": "ver-1",
                    "content_hash": "hash-raw",
                    "action": "upsert",
                    "chunk_count": 2,
                    "vector_count": 2,
                    "error_message": None,
                }
            ]
        )
        self.assertEqual(len(build_document_payloads), 1)

        chunk_payloads = self.chunk_repository.add_records(
            records=[
                {
                    "chunk_id": "chk-1",
                    "build_id": "build-1",
                    "document_id": "doc-1",
                    "document_version_id": "ver-1",
                    "chunk_index": 0,
                    "token_count": 12,
                    "start_offset": 0,
                    "end_offset": 24,
                    "chunk_text_hash": "hash-chk-1",
                    "chunk_preview": "law baseline text",
                    "embedding_model_name": "deterministic-text-v1",
                    "vector_dimension": 64,
                    "vector_collection": "vi_ai_knowledge_chunks",
                    "vector_point_id": "chk-1",
                    "metadata_details": {"build_id": "build-1"},
                }
            ]
        )
        self.assertEqual(len(chunk_payloads), 1)
        chunk_payload = self.chunk_repository.get_chunk(chunk_id="chk-1")
        self.assertIsNotNone(chunk_payload)
        self.assertEqual(chunk_payload["vector_point_id"], "chk-1")
        self.assertEqual(self.chunk_repository.count_chunks(), 1)

        run_payload = self.evaluation_run_repository.create_run(
            run_id="run-1",
            build_id="build-1",
            dataset_id="dataset-1",
            dataset_version_id="v1",
            status="running",
            trigger_type="manual",
            triggered_by="test",
            summary_details={},
            metadata_details={"build_id": "build-1"},
            started_at=utcnow(),
        )
        self.assertEqual(run_payload["run_id"], "run-1")

        updated_run_payload = self.evaluation_run_repository.update_run(
            run_id="run-1",
            status="succeeded",
            summary_details={"sample_count": 1, "overall_pass_count": 1},
            metadata_details={"build_id": "build-1", "status": "succeeded"},
            completed_at=utcnow(),
        )
        self.assertIsNotNone(updated_run_payload)
        self.assertEqual(updated_run_payload["status"], "succeeded")

        case_payloads = self.evaluation_case_repository.add_cases(
            cases=[
                {
                    "case_id": "run-1_case-1",
                    "run_id": "run-1",
                    "sample_id": "case-1",
                    "query_text": "law baseline",
                    "metadata_filter_details": {},
                    "top_k": 4,
                    "retrieval_label_details": {"min_recall": 0.0},
                    "citation_label_details": {"min_recall": 0.0, "min_precision": 0.0},
                    "answer_label_details": {"min_required_term_hit_ratio": 0.0},
                    "retrieved_chunk_ids": ["chk-1"],
                    "retrieved_document_ids": ["doc-1"],
                    "generated_citation_ids": ["c-1"],
                    "generated_citation_document_ids": ["doc-1"],
                    "answer_text": "law baseline answer",
                    "case_result_details": {"passed": True},
                    "passed": True,
                    "error_message": None,
                }
            ]
        )
        self.assertEqual(len(case_payloads), 1)

        listed_cases = self.evaluation_case_repository.list_cases_by_run_id(run_id="run-1")
        self.assertEqual(len(listed_cases), 1)
        self.assertTrue(listed_cases[0]["passed"])

        recent_build_statuses = self.build_task_repository.list_recent_statuses(limit=5)
        recent_evaluation_statuses = self.evaluation_run_repository.list_recent_statuses(limit=5)
        self.assertEqual(recent_build_statuses[0]["status"], "succeeded")
        self.assertEqual(recent_evaluation_statuses[0]["status"], "succeeded")
