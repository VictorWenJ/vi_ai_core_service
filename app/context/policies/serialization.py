"""Serialization policies for context history messages."""

from __future__ import annotations

from app.context.models import ContextTruncationResult
from app.context.policies.base import HistorySerializationPolicy


class DefaultHistorySerializationPolicy(HistorySerializationPolicy):
    """Serialize selected history as provider-agnostic role/content pairs."""

    name = "serialization.default_history"

    def serialize(self, truncation_result: ContextTruncationResult) -> list[dict[str, str]]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in truncation_result.messages
        ]
