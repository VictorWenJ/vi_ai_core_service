from __future__ import annotations

import unittest

from app.context.models import ContextMessage, ContextSelectionResult, ContextWindow
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.truncation import CharacterBudgetTruncationPolicy
from app.context.policies.window_selection import LastNMessagesSelectionPolicy


class ContextPoliciesTests(unittest.TestCase):
    def test_last_n_messages_selection_uses_recent_window(self) -> None:
        window = ContextWindow(
            session_id="session-1",
            messages=[
                ContextMessage(role="user", content="m1"),
                ContextMessage(role="assistant", content="m2"),
                ContextMessage(role="user", content="m3"),
                ContextMessage(role="assistant", content="m4"),
                ContextMessage(role="user", content="m5"),
            ],
        )
        policy = LastNMessagesSelectionPolicy(max_messages=3)

        result = policy.select(window)

        self.assertEqual(result.source_message_count, 5)
        self.assertEqual(result.selected_message_count, 3)
        self.assertEqual(result.dropped_message_count, 2)
        self.assertEqual(
            [message.content for message in result.selected_messages],
            ["m3", "m4", "m5"],
        )

    def test_character_budget_truncation_keeps_recent_messages_within_budget(self) -> None:
        selection_result = ContextSelectionResult(
            session_id="session-1",
            source_message_count=4,
            selected_messages=[
                ContextMessage(role="user", content="12345"),
                ContextMessage(role="assistant", content="67890"),
                ContextMessage(role="user", content="abcde"),
                ContextMessage(role="assistant", content="fghij"),
            ],
            selection_policy="window_selection.last_n_messages",
        )
        policy = CharacterBudgetTruncationPolicy(max_characters=10)

        result = policy.truncate(selection_result)

        self.assertEqual(result.input_message_count, 4)
        self.assertEqual(result.final_message_count, 2)
        self.assertEqual(result.truncated_message_count, 2)
        self.assertEqual(
            [message.content for message in result.messages],
            ["abcde", "fghij"],
        )

    def test_default_history_serialization_preserves_order(self) -> None:
        selection_result = ContextSelectionResult(
            session_id="session-1",
            source_message_count=2,
            selected_messages=[
                ContextMessage(role="user", content="hello"),
                ContextMessage(role="assistant", content="hi"),
            ],
            selection_policy="window_selection.last_n_messages",
        )
        truncation_result = CharacterBudgetTruncationPolicy(max_characters=20).truncate(
            selection_result
        )
        policy = DefaultHistorySerializationPolicy()

        serialized = policy.serialize(truncation_result)

        self.assertEqual(
            serialized,
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ],
        )
