"""聊天路由请求/响应模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    user_prompt: str = Field(min_length=1, description="单轮用户输入。")
    provider: str | None = Field(default=None, description="可选的 Provider 覆盖。")
    model: str | None = Field(default=None, description="可选的模型覆盖。")
    temperature: float | None = Field(
        default=None,
        ge=0,
        le=2,
        description="可选的采样温度覆盖。",
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,
        description="可选的最大 token 覆盖。",
    )
    system_prompt: str | None = Field(default=None, description="可选的系统提示词。")
    stream: bool = Field(default=False, description="流式响应开关。")

    # 用户会话容器
    session_id: str | None = Field(default=None, description="可选的有状态会话 ID。")

    # 当前对话线程
    conversation_id: str | None = Field(
        default=None,
        description="可选的会话轮次 ID，用于跨请求连续性。",
    )
    request_id: str | None = Field(default=None, description="可选的外部请求 ID。")
    metadata: dict[str, Any] | None = Field(default=None, description="可选的元数据。")


class ChatStreamOptions(BaseModel):
    stream_heartbeat_interval_seconds: float | None = Field(
        default=None,
        gt=0,
        description="可选心跳间隔（秒），为空时使用配置默认值。",
    )
    stream_request_timeout_seconds: float | None = Field(
        default=None,
        gt=0,
        description="可选请求超时（秒），为空时使用配置默认值。",
    )
    stream_emit_usage: bool | None = Field(
        default=None,
        description="是否在 completed 事件输出 usage。",
    )
    stream_emit_trace: bool | None = Field(
        default=None,
        description="是否在 completed/error/cancelled 事件输出 trace。",
    )


class ChatStreamRequest(ChatRequest):
    stream: bool = Field(default=True, description="流式接口固定为 true。")
    stream_options: ChatStreamOptions | None = Field(
        default=None,
        description="流式行为覆盖选项。",
    )


class ChatCancelRequest(BaseModel):
    request_id: str | None = Field(default=None, description="待取消的 request_id。")
    assistant_message_id: str | None = Field(default=None, description="待取消的 assistant_message_id。")
    session_id: str | None = Field(default=None, description="可选 session 过滤。")
    conversation_id: str | None = Field(default=None, description="可选 conversation 过滤。")

    @model_validator(mode="after")
    def validate_identity(self) -> "ChatCancelRequest":
        if not (self.request_id or self.assistant_message_id):
            raise ValueError("request_id 与 assistant_message_id 至少提供一个。")
        return self


class ChatCancelResponse(BaseModel):
    found: bool
    cancelled: bool
    already_cancelled: bool = False
    request_id: str | None = None
    assistant_message_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None


class ChatUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatCitation(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    title: str | None = None
    snippet: str
    origin_uri: str | None = None
    source_type: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str | None = None
    usage: ChatUsage | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] | None = None
    citations: list[ChatCitation] = Field(default_factory=list)


class ChatResetRequest(BaseModel):
    session_id: str = Field(min_length=1, description="待重置的会话 ID。")
    conversation_id: str | None = Field(
        default=None,
        description="可选会话轮次 ID；缺省时重置整个会话窗口。",
    )


class ChatResetResponse(BaseModel):
    reset: bool = True
    session_id: str
    conversation_id: str | None = None
    remaining_message_count: int
    scope: str
