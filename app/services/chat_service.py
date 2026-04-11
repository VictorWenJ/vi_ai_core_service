"""带独立请求装配的服务层聊天编排。"""

from __future__ import annotations

from time import perf_counter
import traceback
from typing import Any

from app.api.schemas import ChatRequest
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
from app.rag.models import RetrievalResult
from app.rag.runtime import RAGRuntime
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse
from app.services.chat_result import ChatServiceResult
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceError,
    ServiceNotImplementedError,
    ServiceValidationError,
)
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler


class ChatService:
    """面向业务的聊天编排（当前非流式阶段）。"""

    def __init__(
            self,
            app_config: AppConfig,
            registry: ProviderRegistry | None = None,
            prompt_service: PromptService | None = None,
            context_manager: ContextManager | None = None,
            request_assembler: ChatRequestAssembler | None = None,
            rag_runtime: RAGRuntime | None = None,
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

    def chat(self, llm_request: LLMRequest) -> LLMResponse:
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
        except ServiceError as exc:
            _log_service_exception(
                exc,
                provider=provider_for_log,
                model=model_for_log,
                started_at=started_at,
            )
            raise
        except ProviderConfigurationError as exc:
            _log_service_exception(
                exc,
                provider=provider_for_log,
                model=model_for_log,
                started_at=started_at,
            )
            raise ServiceConfigurationError(str(exc)) from exc
        except ConfigError as exc:
            _log_service_exception(
                exc,
                provider=provider_for_log,
                model=model_for_log,
                started_at=started_at,
            )
            raise ServiceConfigurationError(str(exc)) from exc
        except ProviderInvocationError as exc:
            _log_service_exception(
                exc,
                provider=provider_for_log,
                model=model_for_log,
                started_at=started_at,
            )
            raise ServiceDependencyError(str(exc)) from exc
        except (ProviderNotImplementedError, StreamNotImplementedError, NotImplementedError) as exc:
            _log_service_exception(
                exc,
                provider=provider_for_log,
                model=model_for_log,
                started_at=started_at,
            )
            raise ServiceNotImplementedError(str(exc)) from exc
        except ValueError as exc:
            _log_service_exception(
                exc,
                provider=provider_for_log,
                model=model_for_log,
                started_at=started_at,
            )
            raise ServiceValidationError(str(exc)) from exc

    def chat_with_citations_from_user_prompt(self, chat_request: ChatRequest) -> ChatServiceResult:
        retrieval_filter = _extract_retrieval_filter(chat_request.metadata)

        retrieval_result = self._rag_runtime.retrieve_for_chat(
            query_text=chat_request.user_prompt,
            metadata_filter=retrieval_filter,
        )
        log_report("ChatService.chat_with_citations_from_user_prompt.retrieval_result", retrieval_result)

        llm_request = (
            self._request_assembler.assemble_from_user_prompt(
                request=chat_request,
                context_manager=self._context_manager,
                knowledge_block=retrieval_result.knowledge_block,
            ))
        llm_request.metadata["retrieval"] = retrieval_result.trace.to_dict()
        log_report("ChatService.chat_with_citations_from_user_prompt.llm_request", llm_request)

        llm_response = self.chat(llm_request)
        log_report("ChatService.chat_with_citations_from_user_prompt.llm_response", llm_response)

        self._write_context_after_response(
            llm_request,
            chat_request,
            llm_response,
            retrieval_result=retrieval_result,
        )

        return ChatServiceResult(
            llm_response=llm_response,
            citations=retrieval_result.citations,
            retrieval_trace=retrieval_result.trace,
        )

    def _write_context_after_response(
            self,
            llm_request: LLMRequest,
            chat_request: ChatRequest,
            llm_response: LLMResponse,
            *,
            retrieval_result: RetrievalResult,
    ) -> None:
        if llm_request.session_id:
            context_metadata = {
                "conversation_id": llm_request.conversation_id,
                "request_id": llm_request.request_id,
                "provider": llm_response.provider,
                "model": llm_response.model,
                "retrieval_status": retrieval_result.trace.status,
                "citation_count": len(retrieval_result.citations),
            }

            updated_context_window = self._context_manager.update_after_chat_turn(
                session_id=llm_request.session_id,
                conversation_id=llm_request.conversation_id,
                user_content=chat_request.user_prompt,
                assistant_content=llm_response.content,
                metadata=context_metadata,
                memory_config=self._app_config.context_memory_config,
            )
            log_report("ChatService._write_context_after_response.updated_context_window", updated_context_window)

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


def _extract_retrieval_filter(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None
    retrieval_filter = metadata.get("retrieval_filter")
    if not isinstance(retrieval_filter, dict):
        return None
    return dict(retrieval_filter)


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
            "traceback": "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            ),
        },
    )
