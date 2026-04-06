"""Truncation policies for selected history."""

from __future__ import annotations

from app.context.models import ContextSelectionResult, ContextTruncationResult
from app.context.policies.base import TruncationPolicy


class NoOpTruncationPolicy(TruncationPolicy):
    """Keep selected history unchanged."""

    name = "truncation.noop"

    def truncate(self, selection_result: ContextSelectionResult) -> ContextTruncationResult:
        return ContextTruncationResult(
            session_id=selection_result.session_id,
            source_message_count=selection_result.source_message_count,
            input_message_count=selection_result.selected_message_count,
            messages=list(selection_result.selected_messages),
            truncation_policy=self.name,
        )


class CharacterBudgetTruncationPolicy(TruncationPolicy):
    """Lightweight truncation placeholder based on character budget."""

    name = "truncation.character_budget"

    def __init__(self, max_characters: int) -> None:
        if max_characters <= 0:
            raise ValueError("max_characters must be greater than 0.")
        self._max_characters = max_characters

    def truncate(self, selection_result: ContextSelectionResult) -> ContextTruncationResult:
        budget_used = 0
        kept_reversed = []
        for message in reversed(selection_result.selected_messages):
            message_length = len(message.content)
            if budget_used + message_length > self._max_characters:
                continue
            kept_reversed.append(message)
            budget_used += message_length

        kept_messages = list(reversed(kept_reversed))
        return ContextTruncationResult(
            session_id=selection_result.session_id,
            source_message_count=selection_result.source_message_count,
            input_message_count=selection_result.selected_message_count,
            messages=kept_messages,
            truncation_policy=self.name,
        )
