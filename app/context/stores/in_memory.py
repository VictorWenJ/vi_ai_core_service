"""In-memory context store skeleton."""

from __future__ import annotations

from app.context.models import ContextMessage, ContextWindow
from app.context.stores.base import BaseContextStore


class InMemoryContextStore(BaseContextStore):
    def __init__(self) -> None:
        self._windows: dict[str, ContextWindow] = {}

    def get_window(self, session_id: str) -> ContextWindow:
        return self._windows.setdefault(session_id, ContextWindow(session_id=session_id))

    def append_message(self, session_id: str, message: ContextMessage) -> ContextWindow:
        window = self.get_window(session_id)
        window.messages.append(message)
        return window
