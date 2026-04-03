"""Base interface for context storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.context.models import ContextMessage, ContextWindow


class BaseContextStore(ABC):
    @abstractmethod
    def get_window(self, session_id: str) -> ContextWindow:
        raise NotImplementedError

    @abstractmethod
    def append_message(self, session_id: str, message: ContextMessage) -> ContextWindow:
        raise NotImplementedError
