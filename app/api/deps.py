"""API 路由依赖装配辅助。"""

from __future__ import annotations

from functools import lru_cache

from app.config import AppConfig
from app.context.manager import ContextManager
from app.providers.chat.registry import ProviderRegistry
from app.rag.console_service import InternalConsoleRAGService
from app.rag.runtime import RAGRuntime
from app.services.cancellation_registry import CancellationRegistry
from app.services.chat_service import ChatService
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler
from app.services.streaming_chat_service import StreamingChatService


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    return AppConfig.from_env()


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
def get_cancellation_registry() -> CancellationRegistry:
    return CancellationRegistry()


@lru_cache(maxsize=1)
def get_rag_runtime() -> RAGRuntime:
    app_config = get_app_config()
    if not app_config.rag_config.enabled:
        return RAGRuntime.disabled(default_top_k=app_config.rag_config.retrieval_top_k)
    return RAGRuntime.from_app_config(app_config)


@lru_cache(maxsize=1)
def get_internal_console_rag_service() -> InternalConsoleRAGService:
    return InternalConsoleRAGService(
        app_config=get_app_config(),
        rag_runtime=get_rag_runtime(),
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
    )
