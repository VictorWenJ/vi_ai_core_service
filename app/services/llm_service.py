"""Service-layer orchestration for LLM chat requests."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.config import AppConfig, ConfigError
from app.context.manager import ContextManager
from app.providers.base import (
    ProviderConfigurationError,
    ProviderInvocationError,
    ProviderNotImplementedError,
    StreamNotImplementedError,
)
from app.providers.registry import ProviderRegistry
from app.schemas.llm_request import LLMMessage, LLMRequest
from app.schemas.llm_response import LLMResponse
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceError,
    ServiceNotImplementedError,
    ServiceValidationError,
)
from app.services.prompt_service import PromptService


class LLMService:
    """Business-facing entrypoint for Phase 1 chat requests."""

    def __init__(
        self,
        config: AppConfig,
        registry: ProviderRegistry | None = None,
        prompt_service: PromptService | None = None,
        context_manager: ContextManager | None = None,
    ) -> None:
        self._config = config
        self._registry = registry or ProviderRegistry(config)
        self._prompt_service = prompt_service or PromptService()
        self._context_manager = context_manager or ContextManager()

    def chat(self, request: LLMRequest) -> LLMResponse:
        try:
            normalized_request = self._normalize_request(request)
            provider = self._registry.get_provider(normalized_request.provider or "")
            return provider.chat(normalized_request)
        except ServiceError:
            raise
        except ProviderConfigurationError as exc:
            raise ServiceConfigurationError(str(exc)) from exc
        except ConfigError as exc:
            raise ServiceConfigurationError(str(exc)) from exc
        except ProviderInvocationError as exc:
            raise ServiceDependencyError(str(exc)) from exc
        except (ProviderNotImplementedError, StreamNotImplementedError, NotImplementedError) as exc:
            raise ServiceNotImplementedError(str(exc)) from exc
        except ValueError as exc:
            raise ServiceValidationError(str(exc)) from exc

    def chat_from_user_prompt(
        self,
        user_prompt: str,
        provider: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        stream: bool = False,
        session_id: str | None = None,
        conversation_id: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        normalized_session_id = _normalize_optional_text(session_id)
        normalized_conversation_id = _normalize_optional_text(conversation_id)
        normalized_request_id = _normalize_optional_text(request_id)

        history_messages: list[LLMMessage] = []
        if normalized_session_id:
            context_window = self._context_manager.get_context(normalized_session_id)
            history_messages = [
                LLMMessage(role=message.role, content=message.content)
                for message in context_window.messages
            ]

        assembled_messages = self._prompt_service.build_chat_messages(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            messages=history_messages,
        )

        request_metadata = dict(metadata or {})
        if normalized_conversation_id:
            request_metadata["conversation_id"] = normalized_conversation_id
        if normalized_request_id:
            request_metadata["request_id"] = normalized_request_id
        if normalized_session_id:
            request_metadata["session_id"] = normalized_session_id

        response = self.chat(
            LLMRequest(
                provider=provider,
                model=model,
                messages=assembled_messages,
                stream=stream,
                session_id=normalized_session_id,
                conversation_id=normalized_conversation_id,
                request_id=normalized_request_id,
                metadata=request_metadata,
            )
        )

        if normalized_session_id:
            self._context_manager.append_user_message(normalized_session_id, user_prompt)
            self._context_manager.append_assistant_message(
                normalized_session_id,
                response.content,
            )

        return response

    def _normalize_request(self, request: LLMRequest) -> LLMRequest:
        provider_name = request.provider or self._config.default_provider
        provider_config = self._registry.get_provider_config(provider_name)
        model_name = request.model or provider_config.default_model

        if not model_name:
            env_var_name = f"{provider_name.upper()}_DEFAULT_MODEL"
            raise ServiceValidationError(
                f"Model is required for provider '{provider_name}'. "
                f"Provide it in the request or configure {env_var_name}."
            )

        if request.stream:
            raise ServiceNotImplementedError(
                "Streaming is intentionally out of scope for this Phase 1 implementation."
            )

        normalized_messages = list(request.messages)
        if request.system_prompt:
            normalized_messages = self._prompt_service.build_messages(
                system_prompt=request.system_prompt,
                messages=normalized_messages,
            )

        if not normalized_messages:
            raise ServiceValidationError("At least one message is required.")

        return replace(
            request,
            provider=provider_name,
            model=model_name,
            messages=normalized_messages,
        )


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped_value = value.strip()
    return stripped_value or None
