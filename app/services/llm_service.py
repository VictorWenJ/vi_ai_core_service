"""Backward-compatible LLM service export.

Phase 1 keeps `LLMService` as stable import path while orchestration is
implemented in `ChatService`.
"""

from __future__ import annotations

from app.services.chat_service import ChatService


class LLMService(ChatService):
    """Compatibility alias for chat orchestration service."""

