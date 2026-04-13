"""同步聊天服务 façade。"""

from __future__ import annotations

from time import perf_counter
import traceback
from typing import Any

from app.api.schemas import ChatRequest
from app.chat_runtime.engine import ChatRuntimeEngine
from app.chat_runtime.models import RuntimeTurnRequest
from app.config import AppConfig, ConfigError
from app.context.manager import ContextManager
from app.observability.log_until import log_report
from app.providers.chat.base import (
    ProviderConfigurationError,
    ProviderInvocationError,
    ProviderNotImplementedError,
    StreamNotImplementedError,
)
from app.providers.chat.registry import ProviderRegistry
from app.rag.runtime import RAGRuntime
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse
from app.services.chat_result import ChatServiceResult
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceNotImplementedError,
    ServiceValidationError,
)
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler


class ChatService:
    """面向 `/chat` 的应用层同步入口。"""

    def __init__(
        self,
        app_config: AppConfig,
        registry: ProviderRegistry | None = None,
        prompt_service: PromptService | None = None,
        context_manager: ContextManager | None = None,
        request_assembler: ChatRequestAssembler | None = None,
        rag_runtime: RAGRuntime | None = None,
        runtime_engine: ChatRuntimeEngine | None = None,
    ) -> None:
        self._app_config = app_config
        self._registry = registry or ProviderRegistry(app_config)
        self._prompt_service = prompt_service or PromptService()
        self._context_manager = context_manager or ContextManager.from_app_config(app_config)
        self._request_assembler = request_assembler or ChatRequestAssembler(
            app_config=app_config,
            prompt_service=self._prompt_service,
        )
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

    def chat(self, llm_request: LLMRequest) -> LLMResponse:
        """兼容旧用例：直接执行规范化后的非流式 provider 调用。"""
        started_at = perf_counter()
        provider_for_log = llm_request.provider or self._app_config.default_provider
        model_for_log = llm_request.model

        try:
            normalized_request = self._request_assembler.normalize_request(
                llm_request,
                provider_registry=self._registry,
            )
            log_report("ChatService.chat.normalized_request", normalized_request)
            provider_for_log = normalized_request.provider
            model_for_log = normalized_request.model
            provider = self._registry.get_provider(normalized_request.provider or "")
            return provider.chat(normalized_request)
        except ProviderConfigurationError as exc:
            _log_service_exception(exc, provider=provider_for_log, model=model_for_log, started_at=started_at)
            raise ServiceConfigurationError(str(exc)) from exc
        except ConfigError as exc:
            _log_service_exception(exc, provider=provider_for_log, model=model_for_log, started_at=started_at)
            raise ServiceConfigurationError(str(exc)) from exc
        except ProviderInvocationError as exc:
            _log_service_exception(exc, provider=provider_for_log, model=model_for_log, started_at=started_at)
            raise ServiceDependencyError(str(exc)) from exc
        except (ProviderNotImplementedError, StreamNotImplementedError, NotImplementedError) as exc:
            _log_service_exception(exc, provider=provider_for_log, model=model_for_log, started_at=started_at)
            raise ServiceNotImplementedError(str(exc)) from exc
        except ValueError as exc:
            _log_service_exception(exc, provider=provider_for_log, model=model_for_log, started_at=started_at)
            raise ServiceValidationError(str(exc)) from exc

    def chat_with_citations_from_user_prompt(self, chat_request: ChatRequest) -> ChatServiceResult:
        started_at = perf_counter()
        try:
            runtime_request = RuntimeTurnRequest(
                user_prompt=chat_request.user_prompt,
                session_id=chat_request.session_id,
                conversation_id=chat_request.conversation_id,
                request_id=chat_request.request_id,
                provider_override=chat_request.provider,
                model_override=chat_request.model,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens,
                system_prompt=chat_request.system_prompt,
                stream=False,
                metadata=dict(chat_request.metadata or {}),
            )
            runtime_result = self._runtime_engine.run_sync(runtime_request)
            llm_response = LLMResponse(
                content=runtime_result.response_text,
                provider=runtime_result.provider,
                model=runtime_result.model,
                usage=runtime_result.usage,
                finish_reason=runtime_result.finish_reason,
                metadata={
                    **runtime_result.metadata,
                    "runtime_trace": runtime_result.trace.to_dict(),
                },
                raw_response=runtime_result.raw_response,
            )
            return ChatServiceResult(
                llm_response=llm_response,
                citations=list(runtime_result.citations),
                retrieval_trace=runtime_result.retrieval_trace,
            )
        except ProviderConfigurationError as exc:
            _log_service_exception(
                exc,
                provider=chat_request.provider or self._app_config.default_provider,
                model=chat_request.model,
                started_at=started_at,
            )
            raise ServiceConfigurationError(str(exc)) from exc
        except ConfigError as exc:
            _log_service_exception(
                exc,
                provider=chat_request.provider or self._app_config.default_provider,
                model=chat_request.model,
                started_at=started_at,
            )
            raise ServiceConfigurationError(str(exc)) from exc
        except ProviderInvocationError as exc:
            _log_service_exception(
                exc,
                provider=chat_request.provider or self._app_config.default_provider,
                model=chat_request.model,
                started_at=started_at,
            )
            raise ServiceDependencyError(str(exc)) from exc
        except (ProviderNotImplementedError, StreamNotImplementedError, NotImplementedError) as exc:
            _log_service_exception(
                exc,
                provider=chat_request.provider or self._app_config.default_provider,
                model=chat_request.model,
                started_at=started_at,
            )
            raise ServiceNotImplementedError(str(exc)) from exc
        except ValueError as exc:
            _log_service_exception(
                exc,
                provider=chat_request.provider or self._app_config.default_provider,
                model=chat_request.model,
                started_at=started_at,
            )
            raise ServiceValidationError(str(exc)) from exc

    def reset_context(
        self,
        *,
        session_id: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_session_id = (session_id or "").strip()
        if not normalized_session_id:
            raise ServiceValidationError("重置操作必须提供 session_id。")

        normalized_conversation_id = (conversation_id or "").strip() or None
        if normalized_conversation_id is None:
            window = self._context_manager.reset_session(normalized_session_id)
        else:
            window = self._context_manager.reset_conversation(
                session_id=normalized_session_id,
                conversation_id=normalized_conversation_id,
            )

        result = {
            "session_id": normalized_session_id,
            "conversation_id": normalized_conversation_id,
            "remaining_message_count": window.message_count,
            "scope": "conversation" if normalized_conversation_id else "session",
        }
        log_report("ChatService.reset_context", result)
        return result


def _log_service_exception(
    exc: BaseException,
    *,
    provider: str | None,
    model: str | None,
    started_at: float,
) -> None:
    log_report(
        "service.chat.error",
        {
            "provider": provider,
            "model": model,
            "latency_ms": round((perf_counter() - started_at) * 1000, 2),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        },
    )
