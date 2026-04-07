"""Serialization policies for context history messages."""

from __future__ import annotations

from app.context.models import ContextSummaryResult
from app.context.policies.base import HistorySerializationPolicy


class DefaultHistorySerializationPolicy(HistorySerializationPolicy):
    """Serialize selected history as provider-agnostic role/content pairs."""

    name = "serialization.default_history"

    def serialize(self, summary_result: ContextSummaryResult) -> list[dict[str, str]]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in summary_result.messages
        ]
