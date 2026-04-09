from __future__ import annotations

import unittest

from app.context.models import (
    ContextMessage,
    ContextSelectionResult,
    ContextSummaryResult,
    ContextTruncationResult,
    ContextWindow,
)
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.summary import DeterministicSummaryPolicy
from app.context.policies.tokenizer import CharacterTokenCounter
from app.context.policies.truncation import TokenAwareTruncationPolicy
from app.context.policies.window_selection import TokenAwareWindowSelectionPolicy


class ContextPoliciesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.token_counter = CharacterTokenCounter(message_overhead_tokens=1)

    def test_token_aware_window_selection_uses_recent_messages_within_budget(self) -> None:
        window = ContextWindow(
            session_id="session-1",
            messages=[
                ContextMessage(role="user", content="aaaa"),
                ContextMessage(role="assistant", content="bbbb"),
                ContextMessage(role="user", content="cccc"),
            ],
        )
        policy = TokenAwareWindowSelectionPolicy(
            window_max_tokens=10,
            token_counter=self.token_counter,
        )

        result = policy.select(window)

        self.assertEqual(result.source_message_count, 3)
        self.assertEqual(result.selected_message_count, 2)
        self.assertEqual(result.dropped_message_count, 1)
        self.assertEqual(
            [message.content for message in result.selected_messages],
            ["bbbb", "cccc"],
        )
        self.assertEqual(result.selected_token_count, 10)

    def test_token_aware_truncation_truncates_single_oversized_recent_message(self) -> None:
        selection_policy = TokenAwareWindowSelectionPolicy(
            window_max_tokens=40,
            token_counter=self.token_counter,
        )
        window = ContextWindow(
            session_id="session-1",
            messages=[
                ContextMessage(role="assistant", content="12345678901234567890"),
            ],
        )
        selection_result = selection_policy.select(window)
        truncation_policy = TokenAwareTruncationPolicy(
            truncation_max_tokens=12,
            token_counter=self.token_counter,
        )

        truncation_result = truncation_policy.truncate(selection_result)

        self.assertTrue(truncation_result.truncation_applied)
        self.assertEqual(truncation_result.final_message_count, 1)
        self.assertLessEqual(truncation_result.final_token_count, 12)
        self.assertTrue(truncation_result.messages[0].metadata.get("truncated", False))

    def test_summary_policy_does_not_drop_latest_raw_message_by_default(self) -> None:
        latest_raw = ContextMessage(role="assistant", content="latest-raw-message")
        older_dropped = [ContextMessage(role="user", content="old-1")]
        window = ContextWindow(session_id="session-1", messages=older_dropped + [latest_raw])
        selection_result = ContextSelectionResult(
            session_id="session-1",
            conversation_id="conversation-1",
            source_message_count=2,
            source_token_count=self.token_counter.count_messages_tokens(window.messages),
            token_budget=32,
            selected_messages=[latest_raw],
            dropped_messages=older_dropped,
            selected_token_count=self.token_counter.count_message_tokens(latest_raw),
            selection_policy="window_selection.token_aware",
        )
        truncation_result = ContextTruncationResult(
            session_id="session-1",
            conversation_id="conversation-1",
            source_message_count=2,
            source_token_count=selection_result.source_token_count,
            input_message_count=1,
            input_token_count=selection_result.selected_token_count,
            truncation_token_budget=selection_result.selected_token_count,
            messages=[latest_raw],
            dropped_messages=[],
            final_token_count=selection_result.selected_token_count,
            truncation_policy="truncation.token_aware",
        )
        summary_policy = DeterministicSummaryPolicy(
            enabled=True,
            max_summary_chars=120,
            fallback_behavior="summary_then_drop_oldest",
            token_counter=self.token_counter,
        )

        summary_result = summary_policy.summarize(
            window=window,
            selection=selection_result,
            truncation=truncation_result,
        )

        self.assertTrue(summary_result.messages)
        self.assertEqual(summary_result.messages[-1].content, latest_raw.content)
        self.assertFalse(all(msg.metadata.get("summary", False) for msg in summary_result.messages))

    def test_fallback_behaviors_have_different_outputs(self) -> None:
        dropped_messages = [ContextMessage(role="user", content="old-context")]
        raw_old = ContextMessage(role="assistant", content="older-raw")
        raw_latest = ContextMessage(role="user", content="latest-raw")
        window = ContextWindow(
            session_id="session-1",
            messages=dropped_messages + [raw_old, raw_latest],
        )
        selection_result = ContextSelectionResult(
            session_id="session-1",
            conversation_id="conversation-1",
            source_message_count=3,
            source_token_count=self.token_counter.count_messages_tokens(window.messages),
            token_budget=30,
            selected_messages=[raw_old, raw_latest],
            dropped_messages=dropped_messages,
            selected_token_count=self.token_counter.count_messages_tokens([raw_old, raw_latest]),
            selection_policy="window_selection.token_aware",
        )
        truncation_result = ContextTruncationResult(
            session_id="session-1",
            conversation_id="conversation-1",
            source_message_count=3,
            source_token_count=selection_result.source_token_count,
            input_message_count=2,
            input_token_count=selection_result.selected_token_count,
            truncation_token_budget=20,
            messages=[raw_old, raw_latest],
            dropped_messages=[],
            final_token_count=selection_result.selected_token_count,
            truncation_policy="truncation.token_aware",
        )

        summary_then_drop_oldest = DeterministicSummaryPolicy(
            enabled=True,
            max_summary_chars=120,
            fallback_behavior="summary_then_drop_oldest",
            token_counter=self.token_counter,
        ).summarize(
            window=window,
            selection=selection_result,
            truncation=truncation_result,
        )
        drop_oldest = DeterministicSummaryPolicy(
            enabled=True,
            max_summary_chars=120,
            fallback_behavior="drop_oldest",
            token_counter=self.token_counter,
        ).summarize(
            window=window,
            selection=selection_result,
            truncation=truncation_result,
        )

        self.assertTrue(summary_then_drop_oldest.messages[0].metadata.get("summary", False))
        self.assertFalse(
            drop_oldest.messages[0].metadata.get("summary", False)
            if drop_oldest.messages
            else True
        )
        self.assertEqual(summary_then_drop_oldest.messages[-1].content, "latest-raw")
        self.assertEqual(drop_oldest.messages[-1].content, "latest-raw")

    def test_summary_disabled_uses_noop_path(self) -> None:
        messages = [ContextMessage(role="assistant", content="kept")]
        window = ContextWindow(session_id="session-1", messages=messages)
        selection_result = ContextSelectionResult(
            session_id="session-1",
            conversation_id="conversation-1",
            source_message_count=1,
            source_token_count=self.token_counter.count_messages_tokens(messages),
            token_budget=20,
            selected_messages=list(messages),
            dropped_messages=[],
            selected_token_count=self.token_counter.count_messages_tokens(messages),
            selection_policy="window_selection.token_aware",
        )
        truncation_result = ContextTruncationResult(
            session_id="session-1",
            conversation_id="conversation-1",
            source_message_count=1,
            source_token_count=selection_result.source_token_count,
            input_message_count=1,
            input_token_count=selection_result.selected_token_count,
            truncation_token_budget=20,
            messages=list(messages),
            dropped_messages=[],
            final_token_count=selection_result.selected_token_count,
            truncation_policy="truncation.token_aware",
        )
        summary_result = DeterministicSummaryPolicy(
            enabled=False,
            max_summary_chars=120,
            fallback_behavior="summary_then_drop_oldest",
            token_counter=self.token_counter,
        ).summarize(
            window=window,
            selection=selection_result,
            truncation=truncation_result,
        )

        self.assertFalse(summary_result.summary_applied)
        self.assertEqual(summary_result.messages, messages)

    def test_default_history_serialization_preserves_order(self) -> None:
        summary_result = ContextSummaryResult(
            session_id="session-1",
            conversation_id="conversation-1",
            source_message_count=2,
            source_token_count=20,
            input_message_count=2,
            input_token_count=20,
            token_budget=20,
            messages=[
                ContextMessage(role="user", content="hello"),
                ContextMessage(role="assistant", content="hi"),
            ],
            dropped_messages=[],
            summary_policy="summary.noop",
            summary_applied=False,
            summary_text=None,
            final_token_count=20,
        )
        serialized = DefaultHistorySerializationPolicy().serialize(summary_result)

        self.assertEqual(
            serialized,
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ],
        )
