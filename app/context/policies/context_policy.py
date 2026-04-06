"""Composable context policy pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from app.context.models import ContextSelectionResult, ContextTruncationResult, ContextWindow
from app.context.policies.base import (
    HistorySerializationPolicy,
    TruncationPolicy,
    WindowSelectionPolicy,
)


@dataclass(frozen=True)
class ContextPolicyExecutionResult:
    selection: ContextSelectionResult
    truncation: ContextTruncationResult
    serialization_policy: str
    serialized_messages: list[dict[str, str]]


@dataclass(frozen=True)
class ContextPolicyPipeline:
    selection_policy: WindowSelectionPolicy
    truncation_policy: TruncationPolicy
    serialization_policy: HistorySerializationPolicy

    def run(self, window: ContextWindow) -> ContextPolicyExecutionResult:
        selection = self.selection_policy.select(window)
        truncation = self.truncation_policy.truncate(selection)
        serialized_messages = self.serialization_policy.serialize(truncation)
        return ContextPolicyExecutionResult(
            selection=selection,
            truncation=truncation,
            serialization_policy=self.serialization_policy.name,
            serialized_messages=serialized_messages,
        )
