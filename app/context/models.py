"""用于短期上下文治理的规范化上下文模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# conversation_id 缺失时使用的默认作用域标识。
DEFAULT_CONVERSATION_SCOPE = "__default__"
# 非 assistant 消息默认状态；同时也是 assistant 的默认完成态。
DEFAULT_CONTEXT_MESSAGE_STATUS = "completed"
ASSISTANT_MESSAGE_STATUSES = {"created", "streaming", "completed", "failed", "cancelled"}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_conversation_scope(conversation_id: str | None) -> str:
    if conversation_id is None:
        return DEFAULT_CONVERSATION_SCOPE
    normalized_value = conversation_id.strip()
    return normalized_value or DEFAULT_CONVERSATION_SCOPE


def normalize_message_status(role: str, status: str | None) -> str:
    normalized_role = role.strip().lower()
    normalized_status = (status or DEFAULT_CONTEXT_MESSAGE_STATUS).strip().lower()
    if normalized_role != "assistant":
        return DEFAULT_CONTEXT_MESSAGE_STATUS
    if normalized_status not in ASSISTANT_MESSAGE_STATUSES:
        raise ValueError(
            "assistant 消息状态不合法，支持的状态为："
            f"{', '.join(sorted(ASSISTANT_MESSAGE_STATUSES))}。"
        )
    return normalized_status


@dataclass
class ContextMessage:
    # 消息角色类型，如 system、user、assistant。
    role: str
    # 消息正文文本内容。
    content: str
    # 业务扩展元数据字典，默认空字典。
    metadata: dict[str, Any] = field(default_factory=dict)
    # 消息创建时间，UTC ISO 格式字符串。
    created_at: str = field(default_factory=now_utc_iso)
    # 消息唯一标识；为空时表示未绑定外部 ID。
    message_id: str | None = None
    # 消息状态，assistant 支持 created/streaming/completed/failed/cancelled。
    status: str = DEFAULT_CONTEXT_MESSAGE_STATUS
    # 消息最近更新时间，UTC ISO 格式字符串。
    updated_at: str = field(default_factory=now_utc_iso)
    # 结束原因，通常由 provider 返回；非结束态可为空。
    finish_reason: str | None = None
    # 错误码，失败场景用于诊断；正常场景为空。
    error_code: str | None = None

    def __post_init__(self) -> None:
        self.role = self.role.strip().lower()
        self.content = str(self.content)
        self.status = normalize_message_status(self.role, self.status)
        self.metadata = dict(self.metadata)
        if self.message_id is not None:
            self.message_id = self.message_id.strip() or None
        if self.finish_reason is not None:
            self.finish_reason = self.finish_reason.strip() or None
        if self.error_code is not None:
            self.error_code = self.error_code.strip() or None
        if not self.updated_at:
            self.updated_at = self.created_at or now_utc_iso()

    @property
    def is_completed_assistant(self) -> bool:
        return self.role == "assistant" and self.status == "completed"


@dataclass
class RollingSummaryState:
    # 累积后的滚动摘要正文。
    text: str = ""
    # 摘要最近更新时间，UTC ISO 格式字符串；无摘要时可为空。
    updated_at: str | None = None
    # 参与摘要聚合的原始消息条数，单位为条（count）。
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
    # 会话标识（跨轮固定）。
    session_id: str
    # 会话作用域标识；默认落到 __default__。
    conversation_id: str = DEFAULT_CONVERSATION_SCOPE
    # Phase 4 后该字段只表示 recent raw messages，不表示全量历史。
    messages: list[ContextMessage] = field(default_factory=list)
    # rolling summary 层状态。
    rolling_summary: RollingSummaryState = field(default_factory=RollingSummaryState)
    # working memory 层状态。
    working_memory: WorkingMemoryState = field(default_factory=WorkingMemoryState)
    # 运行时观测元数据，不参与核心业务判定。
    runtime_meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.conversation_id = normalize_conversation_scope(self.conversation_id)

    @property
    def message_count(self) -> int:
        return len(self.messages)


@dataclass
class ContextSelectionResult:
    """截断前的历史窗口选择结果。"""

    # 所属会话 ID。
    session_id: str
    # 所属会话作用域 ID。
    conversation_id: str
    # 选择前源消息总数，单位为条（count）。
    source_message_count: int
    # 选择前源消息 token 总数，单位为 token。
    source_token_count: int
    # 本次窗口选择可用 token 预算，单位为 token。
    token_budget: int
    # 被选中的消息列表。
    selected_messages: list[ContextMessage] = field(default_factory=list)
    # 被丢弃的消息列表。
    dropped_messages: list[ContextMessage] = field(default_factory=list)
    # 被选中消息 token 数，单位为 token。
    selected_token_count: int = 0
    # 实际执行的窗口选择策略名称。
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

    # 所属会话 ID。
    session_id: str
    # 所属会话作用域 ID。
    conversation_id: str
    # 截断前源消息总数，单位为条（count）。
    source_message_count: int
    # 截断前源消息 token 总数，单位为 token。
    source_token_count: int
    # 进入截断阶段的消息条数，单位为条（count）。
    input_message_count: int
    # 进入截断阶段的消息 token 数，单位为 token。
    input_token_count: int
    # 截断阶段预算上限，单位为 token。
    truncation_token_budget: int
    # 截断后保留消息列表。
    messages: list[ContextMessage] = field(default_factory=list)
    # 截断阶段移除的消息列表。
    dropped_messages: list[ContextMessage] = field(default_factory=list)
    # 截断后最终 token 数，单位为 token。
    final_token_count: int = 0
    # 实际执行的截断策略名称。
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

    # 所属会话 ID。
    session_id: str
    # 所属会话作用域 ID。
    conversation_id: str
    # 摘要前源消息总数，单位为条（count）。
    source_message_count: int
    # 摘要前源消息 token 总数，单位为 token。
    source_token_count: int
    # 输入摘要阶段的消息条数，单位为条（count）。
    input_message_count: int
    # 输入摘要阶段的消息 token 数，单位为 token。
    input_token_count: int
    # 摘要阶段预算上限，单位为 token。
    token_budget: int
    # 摘要阶段输出消息列表。
    messages: list[ContextMessage] = field(default_factory=list)
    # 摘要阶段丢弃消息列表。
    dropped_messages: list[ContextMessage] = field(default_factory=list)
    # 实际执行的摘要策略名称。
    summary_policy: str = "summary.noop"
    # 是否实际应用了摘要策略。
    summary_applied: bool = False
    # 摘要文本；未生成时为空。
    summary_text: str | None = None
    # 摘要阶段最终 token 数，单位为 token。
    final_token_count: int = 0

    @property
    def final_message_count(self) -> int:
        return len(self.messages)

    @property
    def dropped_message_count(self) -> int:
        return len(self.dropped_messages)
