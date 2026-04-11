"""可组合的上下文策略管线。"""

from __future__ import annotations

from dataclasses import dataclass

from app.context.models import (
    ContextSelectionResult,
    ContextSummaryResult,
    ContextTruncationResult,
    ContextWindow,
)
from app.context.policies.base import (
    HistorySerializationPolicy,
    SummaryPolicy,
    TruncationPolicy,
    WindowSelectionPolicy,
)
from app.observability.log_until import log_report


@dataclass(frozen=True)
class ContextPolicyExecutionResult:
    # 窗口选择阶段结果。
    selection: ContextSelectionResult
    # 截断阶段结果。
    truncation: ContextTruncationResult
    # 摘要/压缩阶段结果。
    summary: ContextSummaryResult
    # 最终序列化策略名称。
    serialization_policy: str
    # 本次策略管道使用的 token_counter 名称；不可解析时为空。
    token_counter: str | None
    # 提供给 LLM 的规范化消息序列。
    serialized_messages: list[dict[str, str]]


@dataclass(frozen=True)
class ContextPolicyPipeline:
    # 历史窗口选择策略实现。
    selection_policy: WindowSelectionPolicy
    # token 截断策略实现。
    truncation_policy: TruncationPolicy
    # 摘要/压缩策略实现。
    summary_policy: SummaryPolicy
    # 历史消息序列化策略实现。
    serialization_policy: HistorySerializationPolicy

    def run(self, window: ContextWindow) -> ContextPolicyExecutionResult:
        selection = self.selection_policy.select(window)
        log_report("ContextPolicyPipeline.run.selection", selection)

        truncation = self.truncation_policy.truncate(selection)
        log_report("ContextPolicyPipeline.run.truncation", truncation)

        summary = self.summary_policy.summarize(
            window=window,
            selection=selection,
            truncation=truncation,
        )
        log_report("ContextPolicyPipeline.run.summary", summary)

        serialized_messages = self.serialization_policy.serialize(summary)
        log_report("ContextPolicyPipeline.run.serialized_messages", serialized_messages)

        return ContextPolicyExecutionResult(
            selection=selection,
            truncation=truncation,
            summary=summary,
            serialization_policy=self.serialization_policy.name,
            token_counter=_resolve_token_counter_name(
                self.selection_policy,
                self.truncation_policy,
                self.summary_policy,
            ),
            serialized_messages=serialized_messages,
        )


def _resolve_token_counter_name(*policies: object) -> str | None:
    for policy in policies:
        token_counter = getattr(policy, "_token_counter", None)
        token_counter_name = getattr(token_counter, "name", None)
        if isinstance(token_counter_name, str) and token_counter_name:
            return token_counter_name
    return None
