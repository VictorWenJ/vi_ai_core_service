"""带独立请求装配的服务层聊天编排。"""

from __future__ import annotations

from time import perf_counter
import traceback
from typing import Any

from app.api.schemas import ChatRequest
from app.config import AppConfig, ConfigError
from app.context.manager import ContextManager
from app.observability.log_until import log_report
from app.providers.base import (
    ProviderConfigurationError,
    ProviderInvocationError,
    ProviderNotImplementedError,
    StreamNotImplementedError,
)
from app.providers.registry import ProviderRegistry
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse
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
            config: AppConfig,
            registry: ProviderRegistry | None = None,
            prompt_service: PromptService | None = None,
            context_manager: ContextManager | None = None,
            request_assembler: ChatRequestAssembler | None = None,
    ) -> None:
        self._config = config
        self._registry = registry or ProviderRegistry(config)
        self._prompt_service = prompt_service or PromptService()
        self._context_manager = context_manager or ContextManager()
        self._request_assembler = request_assembler or ChatRequestAssembler(
            app_config=config,
            prompt_service=self._prompt_service,
        )

    def chat(self, llm_request: LLMRequest) -> LLMResponse:
        started_at = perf_counter()
        provider_for_log = llm_request.provider or self._config.default_provider
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

    def chat_from_user_prompt(self, chat_request: ChatRequest) -> LLMResponse:
        llm_request = (
            self._request_assembler.assemble_from_user_prompt(
                request=chat_request,
                context_manager=self._context_manager,
            ))
        log_report("ChatService.chat_from_user_prompt.llm_request", llm_request)

        llm_response = self.chat(llm_request)
        log_report("ChatService.chat_from_user_prompt.llm_response", llm_response)

        self.append_message(llm_request, chat_request, llm_response)

        return llm_response

    def append_message(self, llm_request:LLMRequest, chat_request:ChatRequest, llm_response:LLMResponse):
        if llm_request.session_id:
            context_metadata = {
                "conversation_id": llm_request.conversation_id,
                "request_id": llm_request.request_id,
                "provider": llm_response.provider,
                "model": llm_response.model,
            }
            self._context_manager.append_user_message(
                llm_request.session_id,
                chat_request.user_prompt,
                metadata=context_metadata,
            )
            self._context_manager.append_assistant_message(
                llm_request.session_id,
                llm_response.content,
                metadata=context_metadata,
            )
        log_report("ChatService.append_message.context_manager", self._context_manager)

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
            "traceback": "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            ),
        },
    )
