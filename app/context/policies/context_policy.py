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
    selection: ContextSelectionResult
    truncation: ContextTruncationResult
    summary: ContextSummaryResult
    serialization_policy: str
    token_counter: str | None
    serialized_messages: list[dict[str, str]]


@dataclass(frozen=True)
class ContextPolicyPipeline:
    selection_policy: WindowSelectionPolicy
    truncation_policy: TruncationPolicy
    summary_policy: SummaryPolicy
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
