"""Knowledge offline build domain service."""

from __future__ import annotations

from app.rag.document_service import RAGDocumentService
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline
from app.rag.models import OfflineBuildResult, now_utc_iso
from app.rag.state import RAGControlState


def _utc_version_suffix() -> str:
    return now_utc_iso().replace(":", "").replace("-", "").replace("+00:00", "Z")


class RAGBuildService:
    """Create/list/get offline build results and synchronize in-memory snapshots."""

    def __init__(
        self,
        *,
        state: RAGControlState,
        document_service: RAGDocumentService,
        pipeline: KnowledgeIngestionPipeline,
    ) -> None:
        self._state = state
        self._document_service = document_service
        self._pipeline = pipeline

    def create_build(
        self,
        *,
        version_id: str | None = None,
        force_rebuild_document_ids: list[str] | None = None,
        max_failure_ratio: float = 0.0,
        max_empty_chunk_ratio: float = 0.0,
    ) -> OfflineBuildResult:
        documents = self._document_service.clone_documents_for_build()
        if not documents:
            raise ValueError("当前没有可构建的文档。请先上传文档。")

        normalized_version_id = (version_id or "").strip() or f"knowledge-{_utc_version_suffix()}"
        with self._state.lock:
            previous_manifest = self._state.manifest
        result = self._pipeline.build_documents(
            documents=documents,
            version_id=normalized_version_id,
            previous_manifest=previous_manifest,
            force_rebuild_document_ids=force_rebuild_document_ids or [],
            max_failure_ratio=max_failure_ratio,
            max_empty_chunk_ratio=max_empty_chunk_ratio,
        )
        with self._state.lock:
            self._state.manifest = result.manifest
            self._state.build_results[result.metadata.build_id] = result
            if result.metadata.build_id not in self._state.build_ids:
                self._state.build_ids.insert(0, result.metadata.build_id)
        self._document_service.sync_from_build_result(result)
        return result

    def list_builds(self) -> list[OfflineBuildResult]:
        with self._state.lock:
            return [
                self._state.build_results[build_id]
                for build_id in self._state.build_ids
                if build_id in self._state.build_results
            ]

    def get_build(self, build_id: str) -> OfflineBuildResult | None:
        with self._state.lock:
            return self._state.build_results.get(build_id)

    def count_builds(self) -> int:
        with self._state.lock:
            return len(self._state.build_results)

