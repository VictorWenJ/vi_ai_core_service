"""上下文管理器骨架。"""

from __future__ import annotations

from typing import Any

from app.config import AppConfig
from app.context.models import ContextMessage, ContextWindow
from app.context.stores.base import BaseContextStore
from app.context.stores.factory import build_context_store
from app.context.stores.in_memory import InMemoryContextStore


class ContextManager:
    def __init__(self, store: BaseContextStore | None = None) -> None:
        self._store = store or InMemoryContextStore()

    @classmethod
    def from_app_config(cls, app_config: AppConfig) -> "ContextManager":
        return cls(store=build_context_store(app_config))

    @property
    def backend_name(self) -> str:
        return self._store.backend_name

    def get_context(self, session_id: str) -> ContextWindow:
        return self._store.get_window(session_id)

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContextWindow:
        return self._store.append_message(
            session_id=session_id,
            message=ContextMessage(
                role=role,
                content=content,
                metadata=dict(metadata or {}),
            ),
        )

    def append_user_message(
        self,
        session_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContextWindow:
        return self.append_message(
            session_id=session_id,
            role="user",
            content=content,
            metadata=metadata,
        )

    def append_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContextWindow:
        return self.append_message(
            session_id=session_id,
            role="assistant",
            content=content,
            metadata=metadata,
        )

    def clear_context(self, session_id: str) -> ContextWindow:
        return self._store.clear_window(session_id)

    def clear_session(self, session_id: str) -> ContextWindow:
        return self._store.clear_window(session_id)

    def reset_session(self, session_id: str) -> ContextWindow:
        return self._store.clear_window(session_id)

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
    ) -> ContextWindow:
        return self._store.replace_messages(session_id=session_id, messages=messages)
