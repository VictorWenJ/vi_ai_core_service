"""系统运行态摘要应用服务。"""

from __future__ import annotations

from typing import Any

from app.config import AppConfig
from app.rag.build_service import RAGBuildService
from app.rag.document_service import RAGDocumentService
from app.rag.evaluation_service import RAGEvaluationService
from app.rag.models import now_utc_iso


class RuntimeService:
    """聚合 runtime/config/health 摘要给 API 层消费。"""

    def __init__(
        self,
        *,
        app_config: AppConfig,
        document_service: RAGDocumentService,
        build_service: RAGBuildService,
        evaluation_service: RAGEvaluationService,
    ) -> None:
        self._app_config = app_config
        self._document_service = document_service
        self._build_service = build_service
        self._evaluation_service = evaluation_service

    def get_runtime_summary(self) -> dict[str, Any]:
        rag_config = self._app_config.rag_config
        return {
            "service": "vi_ai_core_service",
            "default_provider": self._app_config.default_provider,
            "rag_enabled": rag_config.enabled,
            "embedding_provider": rag_config.embedding_provider,
            "embedding_model": rag_config.embedding_model,
            "retrieval_top_k": rag_config.retrieval_top_k,
            "score_threshold": rag_config.score_threshold,
            "chunk_token_size": rag_config.chunk_token_size,
            "chunk_overlap_token_size": rag_config.chunk_overlap_token_size,
            "document_count": self._document_service.count_documents(),
            "chunk_count": self._document_service.count_chunks(),
            "build_count": self._build_service.count_builds(),
            "evaluation_run_count": self._evaluation_service.count_evaluation_runs(),
        }

    def get_runtime_config_summary(self) -> dict[str, Any]:
        providers = {
            name: {
                "default_model": config.default_model,
                "base_url": config.base_url,
                "timeout_seconds": config.timeout_seconds,
                "api_key_configured": bool(config.api_key),
            }
            for name, config in self._app_config.providers.items()
        }
        return {
            "default_provider": self._app_config.default_provider,
            "providers": providers,
            "streaming": {
                "enabled": self._app_config.streaming_config.streaming_enabled,
                "heartbeat_interval_seconds": self._app_config.streaming_config.stream_heartbeat_interval_seconds,
                "request_timeout_seconds": self._app_config.streaming_config.stream_request_timeout_seconds,
                "emit_usage": self._app_config.streaming_config.stream_emit_usage,
                "emit_trace": self._app_config.streaming_config.stream_emit_trace,
                "cancel_enabled": self._app_config.streaming_config.stream_cancel_enabled,
            },
            "rag": {
                "enabled": self._app_config.rag_config.enabled,
                "qdrant_url": self._app_config.rag_config.qdrant_url,
                "qdrant_collection": self._app_config.rag_config.qdrant_collection,
                "embedding_provider": self._app_config.rag_config.embedding_provider,
                "embedding_model": self._app_config.rag_config.embedding_model,
                "retrieval_top_k": self._app_config.rag_config.retrieval_top_k,
                "score_threshold": self._app_config.rag_config.score_threshold,
            },
        }

    def get_runtime_health(self) -> dict[str, Any]:
        summary = self.get_runtime_summary()
        return {
            "status": "ok",
            "service": summary["service"],
            "checked_at": now_utc_iso(),
            "summary": summary,
        }

