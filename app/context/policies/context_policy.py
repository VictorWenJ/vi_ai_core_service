"""Composable context policy pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from app.observability.log_until import log_report

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


@dataclass(frozen=True)
class ContextPolicyExecutionResult:
    selection: ContextSelectionResult
    truncation: ContextTruncationResult
    summary: ContextSummaryResult
    serialization_policy: str
    serialized_messages: list[dict[str, str]]


@dataclass(frozen=True)
class ContextPolicyPipeline:
    # 窗口选择策略
    selection_policy: WindowSelectionPolicy
    # 截断策略
    truncation_policy: TruncationPolicy
    # 总结策略
    summary_policy: SummaryPolicy
    # 历史上下文序列化策略
    serialization_policy: HistorySerializationPolicy

    def run(self, window: ContextWindow) -> ContextPolicyExecutionResult:
        selection = self.selection_policy.select(window)
        log_report("ContextPolicyPipeline.run.selection", selection)

        truncation = self.truncation_policy.truncate(selection)
        log_report("ContextPolicyPipeline.run.truncation", truncation)

        summary = self.summary_policy.summarize(
            window=window,
            selection_result=selection,
            truncation_result=truncation,
        )
        log_report("ContextPolicyPipeline.run.summary", summary)

        serialized_messages = self.serialization_policy.serialize(summary)
        log_report("ContextPolicyPipeline.run.serialized_messages", serialized_messages)

        return ContextPolicyExecutionResult(
            selection=selection,
            truncation=truncation,
            summary=summary,
            serialization_policy=self.serialization_policy.name,
            serialized_messages=serialized_messages,
        )
