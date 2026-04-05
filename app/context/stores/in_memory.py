"""In-memory context store skeleton."""

from __future__ import annotations

from app.context.models import ContextMessage, ContextWindow
from app.context.stores.base import BaseContextStore
from app.observability.logging_setup import get_logger

_context_store_logger = get_logger("context.in_memory")


class InMemoryContextStore(BaseContextStore):
    def __init__(self) -> None:
        self._windows: dict[str, ContextWindow] = {}

    def get_window(self, session_id: str) -> ContextWindow:
        existed = session_id in self._windows
        window = self._windows.setdefault(session_id, ContextWindow(session_id=session_id))
        _context_store_logger.info(
            "Context window fetched.",
            extra={
                "event": "context.window.get",
                "session_id": session_id,
                "window_exists": existed,
                "message_count": len(window.messages),
                "messages": _serialize_messages(window.messages),
            },
        )
        return window

    def append_message(self, session_id: str, message: ContextMessage) -> ContextWindow:
        window = self._windows.setdefault(session_id, ContextWindow(session_id=session_id))
        window.messages.append(message)
        _context_store_logger.info(
            "Context message appended.",
            extra={
                "event": "context.window.append",
                "session_id": session_id,
                "appended_role": message.role,
                "appended_content": message.content,
                "message_count": len(window.messages),
                "messages": _serialize_messages(window.messages),
            },
        )
        return window


def _serialize_messages(messages: list[ContextMessage]) -> list[dict[str, str]]:
    return [
        {
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in messages
    ]
