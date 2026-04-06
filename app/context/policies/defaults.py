"""Default constants and builders for context policy pipeline."""

from __future__ import annotations

from app.context.policies.context_policy import ContextPolicyPipeline
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.truncation import CharacterBudgetTruncationPolicy
from app.context.policies.window_selection import LastNMessagesSelectionPolicy

DEFAULT_HISTORY_WINDOW_SIZE = 8
DEFAULT_HISTORY_CHAR_BUDGET = 4000


def build_default_context_policy_pipeline() -> ContextPolicyPipeline:
    return ContextPolicyPipeline(
        selection_policy=LastNMessagesSelectionPolicy(DEFAULT_HISTORY_WINDOW_SIZE),
        truncation_policy=CharacterBudgetTruncationPolicy(DEFAULT_HISTORY_CHAR_BUDGET),
        serialization_policy=DefaultHistorySerializationPolicy(),
    )
