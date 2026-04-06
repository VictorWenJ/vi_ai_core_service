"""Request assembly and normalization helpers for chat orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.config import AppConfig
from app.context.manager import ContextManager
from app.context.models import ContextMessage
from app.providers.registry import ProviderRegistry
from app.schemas.llm_request import LLMMessage, LLMRequest
from app.services.errors import ServiceNotImplementedError, ServiceValidationError
from app.services.prompt_service import PromptService


class ChatRequestAssembler:
    """Assemble chat requests from API inputs and normalize canonical requests."""

    def __init__(
        self,
        config: AppConfig,
        prompt_service: PromptService,
    ) -> None:
        self._config = config
        self._prompt_service = prompt_service

    def assemble_from_user_prompt(
        self,
        *,
        user_prompt: str,
        provider: str | None,
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
        system_prompt: str | None,
        stream: bool,
        session_id: str | None,
        conversation_id: str | None,
        request_id: str | None,
        metadata: dict[str, Any] | None,
        context_manager: ContextManager,
    ) -> tuple[LLMRequest, str | None]:
        normalized_session_id = normalize_optional_text(session_id)
        normalized_conversation_id = normalize_optional_text(conversation_id)
        normalized_request_id = normalize_optional_text(request_id)

        history_messages: list[LLMMessage] = []
        if normalized_session_id:
            context_window = context_manager.get_context(normalized_session_id)
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
        request_metadata["used_context_history"] = {
            "enabled": bool(history_messages),
            "message_count": len(history_messages),
            "messages": serialize_context_messages(history_messages),
        }

        return (
            LLMRequest(
                provider=provider,
                model=model,
                messages=assembled_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                session_id=normalized_session_id,
                conversation_id=normalized_conversation_id,
                request_id=normalized_request_id,
                metadata=request_metadata,
            ),
            normalized_session_id,
        )

    def normalize_request(
        self,
        request: LLMRequest,
        *,
        registry: ProviderRegistry,
    ) -> LLMRequest:
        provider_name = request.provider or self._config.default_provider
        provider_config = registry.get_provider_config(provider_name)
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


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped_value = value.strip()
    return stripped_value or None


def serialize_context_messages(
    messages: list[LLMMessage | ContextMessage],
) -> list[dict[str, Any]]:
    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]

