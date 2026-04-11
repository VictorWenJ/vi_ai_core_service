"""LLM 访问的规范化请求模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ALLOWED_MESSAGE_ROLES = {"system", "user", "assistant", "tool"}


@dataclass
class LLMMessage:
    """单条规范化 LLM 消息。"""

    # 消息角色类型，限定为 system/user/assistant/tool。
    role: str
    # 消息正文文本，不能为空字符串。
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

    # 目标 provider 名称；为空时由服务层回退到默认 provider。
    provider: str | None = None
    # 目标模型标识；为空时由 provider 默认模型补齐。
    model: str | None = None
    # 发送给 LLM 的消息序列。
    messages: list[LLMMessage] = field(default_factory=list)
    # system prompt 文本；为空时由请求装配器决定是否注入。
    system_prompt: str | None = None
    # 采样温度，取值区间为 0~2。
    temperature: float | None = None
    # 期望生成的最大 token 数，单位为 token。
    max_tokens: int | None = None
    # 是否使用流式输出模式。
    stream: bool = False
    # 会话 ID，用于上下文作用域与追踪。
    session_id: str | None = None
    # 会话作用域 ID，用于 conversation 维度隔离。
    conversation_id: str | None = None
    # 请求唯一 ID，用于链路追踪与幂等定位。
    request_id: str | None = None
    # 工具声明列表，结构与 provider 能力契约对齐。
    tools: list[dict[str, Any]] = field(default_factory=list)
    # 工具选择策略或显式工具选择对象。
    tool_choice: str | dict[str, Any] | None = None
    # 结构化输出约束配置。
    response_format: dict[str, Any] | None = None
    # 附件元信息列表（例如多模态输入引用）。
    attachments: list[dict[str, Any]] = field(default_factory=list)
    # 业务侧透传元数据，不参与底层协议语义。
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
