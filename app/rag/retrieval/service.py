"""Retrieval service for chat orchestration."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.observability.log_until import log_report
from app.providers.embeddings.base import BaseEmbeddingProvider
from app.rag.citation.formatter import build_citations
from app.rag.models import RetrievalResult, RetrievalTrace
from app.rag.retrieval.rendering import render_knowledge_block
from app.rag.retrieval.vector_store import BaseVectorStore


class RetrievalExecutionError(RuntimeError):
    """Raised when retrieval cannot be completed."""


class KnowledgeRetrievalService:
    """Query embeddings + vector index and build citation-ready output."""

    def __init__(
        self,
        *,
        embedding_provider: BaseEmbeddingProvider,
        vector_store: BaseVectorStore,
        embedding_model: str,
        default_top_k: int,
        default_score_threshold: float | None = None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._embedding_model = embedding_model
        self._default_top_k = default_top_k
        self._default_score_threshold = default_score_threshold

    def retrieve(
        self,
        *,
        query_text: str,
        top_k: int | None = None,
        metadata_filter: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> RetrievalResult:
        # 1) 记录开始时间，用于后续统一计算检索链路耗时。
        started_at = perf_counter()

        # 2) 归一化 top-k：优先使用调用方传入值，否则回落到服务默认值。
        resolved_top_k = top_k or self._default_top_k

        # 3) 归一化过滤条件，确保后续日志与 trace 始终拿到字典快照。
        resolved_filter = dict(metadata_filter or {})

        # 4) 归一化分数阈值：显式传入优先，否则使用默认阈值配置。
        resolved_score_threshold = (
            score_threshold
            if score_threshold is not None
            else self._default_score_threshold
        )
        try:
            # 5) 先对查询文本做 embedding，得到用于向量检索的查询向量。
            embedding_result = self._embedding_provider.embed_texts(
                [query_text],
                model=self._embedding_model,
            )
            log_report("KnowledgeRetrievalService.retrieve.embedding_result", embedding_result)

            # embedding 结果为空时直接判定为执行失败，进入异常收口。
            if not embedding_result.vectors:
                raise RetrievalExecutionError("Embedding provider returned empty vectors.")

            # 6) 基于查询向量执行向量检索，并应用 top-k / metadata filter / score threshold。
            query_vector = embedding_result.vectors[0]
            retrieved_chunks = self._vector_store.query(
                query_vector=query_vector,
                top_k=resolved_top_k,
                metadata_filter=resolved_filter,
                score_threshold=resolved_score_threshold,
            )
            log_report("KnowledgeRetrievalService.retrieve.retrieved_chunks", retrieved_chunks)

            # 7) 将命中 chunk 转换为可追溯 citation，并渲染可注入 prompt 的 knowledge block。
            citations = build_citations(retrieved_chunks)
            log_report("KnowledgeRetrievalService.retrieve.citations", citations)

            knowledge_block = render_knowledge_block(retrieved_chunks)
            log_report("KnowledgeRetrievalService.retrieve.knowledge_block", knowledge_block)

            # 8) 组装成功态 trace，并输出结构化 observability 日志。
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            trace = RetrievalTrace(
                status="succeeded",
                query_text=query_text,
                top_k=resolved_top_k,
                metadata_filter=resolved_filter,
                hit_count=len(retrieved_chunks),
                citation_count=len(citations),
                latency_ms=latency_ms,
            )
            log_report(
                "rag.retrieval.succeeded",
                {
                    "query_text": query_text,
                    "top_k": resolved_top_k,
                    "metadata_filter": resolved_filter,
                    "score_threshold": resolved_score_threshold,
                    "hit_count": len(retrieved_chunks),
                    "citation_count": len(citations),
                    "latency_ms": latency_ms,
                },
            )
            return RetrievalResult(
                knowledge_block=knowledge_block,
                retrieved_chunks=retrieved_chunks,
                citations=citations,
                trace=trace,
            )
        except Exception as exc:
            # 9) 任意异常统一记录失败日志，并抛出 RetrievalExecutionError 给上层做降级处理。
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            log_report(
                "rag.retrieval.failed",
                {
                    "query_text": query_text,
                    "top_k": resolved_top_k,
                    "metadata_filter": resolved_filter,
                    "score_threshold": resolved_score_threshold,
                    "latency_ms": latency_ms,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise RetrievalExecutionError(str(exc)) from exc
