"""Knowledge 离线构建应用服务。"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.rag.content_store.local_store import LocalRAGContentStore
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline
from app.rag.models import KnowledgeDocument, compute_content_hash, generate_build_id
from app.rag.repository.build_document_repository import BuildDocumentRepository
from app.rag.repository.build_task_repository import BuildTaskRepository
from app.rag.repository.chunk_repository import ChunkRepository
from app.rag.repository.document_version_repository import DocumentVersionRepository
from app.rag.repository._utils import utcnow
from app.rag.retrieval.vector_store import BaseVectorStore


def _utc_version_suffix() -> str:
    return utcnow().strftime("%Y%m%dT%H%M%SZ")


class RAGBuildService:
    """负责离线构建任务创建与持久化。"""

    def __init__(
        self,
        *,
        document_version_repository: DocumentVersionRepository,
        build_task_repository: BuildTaskRepository,
        build_document_repository: BuildDocumentRepository,
        chunk_repository: ChunkRepository,
        content_store: LocalRAGContentStore,
        pipeline: KnowledgeIngestionPipeline,
        vector_store: BaseVectorStore,
    ) -> None:
        self._document_version_repository = document_version_repository
        self._build_task_repository = build_task_repository
        self._build_document_repository = build_document_repository
        self._chunk_repository = chunk_repository
        self._content_store = content_store
        self._pipeline = pipeline
        self._vector_store = vector_store

    def create_build(
        self,
        *,
        version_id: str | None = None,
        force_rebuild_document_ids: list[str] | None = None,
        max_failure_ratio: float = 0.0,
        max_empty_chunk_ratio: float = 0.0,
    ) -> dict[str, Any]:
        latest_versions = self._document_version_repository.list_latest_versions_for_build(
            document_ids=force_rebuild_document_ids or None
        )
        if not latest_versions:
            raise ValueError("当前没有可构建的文档版本。")

        build_id = generate_build_id()
        build_version_id = (version_id or "").strip() or f"knowledge-{_utc_version_suffix()}"
        started_at = utcnow()
        manifest_details = self._build_manifest_details(
            build_version_id=build_version_id,
            latest_versions=latest_versions,
            force_rebuild_document_ids=force_rebuild_document_ids or [],
        )
        self._build_task_repository.create_task(
            build_id=build_id,
            build_version_id=build_version_id,
            status="running",
            chunk_strategy_name=self._pipeline._chunk_strategy_version,  # noqa: SLF001
            chunk_strategy_details={
                "chunk_token_size": self._pipeline._chunk_token_size,  # noqa: SLF001
                "overlap_token_size": self._pipeline._overlap_token_size,  # noqa: SLF001
                "strategy_version": self._pipeline._chunk_strategy_version,  # noqa: SLF001
            },
            embedding_model_name=self._pipeline._embedding_model,  # noqa: SLF001
            manifest_details=manifest_details,
            started_at=started_at,
        )

        started_perf = perf_counter()
        requested_document_count = len(latest_versions)
        processed_document_count = 0
        failed_document_count = 0
        chunk_count = 0
        vector_count = 0
        embedding_batch_count = 0
        empty_chunk_document_count = 0
        build_document_records: list[dict[str, Any]] = []
        chunk_records: list[dict[str, Any]] = []

        for item in latest_versions:
            document_payload = dict(item["document"])
            version_payload = dict(item["version"])
            document_id = str(document_payload["document_id"])
            version_key = str(version_payload["version_id"])
            try:
                normalized_text = self._content_store.read_normalized_text(
                    storage_path=version_payload["normalized_storage_path"]
                )
                document = KnowledgeDocument(
                    document_id=document_id,
                    title=document_payload["title"],
                    source_type=document_payload["source_type"],
                    content=normalized_text,
                    origin_uri=document_payload.get("origin_uri"),
                    file_name=document_payload.get("file_name"),
                    jurisdiction=document_payload.get("jurisdiction"),
                    domain=document_payload.get("domain"),
                    tags=list(document_payload.get("tags_details") or []),
                    updated_at=document_payload.get("updated_at"),
                    visibility=document_payload.get("visibility") or "internal",
                    metadata=dict(version_payload.get("metadata_details") or {}),
                )
                ingestion_result = self._pipeline.ingest_document(
                    document,
                    build_metadata={
                        "build_id": build_id,
                        "build_version_id": build_version_id,
                        "document_version_id": version_key,
                    },
                )
                processed_document_count += 1
                chunk_count += ingestion_result.trace.chunk_count
                vector_count += ingestion_result.trace.upserted_count
                embedding_batch_count += ingestion_result.trace.embedding_batch_count
                if ingestion_result.trace.chunk_count == 0:
                    empty_chunk_document_count += 1

                build_document_records.append(
                    {
                        "build_id": build_id,
                        "document_id": document_id,
                        "document_version_id": version_key,
                        "content_hash": version_payload["content_hash"],
                        "action": "upsert",
                        "chunk_count": ingestion_result.trace.chunk_count,
                        "vector_count": ingestion_result.trace.upserted_count,
                        "error_message": None,
                    }
                )
                for chunk in ingestion_result.chunks:
                    chunk_records.append(
                        {
                            "chunk_id": chunk.chunk_id,
                            "build_id": build_id,
                            "document_id": document_id,
                            "document_version_id": version_key,
                            "chunk_index": chunk.chunk_index,
                            "token_count": chunk.token_count,
                            "start_offset": chunk.metadata.get("start_offset"),
                            "end_offset": chunk.metadata.get("end_offset"),
                            "chunk_text_hash": compute_content_hash(chunk.chunk_text),
                            "chunk_preview": self._snippet(chunk.chunk_text, max_chars=240),
                            "embedding_model_name": chunk.embedding_model,
                            "vector_dimension": ingestion_result.trace.embedding_dimension,
                            "vector_collection": self._vector_store.get_collection_name(),
                            "vector_point_id": chunk.chunk_id,
                            "metadata_details": {
                                **dict(chunk.metadata or {}),
                                "build_id": build_id,
                                "build_version_id": build_version_id,
                            },
                        }
                    )
            except Exception as exc:
                failed_document_count += 1
                build_document_records.append(
                    {
                        "build_id": build_id,
                        "document_id": document_id,
                        "document_version_id": version_key,
                        "content_hash": version_payload["content_hash"],
                        "action": "failed",
                        "chunk_count": 0,
                        "vector_count": 0,
                        "error_message": str(exc),
                    }
                )

        self._build_document_repository.add_records(records=build_document_records)
        self._chunk_repository.add_records(records=chunk_records)

        latency_ms = round((perf_counter() - started_perf) * 1000, 2)
        statistics_details = {
            "requested_document_count": requested_document_count,
            "processed_document_count": processed_document_count,
            "skipped_document_count": 0,
            "failed_document_count": failed_document_count,
            "chunk_count": chunk_count,
            "upserted_count": vector_count,
            "embedding_batch_count": embedding_batch_count,
            "latency_ms": latency_ms,
        }
        quality_gate_details = self._evaluate_quality_gate(
            requested_document_count=requested_document_count,
            processed_document_count=processed_document_count,
            failed_document_count=failed_document_count,
            empty_chunk_document_count=empty_chunk_document_count,
            chunk_count=chunk_count,
            vector_count=vector_count,
            max_failure_ratio=max_failure_ratio,
            max_empty_chunk_ratio=max_empty_chunk_ratio,
        )
        status = "succeeded" if quality_gate_details["passed"] else "failed"
        error_message = None if status == "succeeded" else "quality gate failed"
        self._build_task_repository.update_task(
            build_id=build_id,
            status=status,
            statistics_details=statistics_details,
            quality_gate_details=quality_gate_details,
            error_message=error_message,
            completed_at=utcnow(),
        )
        task_payload = self._build_task_repository.get_task(build_id=build_id)
        if task_payload is None:
            raise RuntimeError("构建任务创建成功后读取失败。")
        return self._to_build_detail_payload(task_payload)

    def list_builds(self) -> list[dict[str, Any]]:
        task_payloads = self._build_task_repository.list_tasks()
        return [self._to_build_detail_payload(task_payload) for task_payload in task_payloads]

    def get_build(self, build_id: str) -> dict[str, Any] | None:
        task_payload = self._build_task_repository.get_task(build_id=build_id)
        if task_payload is None:
            return None
        return self._to_build_detail_payload(task_payload)

    def count_builds(self) -> int:
        return self._build_task_repository.count_tasks()

    @staticmethod
    def _snippet(text: str, *, max_chars: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= max_chars:
            return normalized
        if max_chars <= 3:
            return normalized[:max_chars]
        return f"{normalized[: max_chars - 3]}..."

    @staticmethod
    def _build_manifest_details(
        *,
        build_version_id: str,
        latest_versions: list[dict[str, Any]],
        force_rebuild_document_ids: list[str],
    ) -> dict[str, Any]:
        document_ids = [str(item["document"]["document_id"]) for item in latest_versions]
        document_version_ids = [str(item["version"]["version_id"]) for item in latest_versions]
        return {
            "build_version_id": build_version_id,
            "document_ids": document_ids,
            "document_version_ids": document_version_ids,
            "forced_document_ids": [str(item) for item in force_rebuild_document_ids],
            "documents": [
                {
                    "document_id": str(item["document"]["document_id"]),
                    "document_version_id": str(item["version"]["version_id"]),
                    "content_hash": str(item["version"]["content_hash"]),
                }
                for item in latest_versions
            ],
        }

    @staticmethod
    def _evaluate_quality_gate(
        *,
        requested_document_count: int,
        processed_document_count: int,
        failed_document_count: int,
        empty_chunk_document_count: int,
        chunk_count: int,
        vector_count: int,
        max_failure_ratio: float,
        max_empty_chunk_ratio: float,
    ) -> dict[str, Any]:
        requested = max(requested_document_count, 1)
        processed = max(processed_document_count, 1)
        failure_ratio = failed_document_count / requested
        empty_chunk_ratio = empty_chunk_document_count / processed
        failed_rules: list[str] = []
        if failure_ratio > max_failure_ratio:
            failed_rules.append("failure_ratio_exceeded")
        if empty_chunk_ratio > max_empty_chunk_ratio:
            failed_rules.append("empty_chunk_ratio_exceeded")
        if chunk_count != vector_count:
            failed_rules.append("upserted_count_mismatch")
        return {
            "passed": len(failed_rules) == 0,
            "failed_rules": failed_rules,
            "failure_ratio": failure_ratio,
            "empty_chunk_ratio": empty_chunk_ratio,
            "max_failure_ratio": max_failure_ratio,
            "max_empty_chunk_ratio": max_empty_chunk_ratio,
        }

    def _to_build_detail_payload(self, task_payload: dict[str, Any]) -> dict[str, Any]:
        build_id = str(task_payload["build_id"])
        build_documents = self._build_document_repository.list_by_build_id(build_id=build_id)
        statistics_details = dict(task_payload.get("statistics_details") or {})
        quality_gate_details = dict(task_payload.get("quality_gate_details") or {})
        return {
            "metadata": {
                "build_id": build_id,
                "version_id": task_payload["build_version_id"],  # 向后兼容
                "build_version_id": task_payload["build_version_id"],
                "status": task_payload["status"],
                "chunk_strategy_name": task_payload["chunk_strategy_name"],
                "chunk_strategy_version": task_payload["chunk_strategy_name"],  # 向后兼容
                "embedding_model_name": task_payload["embedding_model_name"],
                "embedding_model_version": task_payload["embedding_model_name"],  # 向后兼容
                "started_at": task_payload["started_at"],
                "completed_at": task_payload["completed_at"],
                "created_at": task_payload["created_at"],
            },
            "statistics": {
                "requested_document_count": int(
                    statistics_details.get("requested_document_count", 0)
                ),
                "processed_document_count": int(
                    statistics_details.get("processed_document_count", 0)
                ),
                "skipped_document_count": int(
                    statistics_details.get("skipped_document_count", 0)
                ),
                "failed_document_count": int(
                    statistics_details.get("failed_document_count", 0)
                ),
                "chunk_count": int(statistics_details.get("chunk_count", 0)),
                "upserted_count": int(statistics_details.get("upserted_count", 0)),
                "embedding_batch_count": int(
                    statistics_details.get("embedding_batch_count", 0)
                ),
                "latency_ms": float(statistics_details.get("latency_ms", 0.0)),
            },
            "quality_gate": {
                "passed": bool(quality_gate_details.get("passed", False)),
                "failed_rules": list(quality_gate_details.get("failed_rules") or []),
                "failure_ratio": float(quality_gate_details.get("failure_ratio", 0.0)),
                "empty_chunk_ratio": float(quality_gate_details.get("empty_chunk_ratio", 0.0)),
                "max_failure_ratio": float(
                    quality_gate_details.get("max_failure_ratio", 0.0)
                ),
                "max_empty_chunk_ratio": float(
                    quality_gate_details.get("max_empty_chunk_ratio", 0.0)
                ),
            },
            "manifest": dict(task_payload.get("manifest_details") or {}),
            "ingestion_results": [
                {
                    "document_id": record["document_id"],
                    "document_version_id": record["document_version_id"],
                    "chunk_count": record["chunk_count"],
                    "vector_count": record["vector_count"],
                    "action": record["action"],
                    "error_message": record["error_message"],
                }
                for record in build_documents
            ],
        }
