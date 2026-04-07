from __future__ import annotations

import unittest

from app.context.models import ContextMessage, ContextWindow
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.summary import DeterministicSummaryPolicy
from app.context.policies.tokenizer import CharacterTokenCounter
from app.context.policies.truncation import TokenAwareTruncationPolicy
from app.context.policies.window_selection import TokenAwareWindowSelectionPolicy


class ContextPoliciesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.token_counter = CharacterTokenCounter()

    def test_token_aware_window_selection_uses_recent_messages_within_budget(self) -> None:
        window = ContextWindow(
            session_id="session-1",
            messages=[
                ContextMessage(role="user", content="aaaa"),      # 8 tokens
                ContextMessage(role="assistant", content="bbbb"), # 8 tokens
                ContextMessage(role="user", content="cccc"),      # 8 tokens
            ],
        )
        policy = TokenAwareWindowSelectionPolicy(
            max_tokens=16,
            token_counter=self.token_counter,
        )

        result = policy.select(window)

        self.assertEqual(result.source_message_count, 3)
        self.assertEqual(result.selected_message_count, 2)
        self.assertEqual(result.dropped_message_count, 1)
        self.assertEqual([message.content for message in result.selected_messages], ["bbbb", "cccc"])
        self.assertEqual(result.selected_token_count, 16)

    def test_token_aware_truncation_truncates_oldest_message_when_needed(self) -> None:
        selection_policy = TokenAwareWindowSelectionPolicy(
            max_tokens=30,
            token_counter=self.token_counter,
        )
        window = ContextWindow(
            session_id="session-1",
            messages=[
                ContextMessage(role="user", content="1234567890"),      # 14 tokens
                ContextMessage(role="assistant", content="abcdefghij"), # 14 tokens
            ],
        )
        selection_result = selection_policy.select(window)
        truncation_policy = TokenAwareTruncationPolicy(
            max_tokens=20,
            token_counter=self.token_counter,
        )

        truncation_result = truncation_policy.truncate(selection_result)

        self.assertTrue(truncation_result.truncation_applied)
        self.assertLessEqual(truncation_result.final_token_count, 20)
        self.assertEqual(truncation_result.final_message_count, 2)
        self.assertTrue(truncation_result.messages[0].metadata.get("truncated", False))
        self.assertEqual(truncation_result.messages[1].content, "abcdefghij")

    def test_summary_policy_inserts_summary_message_for_dropped_history(self) -> None:
        selection_policy = TokenAwareWindowSelectionPolicy(
            max_tokens=16,
            token_counter=self.token_counter,
        )
        window = ContextWindow(
            session_id="session-1",
            messages=[
                ContextMessage(role="user", content="old-1"),
                ContextMessage(role="assistant", content="old-2"),
                ContextMessage(role="user", content="latest"),
            ],
        )
        selection_result = selection_policy.select(window)
        truncation_policy = TokenAwareTruncationPolicy(
            max_tokens=16,
            token_counter=self.token_counter,
        )
        truncation_result = truncation_policy.truncate(selection_result)
        summary_policy = DeterministicSummaryPolicy(
            enabled=True,
            max_summary_chars=120,
            fallback_behavior="summary_then_drop_oldest",
            token_counter=self.token_counter,
        )

        summary_result = summary_policy.summarize(
            window=window,
            selection_result=selection_result,
            truncation_result=truncation_result,
        )

        self.assertTrue(summary_result.summary_applied)
        self.assertGreaterEqual(summary_result.final_message_count, 1)
        self.assertTrue(summary_result.messages[0].metadata.get("summary", False))
        self.assertTrue(summary_result.messages[0].content.startswith("[history_"))

    def test_default_history_serialization_preserves_order(self) -> None:
        selection_policy = TokenAwareWindowSelectionPolicy(
            max_tokens=40,
            token_counter=self.token_counter,
        )
        truncation_policy = TokenAwareTruncationPolicy(
            max_tokens=40,
            token_counter=self.token_counter,
        )
        summary_policy = DeterministicSummaryPolicy(
            enabled=False,
            max_summary_chars=120,
            fallback_behavior="summary_then_drop_oldest",
            token_counter=self.token_counter,
        )
        serialization_policy = DefaultHistorySerializationPolicy()
        window = ContextWindow(
            session_id="session-1",
            messages=[
                ContextMessage(role="user", content="hello"),
                ContextMessage(role="assistant", content="hi"),
            ],
        )

        selection_result = selection_policy.select(window)
        truncation_result = truncation_policy.truncate(selection_result)
        summary_result = summary_policy.summarize(
            window=window,
            selection_result=selection_result,
            truncation_result=truncation_result,
        )
        serialized = serialization_policy.serialize(summary_result)

        self.assertEqual(
            serialized,
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ],
        )
