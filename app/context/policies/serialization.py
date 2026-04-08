"""上下文历史消息的序列化策略。"""

from __future__ import annotations

from app.context.models import ContextSummaryResult
from app.context.policies.base import HistorySerializationPolicy


class DefaultHistorySerializationPolicy(HistorySerializationPolicy):
    """将已选历史序列化为与 Provider 无关的 role/content 对。"""

    name = "serialization.default_history"

    def serialize(self, summary_result: ContextSummaryResult) -> list[dict[str, str]]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in summary_result.messages
        ]
