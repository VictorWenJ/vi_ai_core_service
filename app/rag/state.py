"""RAG 控制面共享状态容器。"""

from __future__ import annotations

from threading import RLock

from app.rag.evaluation.models import EvaluationRunResult
from app.rag.models import (
    KnowledgeChunk,
    KnowledgeDocument,
    OfflineBuildManifest,
    OfflineBuildResult,
)


class RAGControlState:
    """为 document/build/inspector/evaluation 服务提供共享状态。"""

    def __init__(self) -> None:
        self.lock = RLock()
        self.documents: dict[str, KnowledgeDocument] = {}
        self.chunks: dict[str, KnowledgeChunk] = {}
        self.document_chunk_ids: dict[str, list[str]] = {}
        self.manifest: OfflineBuildManifest | None = None
        self.build_results: dict[str, OfflineBuildResult] = {}
        self.build_ids: list[str] = []
        self.evaluation_runs: dict[str, EvaluationRunResult] = {}
        self.evaluation_run_ids: list[str] = []

