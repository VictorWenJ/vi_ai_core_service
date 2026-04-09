"""用于短期历史治理的规范化上下文模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

DEFAULT_CONVERSATION_SCOPE = "__default__"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_conversation_scope(conversation_id: str | None) -> str:
    if conversation_id is None:
        return DEFAULT_CONVERSATION_SCOPE
    normalized_value = conversation_id.strip()
    return normalized_value or DEFAULT_CONVERSATION_SCOPE


@dataclass
class ContextMessage:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_utc_iso)


@dataclass
class RollingSummaryState:
    text: str = ""
    updated_at: str | None = None
    source_message_count: int = 0

    @property
    def has_content(self) -> bool:
        return bool(self.text.strip())


@dataclass
class WorkingMemoryState:
    # 当前会话的主要目标（高置信度、可直接复用）。
    active_goal: str | None = None
    # 对当前任务形成约束条件列表（如“只返回中文”“不要使用流式”）。
    constraints: list[str] = field(default_factory=list)
    # 已确认的关键决策列表（用于保持多轮一致性）。
    decisions: list[str] = field(default_factory=list)
    # 仍待澄清或待用户补充的问题列表。
    open_questions: list[str] = field(default_factory=list)
    # 当前最建议执行的下一步动作描述。
    next_step: str | None = None
    # 工作记忆最近一次更新时间（UTC ISO 字符串）。
    updated_at: str | None = None

    def non_empty_fields(self) -> list[str]:
        fields: list[str] = []
        if self.active_goal:
            fields.append("active_goal")
        if self.constraints:
            fields.append("constraints")
        if self.decisions:
            fields.append("decisions")
        if self.open_questions:
            fields.append("open_questions")
        if self.next_step:
            fields.append("next_step")
        return fields


@dataclass
class ContextWindow:
    session_id: str
    conversation_id: str = DEFAULT_CONVERSATION_SCOPE
    # Phase 4 后该字段只表示 recent raw messages，不表示全量历史。
    messages: list[ContextMessage] = field(default_factory=list)
    rolling_summary: RollingSummaryState = field(default_factory=RollingSummaryState)
    working_memory: WorkingMemoryState = field(default_factory=WorkingMemoryState)
    runtime_meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.conversation_id = normalize_conversation_scope(self.conversation_id)

    @property
    def message_count(self) -> int:
        return len(self.messages)


@dataclass
class ContextSelectionResult:
    """截断前的历史窗口选择结果。"""

    session_id: str
    conversation_id: str
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
    conversation_id: str
    source_message_count: int
    source_token_count: int
    input_message_count: int
    input_token_count: int
    truncation_token_budget: int
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
        return (
            self.truncated_message_count > 0
            or self.input_token_count > self.truncation_token_budget
        )


@dataclass
class ContextSummaryResult:
    """序列化前的摘要/压缩策略结果。"""

    session_id: str
    conversation_id: str
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
