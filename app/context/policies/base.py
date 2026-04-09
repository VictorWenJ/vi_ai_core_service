"""上下文历史治理的策略接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.context.models import (
    ContextSelectionResult,
    ContextSummaryResult,
    ContextTruncationResult,
    ContextWindow,
)


class WindowSelectionPolicy(ABC):
    """从原始会话上下文中选择可管理的历史窗口。"""

    name: str = "window_selection.base"

    @abstractmethod
    def select(self, window: ContextWindow) -> ContextSelectionResult:
        raise NotImplementedError


class TruncationPolicy(ABC):
    """对已选历史应用预算化截断。"""

    name: str = "truncation.base"

    @abstractmethod
    def truncate(self, selection_result: ContextSelectionResult) -> ContextTruncationResult:
        raise NotImplementedError


class SummaryPolicy(ABC):
    """可选地将丢弃历史压缩为确定性摘要。"""

    name: str = "summary.base"

    @abstractmethod
    def summarize(
        self,
        *,
        window: ContextWindow,
        selection: ContextSelectionResult,
        truncation: ContextTruncationResult,
    ) -> ContextSummaryResult:
        raise NotImplementedError


class HistorySerializationPolicy(ABC):
    """将与 Provider 无关的历史消息序列化供请求装配使用。"""

    name: str = "serialization.base"

    @abstractmethod
    def serialize(self, summary_result: ContextSummaryResult) -> list[dict[str, str]]:
        raise NotImplementedError
