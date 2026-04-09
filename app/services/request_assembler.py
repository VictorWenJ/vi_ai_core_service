"""聊天编排的请求装配与规范化辅助。"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.api.schemas import ChatRequest
from app.config import AppConfig
from app.context.manager import ContextManager
from app.context.models import ContextMessage, ContextWindow, normalize_conversation_scope
from app.context.policies.context_policy import (
    ContextPolicyExecutionResult,
    ContextPolicyPipeline,
)
from app.context.policies.defaults import build_default_context_policy_pipeline
from app.context.rendering import (
    render_rolling_summary_block,
    render_working_memory_block,
)
from app.observability.log_until import log_report
from app.providers.registry import ProviderRegistry
from app.schemas.llm_request import LLMMessage, LLMRequest
from app.services.errors import ServiceNotImplementedError, ServiceValidationError
from app.services.prompt_service import PromptService


class ChatRequestAssembler:
    """从 API 输入装配聊天请求并规范化标准请求。"""

    def __init__(
        self,
        app_config: AppConfig,
        prompt_service: PromptService,
        context_policy_pipeline: ContextPolicyPipeline | None = None,
    ) -> None:
        self._config = app_config
        self._prompt_service = prompt_service
        self._context_policy_pipeline = (
            context_policy_pipeline
            or build_default_context_policy_pipeline(app_config.context_policy_config)
        )

    def assemble_from_user_prompt(self, request: ChatRequest, context_manager: ContextManager) -> LLMRequest:
        normalized_session_id = normalize_optional_text(request.session_id)
        normalized_conversation_id = normalize_optional_text(request.conversation_id)
        normalized_request_id = normalize_optional_text(request.request_id)
        use_server_history = bool(normalized_session_id)

        log_report(
            "ChatRequestAssembler.assemble_from_user_prompt.normalized_data",
            {
                "normalized_session_id": normalized_session_id,
                "normalized_conversation_id": normalized_conversation_id,
                "normalized_request_id": normalized_request_id,
                "use_server_history": use_server_history,
            },
        )

        context_window, ignored_non_completed_assistant_count = self.get_context_window(
            context_manager,
            normalized_conversation_id,
            normalized_session_id,
            use_server_history,
        )
        log_report("ChatRequestAssembler.assemble_from_user_prompt.context_window", context_window)

        policy_result = self._context_policy_pipeline.run(context_window)
        log_report("ChatRequestAssembler.assemble_from_user_prompt.policy_result", policy_result)

        recent_raw_messages = [
            LLMMessage(role=message["role"], content=message["content"])
            for message in policy_result.serialized_messages
        ]

        # 分层短期记忆组装（Layered Memory）：
        layered_messages = self.build_layered_messages(context_window)
        log_report("ChatRequestAssembler.assemble_from_user_prompt.layered_messages", layered_messages)

        history_messages = layered_messages + recent_raw_messages
        log_report("ChatRequestAssembler.assemble_from_user_prompt.history_messages", history_messages)

        resolved_system_prompt = request.system_prompt
        if resolved_system_prompt is None:
            resolved_system_prompt = self._prompt_service.get_default_system_prompt()

        assembled_messages = self._prompt_service.build_messages(
            system_prompt=resolved_system_prompt,
            user_prompt=request.user_prompt,
            messages=history_messages,
        )
        log_report("ChatRequestAssembler.assemble_from_user_prompt.assembled_messages", assembled_messages)

        request_metadata = self.build_request_metadata(
            context_window=context_window,
            normalized_conversation_id=normalized_conversation_id,
            normalized_request_id=normalized_request_id,
            normalized_session_id=normalized_session_id,
            policy_result=policy_result,
            request=request,
            use_server_history=use_server_history,
            ignored_non_completed_assistant_count=ignored_non_completed_assistant_count,
        )

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

    @staticmethod
    def build_request_metadata(
        *,
        context_window: ContextWindow,
        normalized_conversation_id: str | None,
        normalized_request_id: str | None,
        normalized_session_id: str | None,
        policy_result: ContextPolicyExecutionResult,
        request: ChatRequest,
        use_server_history: bool,
        ignored_non_completed_assistant_count: int,
    ) -> dict[str, Any]:
        request_metadata = dict(request.metadata or {})
        if normalized_conversation_id:
            request_metadata["conversation_id"] = normalized_conversation_id
        if normalized_request_id:
            request_metadata["request_id"] = normalized_request_id
        if normalized_session_id:
            request_metadata["session_id"] = normalized_session_id
        context_trace = build_context_assembly_trace(
            use_server_history=use_server_history,
            session_id=normalized_session_id,
            conversation_id=normalized_conversation_id,
            context_window=context_window,
            policy_result=policy_result,
            ignored_non_completed_assistant_count=ignored_non_completed_assistant_count,
        )
        request_metadata["context_assembly"] = context_trace
        request_metadata["used_context_history"] = context_trace
        return request_metadata

    @staticmethod
    def build_layered_messages(context_window: ContextWindow) -> list[LLMMessage]:
        # 1) working_memory 先入列，提供当前会话结构化状态；
        # 2) rolling_summary 后入列，提供被压缩历史的背景信息；
        # 3) recent_raw_messages 最后拼接，保留最近原始对话上下文。
        layered_messages: list[LLMMessage] = []

        # 将 working memory 渲染为系统提示块；为空时跳过，避免噪音注入。
        working_memory_block = render_working_memory_block(context_window.working_memory)
        if working_memory_block:
            layered_messages.append(LLMMessage(role="system", content=working_memory_block))

        # 将 rolling summary 渲染为系统提示块；为空时跳过。
        rolling_summary_block = render_rolling_summary_block(context_window.rolling_summary)
        if rolling_summary_block:
            layered_messages.append(LLMMessage(role="system", content=rolling_summary_block))

        return layered_messages

    @staticmethod
    def get_context_window(
        context_manager: ContextManager,
        normalized_conversation_id: str | None,
        normalized_session_id: str | None,
        use_server_history: bool,
    ) -> tuple[ContextWindow, int]:
        context_window = ContextWindow(
            session_id=normalized_session_id or "",
            conversation_id=normalize_conversation_scope(normalized_conversation_id),
            messages=[],
        )
        ignored_non_completed_assistant_count = 0
        if use_server_history:
            original_window = context_manager.get_context(
                normalized_session_id or "",
                normalized_conversation_id,
            )
            filtered_messages, ignored_non_completed_assistant_count = filter_messages_for_request_assembly(
                original_window.messages
            )
            context_window = ContextWindow(
                session_id=original_window.session_id,
                conversation_id=original_window.conversation_id,
                messages=filtered_messages,
                rolling_summary=original_window.rolling_summary,
                working_memory=original_window.working_memory,
                runtime_meta=original_window.runtime_meta,
            )
        return context_window, ignored_non_completed_assistant_count

    def normalize_request(
        self,
        llm_request: LLMRequest,
        *,
        provider_registry: ProviderRegistry,
        allow_stream: bool = False,
    ) -> LLMRequest:
        provider_name = llm_request.provider or self._config.default_provider
        provider_config = provider_registry.get_provider_config(provider_name)
        model_name = llm_request.model or provider_config.default_model

        if not model_name:
            env_var_name = f"{provider_name.upper()}_DEFAULT_MODEL"
            raise ServiceValidationError(
                f"Provider '{provider_name}' 需要模型。"
                f"请在请求中提供，或配置 {env_var_name}。"
            )

        if llm_request.stream and not allow_stream:
            raise ServiceNotImplementedError(
                "当前同步 chat 链路不支持流式能力。"
            )

        normalized_messages = list(llm_request.messages)
        if llm_request.system_prompt:
            normalized_messages = self._prompt_service.build_messages(
                system_prompt=llm_request.system_prompt,
                messages=normalized_messages,
            )

        if not normalized_messages:
            raise ServiceValidationError("至少需要一条消息。")

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


def filter_messages_for_request_assembly(
    messages: list[ContextMessage],
) -> tuple[list[ContextMessage], int]:
    filtered_messages: list[ContextMessage] = []
    ignored_non_completed_assistant_count = 0

    for message in messages:
        if message.role != "assistant":
            filtered_messages.append(message)
            continue

        if message.status in {"completed", ""}:
            filtered_messages.append(message)
            continue

        ignored_non_completed_assistant_count += 1

    return filtered_messages, ignored_non_completed_assistant_count


def build_context_assembly_trace(
    *,
    use_server_history: bool,
    session_id: str | None,
    conversation_id: str | None,
    context_window: ContextWindow,
    policy_result: ContextPolicyExecutionResult,
    ignored_non_completed_assistant_count: int,
) -> dict[str, Any]:
    selection = policy_result.selection
    truncation = policy_result.truncation
    summary = policy_result.summary
    serialized_count = len(policy_result.serialized_messages)
    selection_dropped_message_count = selection.dropped_message_count
    truncation_dropped_message_count = len(truncation.dropped_messages)
    summary_dropped_message_count = summary.dropped_message_count
    total_dropped_message_count = (
        selection_dropped_message_count
        + truncation_dropped_message_count
        + summary_dropped_message_count
    )
    runtime_meta = context_window.runtime_meta or {}
    return {
        "enabled": use_server_history,
        "session_id": session_id,
        "conversation_id": conversation_id,
        "context_scope": {
            "session_id": context_window.session_id,
            "conversation_id": context_window.conversation_id,
        },
        "recent_raw_message_count": context_window.message_count,
        "rolling_summary_present": context_window.rolling_summary.has_content,
        "working_memory_fields_present": context_window.working_memory.non_empty_fields(),
        "compaction_applied": bool(runtime_meta.get("compaction_applied", False)),
        "compacted_message_count": int(runtime_meta.get("compacted_message_count", 0)),
        "ignored_non_completed_assistant_count": ignored_non_completed_assistant_count,
        "source_message_count": selection.source_message_count,
        "source_token_count": selection.source_token_count,
        "selection_selected_message_count": selection.selected_message_count,
        "selection_dropped_message_count": selection_dropped_message_count,
        "selection_token_budget": selection.token_budget,
        "selection_selected_token_count": selection.selected_token_count,
        "truncation_input_message_count": truncation.input_message_count,
        "truncation_output_message_count": truncation.final_message_count,
        "truncation_dropped_message_count": truncation_dropped_message_count,
        "truncation_input_token_count": truncation.input_token_count,
        "truncation_final_token_count": truncation.final_token_count,
        "truncation_token_budget": truncation.truncation_token_budget,
        "truncation_applied": truncation.truncation_applied,
        "summary_input_message_count": summary.input_message_count,
        "summary_output_message_count": summary.final_message_count,
        "summary_dropped_message_count": summary_dropped_message_count,
        "summary_input_token_count": summary.input_token_count,
        "summary_final_token_count": summary.final_token_count,
        "summary_applied": summary.summary_applied,
        "total_dropped_message_count": total_dropped_message_count,
        "selection_policy": selection.selection_policy,
        "truncation_policy": truncation.truncation_policy,
        "summary_policy": summary.summary_policy,
        "serialization_policy": policy_result.serialization_policy,
        "token_counter": policy_result.token_counter,
        "serialized_message_count": serialized_count,
        # 为现有调用方/测试保留兼容别名。
        "total_messages_before_selection": selection.source_message_count,
        "raw_message_count": selection.source_message_count,
        "selected_message_count": selection.selected_message_count,
        "dropped_message_count": total_dropped_message_count,
        "truncated_message_count": truncation.truncated_message_count,
        "token_budget": selection.token_budget,
        "selected_token_count": selection.selected_token_count,
        "final_token_count_after_truncation": truncation.final_token_count,
        "final_token_count_after_summary": summary.final_token_count,
    }
