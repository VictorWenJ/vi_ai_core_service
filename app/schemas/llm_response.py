"""LLM 访问的规范化响应模型。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class LLMUsage:
    """规范化 token 用量。"""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class LLMResponse:
    """返回给业务代码的规范化 Provider 响应。"""

    content: str
    provider: str
    model: str | None = None
    usage: LLMUsage | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LLMStreamChunk:
    """Provider 流式输出的规范化增量片段。"""

    delta: str = ""
    sequence: int = 0
    finish_reason: str | None = None
    usage: LLMUsage | None = None
    done: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
