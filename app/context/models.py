"""用于短期历史治理的规范化上下文模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ContextMessage:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ContextWindow:
    session_id: str
    messages: list[ContextMessage] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        return len(self.messages)


@dataclass
class ContextSelectionResult:
    """截断前的历史窗口选择结果。"""

    session_id: str
    source_message_count: int
    source_token_count: int
    token_budget: int
    selected_messages: list[ContextMessage] = field(default_factory=list)
    dropped_messages: list[ContextMessage] = field(default_factory=list)
    selected_token_count: int = 0
    selection_policy: str = "unknown"

    @property
    def selected_message_count(self) -> int:
        return len(self.selected_messages)

    @property
    def dropped_message_count(self) -> int:
        return max(self.source_message_count - self.selected_message_count, 0)


@dataclass
class ContextTruncationResult:
    """序列化前的截断策略结果。"""

    session_id: str
    source_message_count: int
    source_token_count: int
    input_message_count: int
    input_token_count: int
    token_budget: int
    messages: list[ContextMessage] = field(default_factory=list)
    dropped_messages: list[ContextMessage] = field(default_factory=list)
    final_token_count: int = 0
    truncation_policy: str = "unknown"

    @property
    def final_message_count(self) -> int:
        return len(self.messages)

    @property
    def truncated_message_count(self) -> int:
        return max(self.input_message_count - self.final_message_count, 0)

    @property
    def truncation_applied(self) -> bool:
        return self.truncated_message_count > 0 or self.input_token_count > self.token_budget


@dataclass
class ContextSummaryResult:
    """序列化前的摘要/压缩策略结果。"""

    session_id: str
    source_message_count: int
    source_token_count: int
    input_message_count: int
    input_token_count: int
    token_budget: int
    messages: list[ContextMessage] = field(default_factory=list)
    dropped_messages: list[ContextMessage] = field(default_factory=list)
    summary_policy: str = "summary.noop"
    summary_applied: bool = False
    summary_text: str | None = None
    final_token_count: int = 0

    @property
    def final_message_count(self) -> int:
        return len(self.messages)

    @property
    def dropped_message_count(self) -> int:
        return len(self.dropped_messages)
