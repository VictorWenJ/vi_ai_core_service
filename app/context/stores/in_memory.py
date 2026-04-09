"""内存上下文存储骨架。"""

from __future__ import annotations

from copy import deepcopy

from app.context.models import (
    ContextMessage,
    ContextWindow,
    normalize_conversation_scope,
)
from app.context.stores.base import BaseContextStore


class InMemoryContextStore(BaseContextStore):
    backend_name = "memory"

    def __init__(self) -> None:
        self._windows: dict[str, dict[str, ContextWindow]] = {}

    def get_window(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        normalize_scope_conversation_id = normalize_conversation_scope(conversation_id)
        session_windows = self._windows.setdefault(session_id, {})
        window = session_windows.setdefault(
            normalize_scope_conversation_id,
            ContextWindow(session_id=session_id, conversation_id=normalize_scope_conversation_id),
        )
        return deepcopy(window)

    def append_message(
        self,
        session_id: str,
        conversation_id: str | None,
        message: ContextMessage,
    ) -> ContextWindow:
        window = self._get_or_create_window(session_id, conversation_id)
        window.messages.append(message)
        return deepcopy(window)

    def clear_window(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        window = self._get_or_create_window(session_id, conversation_id)
        window.messages.clear()
        window.rolling_summary.text = ""
        window.rolling_summary.updated_at = None
        window.rolling_summary.source_message_count = 0
        window.working_memory = type(window.working_memory)()
        window.runtime_meta = {}
        return deepcopy(window)

    def reset_session(self, session_id: str) -> ContextWindow:
        self._windows.pop(session_id, None)
        return ContextWindow(session_id=session_id)

    def reset_conversation(
        self,
        session_id: str,
        conversation_id: str | None,
    ) -> ContextWindow:
        scope = normalize_conversation_scope(conversation_id)
        session_windows = self._windows.setdefault(session_id, {})
        session_windows.pop(scope, None)
        return ContextWindow(session_id=session_id, conversation_id=scope)

    def replace_messages(
        self,
        session_id: str,
        conversation_id: str | None,
        messages: list[ContextMessage],
    ) -> ContextWindow:
        copied_messages = deepcopy(list(messages))
        window = self._get_or_create_window(session_id, conversation_id)
        window.messages = copied_messages
        return deepcopy(window)

    def upsert_window(self, window: ContextWindow) -> ContextWindow:
        scope = normalize_conversation_scope(window.conversation_id)
        session_windows = self._windows.setdefault(window.session_id, {})
        session_windows[scope] = deepcopy(window)
        return deepcopy(session_windows[scope])

    def _get_or_create_window(
        self,
        session_id: str,
        conversation_id: str | None,
    ) -> ContextWindow:
        scope = normalize_conversation_scope(conversation_id)
        session_windows = self._windows.setdefault(session_id, {})
        return session_windows.setdefault(
            scope,
            ContextWindow(session_id=session_id, conversation_id=scope),
        )
