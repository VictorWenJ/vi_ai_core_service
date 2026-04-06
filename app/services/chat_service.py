"""Service-level chat orchestration with separated request assembly."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.config import AppConfig, ConfigError
from app.context.manager import ContextManager
from app.observability.context import update_request_context
from app.observability.events import log_service_request
from app.observability.exception_logging import log_exception
from app.observability.logging_setup import get_logger
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

_service_logger = get_logger("services.llm")


class ChatService:
    """Business-facing chat orchestration for Phase 1 non-streaming requests."""

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
            config=config,
            prompt_service=self._prompt_service,
        )

    def chat(self, request: LLMRequest) -> LLMResponse:
        started_at = perf_counter()
        provider_for_log = request.provider or self._config.default_provider
        model_for_log = request.model
        update_request_context(
            request_id=request.request_id,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            provider=provider_for_log,
            model=model_for_log,
        )

        try:
            normalized_request = self._request_assembler.normalize_request(
                request,
                registry=self._registry,
            )
            provider_for_log = normalized_request.provider
            model_for_log = normalized_request.model
            update_request_context(provider=provider_for_log, model=model_for_log)

            log_service_request(
                provider=normalized_request.provider,
                model=normalized_request.model,
                stream=normalized_request.stream,
                message_count=len(normalized_request.messages),
                used_context_history=normalized_request.metadata.get("used_context_history"),
            )

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

    def chat_from_user_prompt(
        self,
        user_prompt: str,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        stream: bool = False,
        session_id: str | None = None,
        conversation_id: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        assembled_request, normalized_session_id = self._request_assembler.assemble_from_user_prompt(
            user_prompt=user_prompt,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            stream=stream,
            session_id=session_id,
            conversation_id=conversation_id,
            request_id=request_id,
            metadata=metadata,
            context_manager=self._context_manager,
        )

        response = self.chat(assembled_request)

        if normalized_session_id:
            self._context_manager.append_user_message(normalized_session_id, user_prompt)
            self._context_manager.append_assistant_message(
                normalized_session_id,
                response.content,
            )

        return response


def _log_service_exception(
    exc: BaseException,
    *,
    provider: str | None,
    model: str | None,
    started_at: float,
) -> None:
    log_exception(
        exc,
        event="service.chat.error",
        message="Service failed to complete chat request.",
        logger=_service_logger,
        provider=provider,
        model=model,
        latency_ms=round((perf_counter() - started_at) * 1000, 2),
    )

