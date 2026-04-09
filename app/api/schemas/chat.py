"""聊天路由请求/响应模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
    stream: bool = Field(default=False, description="流式响应开关（预留）。")

    # 用户会话容器
    session_id: str | None = Field(default=None, description="可选的有状态会话 ID。")

    # 当前对话线程
    conversation_id: str | None = Field(
        default=None,
        description="可选的会话轮次 ID，用于跨请求连续性。",
    )
    request_id: str | None = Field(default=None, description="可选的外部请求 ID。")
    metadata: dict[str, Any] | None = Field(default=None, description="可选的元数据。")


class ChatUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str | None = None
    usage: ChatUsage | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] | None = None


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
