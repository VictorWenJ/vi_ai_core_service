from __future__ import annotations

import unittest

from app.config import ContextMemoryConfig
from app.context.manager import ContextManager
from app.context.models import ContextMessage
from app.context.stores.in_memory import InMemoryContextStore


class ContextManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = ContextManager(store=InMemoryContextStore())

    def test_conversation_scope_isolation_and_resets(self) -> None:
        self.manager.replace_context_messages(
            "session-1",
            [ContextMessage(role="user", content="c1-msg")],
            conversation_id="conversation-1",
        )
        self.manager.replace_context_messages(
            "session-1",
            [ContextMessage(role="user", content="c2-msg")],
            conversation_id="conversation-2",
        )

        c1_window = self.manager.get_context("session-1", "conversation-1")
        c2_window = self.manager.get_context("session-1", "conversation-2")
        self.assertEqual([m.content for m in c1_window.messages], ["c1-msg"])
        self.assertEqual([m.content for m in c2_window.messages], ["c2-msg"])

        self.manager.reset_conversation("session-1", "conversation-1")
        c1_after_reset = self.manager.get_context("session-1", "conversation-1")
        c2_after_reset = self.manager.get_context("session-1", "conversation-2")
        self.assertEqual(c1_after_reset.message_count, 0)
        self.assertEqual([m.content for m in c2_after_reset.messages], ["c2-msg"])

        self.manager.reset_session("session-1")
        self.assertEqual(
            self.manager.get_context("session-1", "conversation-1").message_count,
            0,
        )
        self.assertEqual(
            self.manager.get_context("session-1", "conversation-2").message_count,
            0,
        )

    def test_update_after_chat_turn_compacts_recent_raw_and_updates_summary(self) -> None:
        self.manager.replace_context_messages(
            "session-1",
            [
                ContextMessage(role="user", content="old-" + "a" * 40),
                ContextMessage(role="assistant", content="old-" + "b" * 40),
                ContextMessage(role="user", content="old-" + "c" * 40),
                ContextMessage(role="assistant", content="old-" + "d" * 40),
            ],
            conversation_id="conversation-1",
        )

        updated_window = self.manager.update_after_chat_turn(
            session_id="session-1",
            conversation_id="conversation-1",
            user_content="new-user-" + "u" * 40,
            assistant_content="new-assistant-" + "v" * 40,
            metadata={"request_id": "req-1"},
            memory_config=ContextMemoryConfig(
                layered_memory_enabled=True,
                recent_raw_max_token_budget=80,
                recent_raw_min_keep_messages=2,
                rolling_summary_enabled=True,
                rolling_summary_max_chars=400,
                working_memory_enabled=False,
                working_memory_max_items_per_section=5,
                working_memory_max_value_chars=160,
            ),
        )

        self.assertTrue(updated_window.runtime_meta.get("compaction_applied"))
        self.assertGreater(updated_window.runtime_meta.get("compacted_message_count", 0), 0)
        self.assertTrue(updated_window.rolling_summary.has_content)
        self.assertGreater(updated_window.rolling_summary.source_message_count, 0)
        self.assertGreaterEqual(updated_window.message_count, 2)

    def test_update_after_chat_turn_updates_working_memory(self) -> None:
        updated_window = self.manager.update_after_chat_turn(
            session_id="session-1",
            conversation_id="conversation-1",
            user_content="我想完成接口治理，必须保持分层边界。",
            assistant_content="决定采用最小改动方案。下一步先补测试。",
            metadata={"request_id": "req-2"},
            memory_config=ContextMemoryConfig(
                layered_memory_enabled=True,
                recent_raw_max_token_budget=400,
                recent_raw_min_keep_messages=2,
                rolling_summary_enabled=False,
                rolling_summary_max_chars=400,
                working_memory_enabled=True,
                working_memory_max_items_per_section=3,
                working_memory_max_value_chars=80,
            ),
        )

        self.assertEqual(updated_window.working_memory.active_goal, "我想完成接口治理，必须保持分层边界。")
        self.assertTrue(updated_window.working_memory.constraints)
        self.assertTrue(updated_window.working_memory.decisions)
        self.assertIsNotNone(updated_window.working_memory.next_step)

    def test_update_after_stream_completion_only_on_completed_assistant(self) -> None:
        user_id = "um-1"
        assistant_id = "am-1"
        self.manager.append_user_message(
            session_id="session-1",
            conversation_id="conversation-1",
            content="你好",
            message_id=user_id,
        )
        self.manager.create_assistant_placeholder(
            session_id="session-1",
            conversation_id="conversation-1",
            assistant_message_id=assistant_id,
        )
        self.manager.finalize_assistant_message(
            session_id="session-1",
            conversation_id="conversation-1",
            assistant_message_id=assistant_id,
            status="cancelled",
            content="partial",
            error_code="cancelled",
        )
        window_after_cancel = self.manager.update_after_stream_completion(
            session_id="session-1",
            conversation_id="conversation-1",
            user_message_id=user_id,
            assistant_message_id=assistant_id,
            memory_config=ContextMemoryConfig(),
        )
        self.assertEqual(window_after_cancel.messages[-1].status, "cancelled")

        self.manager.finalize_assistant_message(
            session_id="session-1",
            conversation_id="conversation-1",
            assistant_message_id=assistant_id,
            status="completed",
            content="最终回答",
            finish_reason="stop",
        )
        window_after_completed = self.manager.update_after_stream_completion(
            session_id="session-1",
            conversation_id="conversation-1",
            user_message_id=user_id,
            assistant_message_id=assistant_id,
            memory_config=ContextMemoryConfig(),
        )
        self.assertEqual(window_after_completed.messages[-1].status, "completed")
