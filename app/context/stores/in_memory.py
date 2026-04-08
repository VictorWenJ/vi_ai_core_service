"""内存上下文存储骨架。"""

from __future__ import annotations

from app.context.models import ContextMessage, ContextWindow
from app.context.stores.base import BaseContextStore


class InMemoryContextStore(BaseContextStore):
    def __init__(self) -> None:
        self._windows: dict[str, ContextWindow] = {}

    def get_window(self, session_id: str) -> ContextWindow:
        existed = session_id in self._windows
        window = self._windows.setdefault(session_id, ContextWindow(session_id=session_id))
        return window

    def append_message(self, session_id: str, message: ContextMessage) -> ContextWindow:
        window = self._windows.setdefault(session_id, ContextWindow(session_id=session_id))
        window.messages.append(message)
        return window

    def clear_window(self, session_id: str) -> ContextWindow:
        window = self._windows.setdefault(session_id, ContextWindow(session_id=session_id))
        window.messages.clear()
        return window

    def reset_conversation(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        window = self._windows.setdefault(session_id, ContextWindow(session_id=session_id))
        if conversation_id is None:
            window.messages.clear()
            return window

        window.messages = [
            message
            for message in window.messages
            if message.metadata.get("conversation_id") != conversation_id
        ]
        return window

    def replace_messages(
        self,
        session_id: str,
        messages: list[ContextMessage],
    ) -> ContextWindow:
        copied_messages = list(messages)
        window = self._windows.setdefault(session_id, ContextWindow(session_id=session_id))
        window.messages = copied_messages
        return window
