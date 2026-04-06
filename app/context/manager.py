"""Context manager skeleton."""

from __future__ import annotations

from app.context.models import ContextMessage, ContextWindow
from app.context.stores.base import BaseContextStore
from app.context.stores.in_memory import InMemoryContextStore


class ContextManager:
    def __init__(self, store: BaseContextStore | None = None) -> None:
        self._store = store or InMemoryContextStore()

    def get_context(self, session_id: str) -> ContextWindow:
        return self._store.get_window(session_id)

    def append_message(self, session_id: str, role: str, content: str) -> ContextWindow:
        return self._store.append_message(
            session_id=session_id,
            message=ContextMessage(role=role, content=content),
        )

    def append_user_message(self, session_id: str, content: str) -> ContextWindow:
        return self.append_message(session_id=session_id, role="user", content=content)

    def append_assistant_message(self, session_id: str, content: str) -> ContextWindow:
        return self.append_message(
            session_id=session_id,
            role="assistant",
            content=content,
        )

    def clear_context(self, session_id: str) -> ContextWindow:
        return self._store.clear_window(session_id)

    def replace_context_messages(
        self,
        session_id: str,
        messages: list[ContextMessage],
    ) -> ContextWindow:
        return self._store.replace_messages(session_id=session_id, messages=messages)
