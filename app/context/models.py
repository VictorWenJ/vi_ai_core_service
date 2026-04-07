"""Canonical context models for short-term history governance."""

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
    """Output of history window selection before truncation."""

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
    """Output of truncation policy before serialization."""

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
    """Output of summary/compaction policy before serialization."""

    session_id: str
    source_message_count: int
    source_token_count: int
    input_message_count: int
    input_token_count: int
    token_budget: int
    messages: list[ContextMessage] = field(default_factory=list)
    summary_policy: str = "summary.noop"
    summary_applied: bool = False
    summary_text: str | None = None
    final_token_count: int = 0

    @property
    def final_message_count(self) -> int:
        return len(self.messages)
