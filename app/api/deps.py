"""API 路由依赖装配辅助。"""

from __future__ import annotations

from functools import lru_cache

from app.chat_runtime.engine import ChatRuntimeEngine
from app.config import AppConfig
from app.context.manager import ContextManager
from app.context.policies.tokenizer import CharacterTokenCounter
from app.db import DatabaseRuntime, ensure_database_schema
from app.providers.embeddings.registry import build_embedding_provider
from app.providers.chat.registry import ProviderRegistry
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
from app.rag.retrieval.vector_store import InMemoryVectorStore, QdrantVectorStore
from app.rag.runtime import RAGRuntime
from app.services.cancellation_registry import CancellationRegistry
from app.services.chat_service import ChatService
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler
from app.services.runtime_service import RuntimeService
from app.services.streaming_chat_service import StreamingChatService


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    return AppConfig.from_env()


@lru_cache(maxsize=1)
def get_database_runtime() -> DatabaseRuntime:
    config = get_app_config()
    runtime = DatabaseRuntime(
        database_url=config.database_config.url,
        echo_sql=config.database_config.echo_sql,
        pool_pre_ping=config.database_config.pool_pre_ping,
    )
    ensure_database_schema(runtime)
    return runtime


@lru_cache(maxsize=1)
def get_rag_content_store() -> LocalRAGContentStore:
    config = get_app_config()
    return LocalRAGContentStore(root_path=config.rag_content_store_config.root_path)


@lru_cache(maxsize=1)
def get_document_repository() -> DocumentRepository:
    return DocumentRepository(database_runtime=get_database_runtime())


@lru_cache(maxsize=1)
def get_document_version_repository() -> DocumentVersionRepository:
    return DocumentVersionRepository(database_runtime=get_database_runtime())


@lru_cache(maxsize=1)
def get_build_task_repository() -> BuildTaskRepository:
    return BuildTaskRepository(database_runtime=get_database_runtime())


@lru_cache(maxsize=1)
def get_build_document_repository() -> BuildDocumentRepository:
    return BuildDocumentRepository(database_runtime=get_database_runtime())


@lru_cache(maxsize=1)
def get_chunk_repository() -> ChunkRepository:
    return ChunkRepository(database_runtime=get_database_runtime())


@lru_cache(maxsize=1)
def get_evaluation_run_repository() -> EvaluationRunRepository:
    return EvaluationRunRepository(database_runtime=get_database_runtime())


@lru_cache(maxsize=1)
def get_evaluation_case_repository() -> EvaluationCaseRepository:
    return EvaluationCaseRepository(database_runtime=get_database_runtime())


@lru_cache(maxsize=1)
def get_prompt_service() -> PromptService:
    return PromptService()


@lru_cache(maxsize=1)
def get_context_manager() -> ContextManager:
    return ContextManager.from_app_config(get_app_config())


@lru_cache(maxsize=1)
def get_provider_registry() -> ProviderRegistry:
    return ProviderRegistry(get_app_config())


@lru_cache(maxsize=1)
def get_request_assembler() -> ChatRequestAssembler:
    return ChatRequestAssembler(
        app_config=get_app_config(),
        prompt_service=get_prompt_service(),
    )


@lru_cache(maxsize=1)
def get_chat_runtime_engine() -> ChatRuntimeEngine:
    return ChatRuntimeEngine(
        app_config=get_app_config(),
        provider_registry=get_provider_registry(),
        context_manager=get_context_manager(),
        request_assembler=get_request_assembler(),
        rag_runtime=get_rag_runtime(),
    )


@lru_cache(maxsize=1)
def get_cancellation_registry() -> CancellationRegistry:
    return CancellationRegistry()


@lru_cache(maxsize=1)
def get_rag_runtime() -> RAGRuntime:
    app_config = get_app_config()
    if not app_config.rag_config.enabled:
        return RAGRuntime.disabled(default_top_k=app_config.rag_config.retrieval_top_k)
    return RAGRuntime.from_app_config(app_config)


@lru_cache(maxsize=1)
def get_rag_control_vector_store():
    app_config = get_app_config()
    rag_config = app_config.rag_config
    if not rag_config.enabled:
        return InMemoryVectorStore()
    return QdrantVectorStore(
        url=rag_config.qdrant_url,
        collection_name=rag_config.qdrant_collection,
        api_key=rag_config.qdrant_api_key,
    )


@lru_cache(maxsize=1)
def get_rag_control_embedding_provider():
    return build_embedding_provider(get_app_config())


@lru_cache(maxsize=1)
def get_rag_document_service() -> RAGDocumentService:
    return RAGDocumentService(
        document_repository=get_document_repository(),
        document_version_repository=get_document_version_repository(),
        content_store=get_rag_content_store(),
        parser=DocumentParser(),
        cleaner=DocumentCleaner(),
    )


@lru_cache(maxsize=1)
def get_rag_control_retrieval_service() -> KnowledgeRetrievalService:
    app_config = get_app_config()
    rag_config = app_config.rag_config
    return KnowledgeRetrievalService(
        embedding_provider=get_rag_control_embedding_provider(),
        vector_store=get_rag_control_vector_store(),
        embedding_model=rag_config.embedding_model,
        default_top_k=rag_config.retrieval_top_k,
        default_score_threshold=rag_config.score_threshold,
    )


@lru_cache(maxsize=1)
def get_rag_control_ingestion_pipeline() -> KnowledgeIngestionPipeline:
    app_config = get_app_config()
    rag_config = app_config.rag_config
    return KnowledgeIngestionPipeline(
        parser=DocumentParser(),
        cleaner=DocumentCleaner(),
        chunker=StructuredTokenChunker(token_counter=CharacterTokenCounter()),
        embedding_provider=get_rag_control_embedding_provider(),
        vector_store=get_rag_control_vector_store(),
        embedding_model=rag_config.embedding_model,
        chunk_token_size=rag_config.chunk_token_size,
        overlap_token_size=rag_config.chunk_overlap_token_size,
        chunk_strategy_version="structure-token-overlap-v1",
        embedding_model_version=rag_config.embedding_model,
    )


@lru_cache(maxsize=1)
def get_rag_build_service() -> RAGBuildService:
    return RAGBuildService(
        document_version_repository=get_document_version_repository(),
        build_task_repository=get_build_task_repository(),
        build_document_repository=get_build_document_repository(),
        chunk_repository=get_chunk_repository(),
        content_store=get_rag_content_store(),
        pipeline=get_rag_control_ingestion_pipeline(),
        vector_store=get_rag_control_vector_store(),
    )


@lru_cache(maxsize=1)
def get_rag_inspector_service() -> RAGInspectorService:
    return RAGInspectorService(
        app_config=get_app_config(),
        rag_runtime=get_rag_runtime(),
        retrieval_service=get_rag_control_retrieval_service(),
        document_repository=get_document_repository(),
        document_version_repository=get_document_version_repository(),
        build_task_repository=get_build_task_repository(),
        build_document_repository=get_build_document_repository(),
        chunk_repository=get_chunk_repository(),
        content_store=get_rag_content_store(),
        vector_store=get_rag_control_vector_store(),
    )


@lru_cache(maxsize=1)
def get_rag_evaluation_service() -> RAGEvaluationService:
    return RAGEvaluationService(
        evaluation_run_repository=get_evaluation_run_repository(),
        evaluation_case_repository=get_evaluation_case_repository(),
        inspector_service=get_rag_inspector_service(),
        document_service=get_rag_document_service(),
    )


@lru_cache(maxsize=1)
def get_runtime_service() -> RuntimeService:
    return RuntimeService(
        app_config=get_app_config(),
        document_repository=get_document_repository(),
        chunk_repository=get_chunk_repository(),
        build_task_repository=get_build_task_repository(),
        evaluation_run_repository=get_evaluation_run_repository(),
    )


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService(
        app_config=get_app_config(),
        registry=get_provider_registry(),
        prompt_service=get_prompt_service(),
        context_manager=get_context_manager(),
        request_assembler=get_request_assembler(),
        rag_runtime=get_rag_runtime(),
        runtime_engine=get_chat_runtime_engine(),
    )


@lru_cache(maxsize=1)
def get_streaming_chat_service() -> StreamingChatService:
    return StreamingChatService(
        app_config=get_app_config(),
        registry=get_provider_registry(),
        prompt_service=get_prompt_service(),
        context_manager=get_context_manager(),
        request_assembler=get_request_assembler(),
        cancellation_registry=get_cancellation_registry(),
        rag_runtime=get_rag_runtime(),
        runtime_engine=get_chat_runtime_engine(),
    )
