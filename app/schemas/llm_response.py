"""LLM 访问的规范化响应模型。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class LLMUsage:
    """规范化 token 用量。"""

    # 输入提示词 token 数，单位为 token。
    prompt_tokens: int | None = None
    # 输出补全文本 token 数，单位为 token。
    completion_tokens: int | None = None
    # 总 token 数，单位为 token。
    total_tokens: int | None = None


@dataclass
class LLMResponse:
    """返回给业务代码的规范化 Provider 响应。"""

    # Provider 归一化后的文本输出内容。
    content: str
    # 产生该响应的 provider 标识。
    provider: str
    # 产生该响应的模型标识；不可用时为空。
    model: str | None = None
    # token 使用量统计；provider 未返回时为空。
    usage: LLMUsage | None = None
    # 结束原因标识，如 stop/length/cancelled。
    finish_reason: str | None = None
    # 标准化响应的附加元数据。
    metadata: dict[str, Any] = field(default_factory=dict)
    # provider 原始响应载荷快照；不可用时为空。
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LLMStreamChunk:
    """Provider 流式输出的规范化增量片段。"""

    # 当前流式片段新增文本。
    delta: str = ""
    # 当前片段序号，从 0 递增，单位为序号（count）。
    sequence: int = 0
    # 流式完成时的结束原因；中间片段通常为空。
    finish_reason: str | None = None
    # 流式片段携带的 token 统计；通常只在结束片段出现。
    usage: LLMUsage | None = None
    # 是否为流式结束片段。
    done: bool = False
    # 流式片段附加元数据。
    metadata: dict[str, Any] = field(default_factory=dict)
