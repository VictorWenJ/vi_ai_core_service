"""上下文存储后端基础接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.context.models import ContextMessage, ContextWindow


class BaseContextStore(ABC):
    backend_name: str = "unknown"

    @abstractmethod
    def get_window(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        raise NotImplementedError

    @abstractmethod
    def append_message(
        self,
        session_id: str,
        conversation_id: str | None,
        message: ContextMessage,
    ) -> ContextWindow:
        raise NotImplementedError

    @abstractmethod
    def clear_window(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        raise NotImplementedError

    @abstractmethod
    def reset_session(self, session_id: str) -> ContextWindow:
        raise NotImplementedError

    @abstractmethod
    def reset_conversation(
        self,
        session_id: str,
        conversation_id: str | None,
    ) -> ContextWindow:
        raise NotImplementedError

    @abstractmethod
    def replace_messages(
        self,
        session_id: str,
        conversation_id: str | None,
        messages: list[ContextMessage],
    ) -> ContextWindow:
        raise NotImplementedError

    @abstractmethod
    def upsert_window(self, window: ContextWindow) -> ContextWindow:
        raise NotImplementedError
