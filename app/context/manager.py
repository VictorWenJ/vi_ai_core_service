"""上下文管理器。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any
from uuid import uuid4

from app.config import AppConfig, ContextMemoryConfig
from app.context.memory_reducer import BaseWorkingMemoryReducer, RuleBasedWorkingMemoryReducer
from app.context.models import (
    ContextMessage,
    ContextWindow,
    RollingSummaryState,
    normalize_conversation_scope,
    now_utc_iso,
)
from app.context.policies.tokenizer import BaseTokenCounter, build_default_token_counter
from app.context.stores.base import BaseContextStore
from app.context.stores.factory import build_context_store
from app.context.stores.in_memory import InMemoryContextStore
from app.observability import log_report


@dataclass(frozen=True)
class RecentRawCompactionResult:
    applied: bool
    compacted_messages: list[ContextMessage]
    recent_raw_messages: list[ContextMessage]
    recent_raw_token_count: int
    budget_exceeded_after_compaction: bool


class ContextManager:
    def __init__(
        self,
        store: BaseContextStore | None = None,
        memory_reducer: BaseWorkingMemoryReducer | None = None,
        token_counter: BaseTokenCounter | None = None,
    ) -> None:
        self._store = store or InMemoryContextStore()
        self._memory_reducer = memory_reducer or RuleBasedWorkingMemoryReducer(
            max_items_per_section=5,
            max_value_chars=160,
        )
        self._token_counter = token_counter or build_default_token_counter()

    @classmethod
    def from_app_config(cls, app_config: AppConfig) -> "ContextManager":
        return cls(
            store=build_context_store(app_config),
            memory_reducer=RuleBasedWorkingMemoryReducer(
                max_items_per_section=app_config.context_memory_config.working_memory_max_items_per_section,
                max_value_chars=app_config.context_memory_config.working_memory_max_value_chars,
            ),
            token_counter=build_default_token_counter(
                message_overhead_tokens=app_config.context_policy_config.message_overhead_tokens
            ),
        )

    @property
    def backend_name(self) -> str:
        return self._store.backend_name

    def get_context(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        return self._store.get_window(session_id, conversation_id)

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        conversation_id: str | None = None,
        *,
        message_id: str | None = None,
        status: str | None = None,
        finish_reason: str | None = None,
        error_code: str | None = None,
    ) -> ContextWindow:
        return self._store.append_message(
            session_id=session_id,
            conversation_id=conversation_id,
            message=ContextMessage(
                role=role,
                content=content,
                metadata=dict(metadata or {}),
                message_id=message_id,
                status=status or "completed",
                finish_reason=finish_reason,
                error_code=error_code,
                updated_at=now_utc_iso(),
            ),
        )

    def append_user_message(
        self,
        session_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        conversation_id: str | None = None,
        *,
        message_id: str | None = None,
    ) -> ContextWindow:
        return self.append_message(
            session_id=session_id,
            role="user",
            content=content,
            metadata=metadata,
            conversation_id=conversation_id,
            message_id=message_id,
            status="completed",
        )

    def append_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        conversation_id: str | None = None,
        *,
        message_id: str | None = None,
        status: str = "completed",
        finish_reason: str | None = None,
        error_code: str | None = None,
    ) -> ContextWindow:
        return self.append_message(
            session_id=session_id,
            role="assistant",
            content=content,
            metadata=metadata,
            conversation_id=conversation_id,
            message_id=message_id,
            status=status,
            finish_reason=finish_reason,
            error_code=error_code,
        )

    def create_assistant_placeholder(
        self,
        *,
        session_id: str,
        conversation_id: str | None,
        assistant_message_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContextWindow:
        return self.append_assistant_message(
            session_id=session_id,
            conversation_id=conversation_id,
            content="",
            metadata=metadata,
            message_id=assistant_message_id,
            status="created",
        )

    def update_assistant_stream_delta(
        self,
        *,
        session_id: str,
        conversation_id: str | None,
        assistant_message_id: str,
        delta: str,
    ) -> ContextWindow:
        window = self.get_context(session_id, conversation_id)
        index = self._find_message_index(window, assistant_message_id)
        if index is None:
            raise ValueError(f"未找到 assistant message_id='{assistant_message_id}'。")

        target = window.messages[index]
        window.messages[index] = replace(
            target,
            content=f"{target.content}{delta}",
            status="streaming",
            updated_at=now_utc_iso(),
        )
        return self.update_context_window(window)

    def finalize_assistant_message(
        self,
        *,
        session_id: str,
        conversation_id: str | None,
        assistant_message_id: str,
        status: str,
        content: str,
        finish_reason: str | None = None,
        error_code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContextWindow:
        window = self.get_context(session_id, conversation_id)
        index = self._find_message_index(window, assistant_message_id)
        if index is None:
            raise ValueError(f"未找到 assistant message_id='{assistant_message_id}'。")

        target = window.messages[index]
        merged_metadata = {**target.metadata, **dict(metadata or {})}
        window.messages[index] = replace(
            target,
            content=content,
            status=status,
            finish_reason=finish_reason,
            error_code=error_code,
            metadata=merged_metadata,
            updated_at=now_utc_iso(),
        )
        return self.update_context_window(window)

    def update_after_stream_completion(
        self,
        *,
        session_id: str,
        conversation_id: str | None,
        user_message_id: str,
        assistant_message_id: str,
        memory_config: ContextMemoryConfig,
    ) -> ContextWindow:
        scope = normalize_conversation_scope(conversation_id)
        window = self.get_context(session_id, scope)

        user_message = self._find_message(window, user_message_id)
        if user_message is None:
            raise ValueError(f"未找到 user message_id='{user_message_id}'。")

        assistant_message = self._find_message(window, assistant_message_id)
        if assistant_message is None:
            raise ValueError(f"未找到 assistant message_id='{assistant_message_id}'。")

        if assistant_message.status != "completed":
            return window

        return self._apply_layered_memory_pipeline(
            window=window,
            session_id=session_id,
            conversation_scope=scope,
            latest_user_message=user_message,
            latest_assistant_message=assistant_message,
            memory_config=memory_config,
        )

    def clear_context(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        return self._store.clear_window(session_id, conversation_id)

    def clear_session(self, session_id: str) -> ContextWindow:
        return self._store.reset_session(session_id)

    def reset_session(self, session_id: str) -> ContextWindow:
        return self._store.reset_session(session_id)

    def reset_conversation(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        return self._store.reset_conversation(
            session_id=session_id,
            conversation_id=conversation_id,
        )

    def replace_context_messages(
        self,
        session_id: str,
        messages: list[ContextMessage],
        conversation_id: str | None = None,
    ) -> ContextWindow:
        return self._store.replace_messages(
            session_id=session_id,
            conversation_id=conversation_id,
            messages=messages,
        )

    def update_context_window(self, window: ContextWindow) -> ContextWindow:
        return self._store.upsert_window(window)

    def update_after_chat_turn(
        self,
        *,
        session_id: str,
        conversation_id: str | None,
        user_content: str,
        assistant_content: str,
        metadata: dict[str, Any] | None,
        memory_config: ContextMemoryConfig,
    ) -> ContextWindow:
        # 1) 规范化会话作用域：统一使用 (session_id, conversation_id) 读取上下文窗口。
        scope = normalize_conversation_scope(conversation_id)
        window = self.get_context(session_id, scope)

        # 2) 为本轮对话构造 user / assistant 消息，并先追加到 recent raw 层。
        user_message = ContextMessage(
            role="user",
            content=user_content,
            metadata=dict(metadata or {}),
            message_id=f"um_{uuid4()}",
            status="completed",
        )
        assistant_message = ContextMessage(
            role="assistant",
            content=assistant_content,
            metadata=dict(metadata or {}),
            message_id=f"am_{uuid4()}",
            status="completed",
        )
        log_report(
            "ContextManager.update_after_chat_turn.context_message",
            {"user_message": user_message, "assistant_message": assistant_message},
        )
        window.messages.extend([user_message, assistant_message])

        return self._apply_layered_memory_pipeline(
            window=window,
            session_id=session_id,
            conversation_scope=scope,
            latest_user_message=user_message,
            latest_assistant_message=assistant_message,
            memory_config=memory_config,
        )

    def _apply_layered_memory_pipeline(
        self,
        *,
        window: ContextWindow,
        session_id: str,
        conversation_scope: str,
        latest_user_message: ContextMessage,
        latest_assistant_message: ContextMessage,
        memory_config: ContextMemoryConfig,
    ) -> ContextWindow:
        # 3) 对 recent raw 层执行预算治理：
        # - 在 token 超预算时，从最旧消息开始压缩（移出 recent raw）；
        # - 至少保留 min_keep_messages 条最近消息；
        # - 返回压缩结果与压缩后 token 统计。
        compaction_result = self._compact_recent_raw_messages(
            messages=window.messages,
            max_token_budget=memory_config.recent_raw_max_token_budget,
            min_keep_messages=memory_config.recent_raw_min_keep_messages,
            enabled=memory_config.layered_memory_enabled,
        )
        log_report(
            "ContextManager.update_after_chat_turn.compaction_result",
            compaction_result,
        )
        window.messages = compaction_result.recent_raw_messages

        # 4) 若开启 rolling summary，且本轮确实有被压出的旧消息，
        # 则把被压出片段合并进 rolling summary（确定性合并，不调用外部 LLM）。
        rolling_summary_state = None
        if memory_config.rolling_summary_enabled and compaction_result.compacted_messages:
            rolling_summary_state = self._merge_rolling_summary(
                previous=window.rolling_summary,
                compacted_messages=compaction_result.compacted_messages,
                max_chars=memory_config.rolling_summary_max_chars,
            )
            window.rolling_summary = rolling_summary_state
        log_report(
            "ContextManager.update_after_chat_turn.rolling_summary_state",
            rolling_summary_state,
        )

        # 5) 若开启 working memory，则由 reducer 结合“上一状态 + 本轮 user/assistant”
        # 生成新的结构化工作记忆（去重、限长、空值保护由 reducer 负责）。
        working_memory_state = None
        if memory_config.working_memory_enabled:
            working_memory_state = self._memory_reducer.reduce(
                previous=window.working_memory,
                latest_user_message=latest_user_message,
                latest_assistant_message=latest_assistant_message,
            )
            window.working_memory = working_memory_state
        log_report(
            "ContextManager.update_after_chat_turn.working_memory_state",
            working_memory_state,
        )

        # 6) 写入本轮 runtime trace，便于 request_assembler / 日志侧观测。
        window.runtime_meta = {
            **window.runtime_meta,
            "scope": {
                "session_id": session_id,
                "conversation_id": conversation_scope,
            },
            "recent_raw_message_count": len(window.messages),
            "recent_raw_token_count": compaction_result.recent_raw_token_count,
            "compaction_applied": compaction_result.applied,
            "compacted_message_count": len(compaction_result.compacted_messages),
            "budget_exceeded_after_compaction": compaction_result.budget_exceeded_after_compaction,
            "rolling_summary_present": window.rolling_summary.has_content,
            "working_memory_fields_present": window.working_memory.non_empty_fields(),
            "layered_memory_updated_at": now_utc_iso(),
        }

        # 7) 通过统一 store contract 持久化更新后的 conversation-scoped 窗口。
        return self.update_context_window(window)

    def _compact_recent_raw_messages(
        self,
        *,
        messages: list[ContextMessage],
        max_token_budget: int,
        min_keep_messages: int,
        enabled: bool,
    ) -> RecentRawCompactionResult:
        recent_raw_messages = list(messages)
        if not enabled:
            token_count = self._token_counter.count_messages_tokens(recent_raw_messages)
            return RecentRawCompactionResult(
                applied=False,
                compacted_messages=[],
                recent_raw_messages=recent_raw_messages,
                recent_raw_token_count=token_count,
                budget_exceeded_after_compaction=token_count > max_token_budget,
            )

        if max_token_budget <= 0:
            raise ValueError("recent_raw_max_token_budget 必须大于 0。")
        if min_keep_messages <= 0:
            raise ValueError("recent_raw_min_keep_messages 必须大于 0。")

        compacted_messages: list[ContextMessage] = []
        while (
            len(recent_raw_messages) > min_keep_messages
            and self._token_counter.count_messages_tokens(recent_raw_messages) > max_token_budget
        ):
            compacted_messages.append(recent_raw_messages.pop(0))

        recent_raw_token_count = self._token_counter.count_messages_tokens(recent_raw_messages)
        return RecentRawCompactionResult(
            applied=bool(compacted_messages),
            compacted_messages=compacted_messages,
            recent_raw_messages=recent_raw_messages,
            recent_raw_token_count=recent_raw_token_count,
            budget_exceeded_after_compaction=recent_raw_token_count > max_token_budget,
        )

    def _merge_rolling_summary(
        self,
        *,
        previous: RollingSummaryState,
        compacted_messages: list[ContextMessage],
        max_chars: int,
    ) -> RollingSummaryState:
        if max_chars <= 0:
            raise ValueError("rolling_summary_max_chars 必须大于 0。")

        segment_summary = self._build_compaction_segment(compacted_messages)
        if not segment_summary:
            return previous

        if previous.has_content:
            merged_text = f"{previous.text}\n{segment_summary}"
        else:
            merged_text = segment_summary

        if len(merged_text) > max_chars:
            merged_text = merged_text[-max_chars:]

        return RollingSummaryState(
            text=merged_text,
            updated_at=now_utc_iso(),
            source_message_count=previous.source_message_count + len(compacted_messages),
        )

    @staticmethod
    def _build_compaction_segment(compacted_messages: list[ContextMessage]) -> str:
        if not compacted_messages:
            return ""
        preview_chunks: list[str] = []
        for message in compacted_messages[-3:]:
            normalized = " ".join(message.content.split())
            if not normalized:
                continue
            preview_chunks.append(f"{message.role}: {normalized[:80]}")
        preview = " | ".join(preview_chunks)
        base_text = f"[rolling_compaction] compacted_messages={len(compacted_messages)}"
        if preview:
            base_text = f"{base_text} preview={preview}"
        return base_text

    @staticmethod
    def _find_message_index(window: ContextWindow, message_id: str) -> int | None:
        for index in range(len(window.messages) - 1, -1, -1):
            message = window.messages[index]
            if message.message_id == message_id:
                return index
        return None

    @staticmethod
    def _find_message(window: ContextWindow, message_id: str) -> ContextMessage | None:
        for message in reversed(window.messages):
            if message.message_id == message_id:
                return message
        return None
