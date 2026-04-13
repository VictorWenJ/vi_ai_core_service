"""流式聊天服务 façade。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from app.api.schemas import ChatCancelRequest, ChatStreamOptions, ChatStreamRequest
from app.chat_runtime.engine import ChatRuntimeEngine
from app.chat_runtime.models import RuntimeStreamOptions, RuntimeTurnRequest
from app.config import AppConfig
from app.context.manager import ContextManager
from app.context.models import normalize_conversation_scope
from app.observability.log_until import log_report
from app.providers.chat.registry import ProviderRegistry
from app.rag.runtime import RAGRuntime
from app.services.cancellation_registry import CancellationRegistry
from app.services.errors import ServiceNotImplementedError
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler


class StreamingChatService:
    """面向 `/chat_stream` 与 `/chat_stream_cancel` 的应用层入口。"""

    def __init__(
        self,
        *,
        app_config: AppConfig,
        registry: ProviderRegistry,
        prompt_service: PromptService,
        context_manager: ContextManager,
        request_assembler: ChatRequestAssembler,
        cancellation_registry: CancellationRegistry,
        rag_runtime: RAGRuntime | None = None,
        runtime_engine: ChatRuntimeEngine | None = None,
    ) -> None:
        self._app_config = app_config
        self._registry = registry
        self._prompt_service = prompt_service
        self._context_manager = context_manager
        self._request_assembler = request_assembler
        self._cancellation_registry = cancellation_registry
        self._rag_runtime = rag_runtime or (
            RAGRuntime.from_app_config(app_config)
            if app_config.rag_config.enabled
            else RAGRuntime.disabled(default_top_k=app_config.rag_config.retrieval_top_k)
        )
        self._runtime_engine = runtime_engine or ChatRuntimeEngine(
            app_config=app_config,
            provider_registry=self._registry,
            context_manager=self._context_manager,
            request_assembler=self._request_assembler,
            rag_runtime=self._rag_runtime,
        )

    def stream_chat_from_user_prompt(self, chat_request: ChatStreamRequest) -> Iterator[dict[str, Any]]:
        if not self._app_config.streaming_config.streaming_enabled:
            raise ServiceNotImplementedError("当前环境未开启流式能力。")

        request_id = (chat_request.request_id or f"req_{uuid4()}").strip()
        assistant_message_id = f"am_{uuid4()}"
        user_message_id = f"um_{uuid4()}"
        normalized_session_id = (chat_request.session_id or "").strip() or None
        normalized_conversation_id = normalize_conversation_scope(chat_request.conversation_id)
        stream_options = self._resolve_stream_options(chat_request.stream_options)

        handle = self._cancellation_registry.register(
            request_id=request_id,
            assistant_message_id=assistant_message_id,
            session_id=normalized_session_id or "__stateless__",
            conversation_id=normalized_conversation_id,
            provider=chat_request.provider,
            model=chat_request.model,
        )
        log_report(
            "StreamingChatService.stream_chat_from_user_prompt.handle",
            {
                "request_id": handle.request_id,
                "assistant_message_id": handle.assistant_message_id,
                "session_id": handle.session_id,
                "conversation_id": handle.conversation_id,
                "provider": handle.provider,
                "model": handle.model,
            },
        )

        runtime_request = RuntimeTurnRequest(
            user_prompt=chat_request.user_prompt,
            session_id=normalized_session_id,
            conversation_id=normalized_conversation_id,
            request_id=request_id,
            provider_override=chat_request.provider,
            model_override=chat_request.model,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
            system_prompt=chat_request.system_prompt,
            stream=True,
            metadata=dict(chat_request.metadata or {}),
            stream_options=stream_options,
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            cancel_event=handle.cancel_event,
        )
        try:
            yield from self._runtime_engine.run_stream(runtime_request)
        finally:
            self._cancellation_registry.unregister(handle)

    def cancel_stream(self, cancel_request: ChatCancelRequest) -> dict[str, object]:
        if not self._app_config.streaming_config.stream_cancel_enabled:
            raise ServiceNotImplementedError("当前环境未开启流式取消能力。")

        result = self._cancellation_registry.cancel(
            request_id=normalize_optional_text(cancel_request.request_id),
            assistant_message_id=normalize_optional_text(cancel_request.assistant_message_id),
            session_id=normalize_optional_text(cancel_request.session_id),
            conversation_id=normalize_optional_text(cancel_request.conversation_id),
        )
        log_report("StreamingChatService.cancel_stream", result)
        return result

    def _resolve_stream_options(self, stream_options: ChatStreamOptions | None) -> RuntimeStreamOptions:
        default_config = self._app_config.streaming_config
        if stream_options is None:
            return RuntimeStreamOptions(
                stream_heartbeat_interval_seconds=default_config.stream_heartbeat_interval_seconds,
                stream_request_timeout_seconds=default_config.stream_request_timeout_seconds,
                stream_emit_usage=default_config.stream_emit_usage,
                stream_emit_trace=default_config.stream_emit_trace,
            )

        return RuntimeStreamOptions(
            stream_heartbeat_interval_seconds=(
                stream_options.stream_heartbeat_interval_seconds
                if stream_options.stream_heartbeat_interval_seconds is not None
                else default_config.stream_heartbeat_interval_seconds
            ),
            stream_request_timeout_seconds=(
                stream_options.stream_request_timeout_seconds
                if stream_options.stream_request_timeout_seconds is not None
                else default_config.stream_request_timeout_seconds
            ),
            stream_emit_usage=(
                stream_options.stream_emit_usage
                if stream_options.stream_emit_usage is not None
                else default_config.stream_emit_usage
            ),
            stream_emit_trace=(
                stream_options.stream_emit_trace
                if stream_options.stream_emit_trace is not None
                else default_config.stream_emit_trace
            ),
        )


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
