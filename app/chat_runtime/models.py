"""聊天运行时数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event
from time import perf_counter
from typing import Any

from app.chat_runtime.trace import ExecutionTrace
from app.providers.chat.base import BaseLLMProvider
from app.rag.models import Citation, RetrievalResult, RetrievalTrace
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse, LLMUsage


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass
class RuntimeStreamOptions:
    # 心跳事件发送间隔，单位为秒（seconds）。
    stream_heartbeat_interval_seconds: float
    # 单次流式请求超时时间，单位为秒（seconds）。
    stream_request_timeout_seconds: float
    # 是否在 completed 事件中输出 usage。
    stream_emit_usage: bool
    # 是否在 completed/error/cancelled 事件中输出 trace。
    stream_emit_trace: bool


@dataclass
class RuntimeTurnRequest:
    # 用户本轮输入原文。
    user_prompt: str
    # 会话 ID；为空表示无状态调用。
    session_id: str | None = None
    # 会话作用域 ID；为空时由运行时归一化到默认 scope。
    conversation_id: str | None = None
    # 请求唯一 ID；为空时由运行时生成。
    request_id: str | None = None
    # Provider 覆盖值；为空时使用系统默认 provider。
    provider_override: str | None = None
    # 模型覆盖值；为空时使用 provider 默认模型。
    model_override: str | None = None
    # 采样温度覆盖；为空时走 provider 默认行为。
    temperature: float | None = None
    # 最大输出 token 覆盖，单位为 token。
    max_tokens: int | None = None
    # 系统提示词覆盖；为空时由装配器回落默认 prompt。
    system_prompt: str | None = None
    # 是否启用流式交付。
    stream: bool = False
    # 业务透传元数据。
    metadata: dict[str, Any] = field(default_factory=dict)
    # 流式选项；同步请求可为空。
    stream_options: RuntimeStreamOptions | None = None
    # 预分配的 user 消息 ID；为空时运行时生成。
    user_message_id: str | None = None
    # 预分配的 assistant 消息 ID；为空时运行时生成。
    assistant_message_id: str | None = None
    # 取消信号；置位后流式执行进入 cancelled 收口。
    cancel_event: Event | None = None

    def __post_init__(self) -> None:
        self.user_prompt = self.user_prompt.strip()
        self.session_id = _normalize_optional_text(self.session_id)
        self.conversation_id = _normalize_optional_text(self.conversation_id)
        self.request_id = _normalize_optional_text(self.request_id)
        self.provider_override = _normalize_optional_text(self.provider_override)
        self.model_override = _normalize_optional_text(self.model_override)
        self.system_prompt = _normalize_optional_text(self.system_prompt)
        self.user_message_id = _normalize_optional_text(self.user_message_id)
        self.assistant_message_id = _normalize_optional_text(self.assistant_message_id)
        self.metadata = dict(self.metadata or {})


@dataclass
class RuntimeTurnContext:
    # 本轮运行时请求对象。
    request: RuntimeTurnRequest
    # 当前执行 workflow 名称。
    workflow_name: str
    # 当前运行 trace。
    trace: ExecutionTrace
    # 当前流程使用的 skills 引用列表。
    skills: list[str]
    # scope 归一化后的 session_id。
    normalized_session_id: str | None = None
    # scope 归一化后的 conversation_id。
    normalized_conversation_id: str | None = None
    # 检索结果对象。
    retrieval_result: RetrievalResult | None = None
    # 组装后的原始 LLM 请求。
    llm_request: LLMRequest | None = None
    # 规范化后的最终 LLM 请求。
    normalized_llm_request: LLMRequest | None = None
    # 选中的 provider 实例。
    selected_provider: BaseLLMProvider | None = None
    # 最终选中的 provider 名称。
    selected_provider_name: str | None = None
    # 最终选中的模型名称。
    selected_model: str | None = None
    # user 消息 ID。
    user_message_id: str | None = None
    # assistant 消息 ID。
    assistant_message_id: str | None = None
    # 非流式响应对象。
    llm_response: LLMResponse | None = None
    # 最终回答文本。
    response_text: str = ""
    # 流式累积文本。
    partial_output: str = ""
    # 最终引用列表。
    citations: list[Citation] = field(default_factory=list)
    # token 使用统计。
    usage: LLMUsage | None = None
    # 结束原因标识。
    finish_reason: str | None = None
    # 运行状态（running/completed/failed/cancelled）。
    status: str = "running"
    # 失败时错误码。
    error_code: str | None = None
    # 失败时错误信息。
    error_message: str | None = None
    # 流式事件计数，单位为条（count）。
    stream_event_count: int = 0
    # 流式 delta 序列号，单位为序号（count）。
    stream_sequence: int = 0
    # 是否已创建流式上下文占位消息。
    stream_placeholder_created: bool = False
    # 流式开始高精度时间戳，单位为秒（seconds）。
    stream_started_perf_seconds: float = field(default_factory=perf_counter)

    @property
    def retrieval_trace(self) -> RetrievalTrace | None:
        if self.retrieval_result is None:
            return None
        return self.retrieval_result.trace


@dataclass
class RuntimeTurnResult:
    # 最终回答文本。
    response_text: str
    # 最终引用列表。
    citations: list[Citation]
    # 实际 provider 名称。
    provider: str
    # 实际模型名称。
    model: str | None
    # token 使用统计。
    usage: LLMUsage | None
    # 结束原因标识。
    finish_reason: str | None
    # 检索追踪信息；禁用检索时可为空。
    retrieval_trace: RetrievalTrace | None
    # 执行 trace 对象。
    trace: ExecutionTrace
    # 响应元数据透传。
    metadata: dict[str, Any] = field(default_factory=dict)
    # 原始响应载荷快照。
    raw_response: dict[str, Any] | None = None
