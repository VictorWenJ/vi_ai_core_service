"""Request assembly and normalization helpers for chat orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.api.schemas import ChatRequest
from app.config import AppConfig
from app.context.manager import ContextManager
from app.context.models import ContextWindow
from app.context.policies.context_policy import (
    ContextPolicyExecutionResult,
    ContextPolicyPipeline,
)
from app.context.policies.defaults import build_default_context_policy_pipeline
from app.observability.log_until import log_report
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
            context_policy_pipeline: ContextPolicyPipeline | None = None,
    ) -> None:
        self._config = config
        self._prompt_service = prompt_service
        self._context_policy_pipeline = (
                context_policy_pipeline or build_default_context_policy_pipeline()
        )

    def assemble_from_user_prompt(self, request: ChatRequest, context_manager: ContextManager) -> LLMRequest:
        normalized_session_id = normalize_optional_text(request.session_id)
        normalized_conversation_id = normalize_optional_text(request.conversation_id)
        normalized_request_id = normalize_optional_text(request.request_id)
        use_server_history = bool(normalized_session_id)

        log_report("ChatRequestAssembler.assemble_from_user_prompt.normalized_data",
                   dict(normalized_session_id=normalized_session_id,
                        normalized_conversation_id=normalized_conversation_id,
                        normalized_request_id=normalized_request_id,
                        use_server_history=use_server_history))

        context_window = ContextWindow(
            session_id=normalized_session_id or "",
            messages=[],
        )
        if use_server_history:
            context_window = context_manager.get_context(normalized_session_id or "")
        log_report("ChatRequestAssembler.assemble_from_user_prompt.context_window", context_window)

        policy_result = self._context_policy_pipeline.run(context_window)
        log_report("ChatRequestAssembler.assemble_from_user_prompt.policy_result", policy_result)

        history_messages = [
            LLMMessage(role=message["role"], content=message["content"])
            for message in policy_result.serialized_messages
        ]

        resolved_system_prompt = request.system_prompt
        if resolved_system_prompt is None:
            resolved_system_prompt = self._prompt_service.get_default_system_prompt()

        assembled_messages = self._prompt_service.build_messages(
            system_prompt=resolved_system_prompt,
            user_prompt=request.user_prompt,
            messages=history_messages,
        )

        request_metadata = dict(request.metadata or {})
        if normalized_conversation_id:
            request_metadata["conversation_id"] = normalized_conversation_id
        if normalized_request_id:
            request_metadata["request_id"] = normalized_request_id
        if normalized_session_id:
            request_metadata["session_id"] = normalized_session_id
        context_trace = build_context_assembly_trace(
            use_server_history=use_server_history,
            policy_result=policy_result,
        )
        request_metadata["context_assembly"] = context_trace
        request_metadata["used_context_history"] = context_trace

        return LLMRequest(
            provider=request.provider,
            model=request.model,
            messages=assembled_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
            session_id=normalized_session_id,
            conversation_id=normalized_conversation_id,
            request_id=normalized_request_id,
            metadata=request_metadata,
        )

    def normalize_request(
            self,
            llm_request: LLMRequest,
            *,
            provider_registry: ProviderRegistry,
    ) -> LLMRequest:


        provider_name = llm_request.provider or self._config.default_provider
        provider_config = provider_registry.get_provider_config(provider_name)
        model_name = llm_request.model or provider_config.default_model

        if not model_name:
            env_var_name = f"{provider_name.upper()}_DEFAULT_MODEL"
            raise ServiceValidationError(
                f"Model is required for provider '{provider_name}'. "
                f"Provide it in the request or configure {env_var_name}."
            )

        if llm_request.stream:
            raise ServiceNotImplementedError(
                "Streaming is intentionally out of scope for this Phase 1 implementation."
            )

        normalized_messages = list(llm_request.messages)
        if llm_request.system_prompt:
            normalized_messages = self._prompt_service.build_messages(
                system_prompt=llm_request.system_prompt,
                messages=normalized_messages,
            )

        if not normalized_messages:
            raise ServiceValidationError("At least one message is required.")

        return replace(
            llm_request,
            provider=provider_name,
            model=model_name,
            messages=normalized_messages,
        )


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped_value = value.strip()
    return stripped_value or None


def build_context_assembly_trace(
        *,
        use_server_history: bool,
        policy_result: ContextPolicyExecutionResult,
) -> dict[str, Any]:
    selection = policy_result.selection
    truncation = policy_result.truncation
    serialized_count = len(policy_result.serialized_messages)
    return {
        "enabled": use_server_history,
        "raw_message_count": selection.source_message_count,
        "selected_message_count": selection.selected_message_count,
        "dropped_message_count": selection.dropped_message_count,
        "truncated_message_count": truncation.truncated_message_count,
        "serialized_message_count": serialized_count,
        "selection_policy": selection.selection_policy,
        "truncation_policy": truncation.truncation_policy,
        "serialization_policy": policy_result.serialization_policy,
    }
