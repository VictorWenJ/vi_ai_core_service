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

    def append_user_message(self, session_id: str, content: str) -> ContextWindow:
        return self._store.append_message(
            session_id=session_id,
            message=ContextMessage(role="user", content=content),
        )

    def append_assistant_message(self, session_id: str, content: str) -> ContextWindow:
        return self._store.append_message(
            session_id=session_id,
            message=ContextMessage(role="assistant", content=content),
        )
