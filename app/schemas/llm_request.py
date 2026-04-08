"""LLM 访问的规范化请求模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ALLOWED_MESSAGE_ROLES = {"system", "user", "assistant", "tool"}


@dataclass
class LLMMessage:
    """单条规范化 LLM 消息。"""

    role: str
    content: str

    def __post_init__(self) -> None:
        self.role = self.role.strip().lower()
        self.content = self.content.strip()

        if self.role not in ALLOWED_MESSAGE_ROLES:
            raise ValueError(
                f"不支持的消息角色 '{self.role}'。 "
                f"支持的角色：{', '.join(sorted(ALLOWED_MESSAGE_ROLES))}。"
            )
        if not self.content:
            raise ValueError("消息内容不能为空。")


@dataclass
class LLMRequest:
    """供 service 与 providers 共享的规范化请求模型。"""

    provider: str | None = None
    model: str | None = None
    messages: list[LLMMessage] = field(default_factory=list)
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    session_id: str | None = None
    conversation_id: str | None = None
    request_id: str | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    tool_choice: str | dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.provider is not None:
            self.provider = self.provider.strip().lower()

        if self.model is not None:
            self.model = self.model.strip() or None

        if self.system_prompt is not None:
            self.system_prompt = self.system_prompt.strip() or None

        if self.session_id is not None:
            self.session_id = self.session_id.strip() or None

        if self.conversation_id is not None:
            self.conversation_id = self.conversation_id.strip() or None

        if self.request_id is not None:
            self.request_id = self.request_id.strip() or None

        if self.temperature is not None and not 0 <= self.temperature <= 2:
            raise ValueError("temperature 必须在 0 到 2 之间。")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens 必须大于 0。")
