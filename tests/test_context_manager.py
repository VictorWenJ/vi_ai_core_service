from __future__ import annotations

import unittest

from app.context.models import ContextMessage
from app.context.manager import ContextManager
from app.context.stores.redis_store import RedisContextStore

try:
    import fakeredis
except ImportError:  # pragma: no cover - 依赖缺失时跳过
    fakeredis = None


class ContextManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = ContextManager()

    def test_get_context_returns_empty_window_when_missing(self) -> None:
        window = self.manager.get_context("session-1")

        self.assertEqual(window.session_id, "session-1")
        self.assertEqual(window.messages, [])

    def test_append_user_and_assistant_messages(self) -> None:
        self.manager.append_user_message(
            "session-1",
            "hello",
            metadata={"conversation_id": "c-1"},
        )
        self.manager.append_assistant_message(
            "session-1",
            "hi",
            metadata={"conversation_id": "c-1"},
        )

        window = self.manager.get_context("session-1")
        self.assertEqual([message.role for message in window.messages], ["user", "assistant"])
        self.assertEqual([message.content for message in window.messages], ["hello", "hi"])
        self.assertEqual(window.messages[0].metadata["conversation_id"], "c-1")

    def test_clear_context_resets_window_messages(self) -> None:
        self.manager.append_user_message("session-1", "hello")
        cleared_window = self.manager.clear_context("session-1")

        self.assertEqual(cleared_window.session_id, "session-1")
        self.assertEqual(cleared_window.messages, [])

    def test_replace_context_messages_overwrites_existing_messages(self) -> None:
        self.manager.append_user_message("session-1", "stale")
        replaced = self.manager.replace_context_messages(
            "session-1",
            [
                ContextMessage(role="user", content="new-user"),
                ContextMessage(role="assistant", content="new-assistant"),
            ],
        )

        self.assertEqual([message.content for message in replaced.messages], ["new-user", "new-assistant"])
        window = self.manager.get_context("session-1")
        self.assertEqual([message.content for message in window.messages], ["new-user", "new-assistant"])

    def test_reset_session_clears_all_messages(self) -> None:
        self.manager.append_user_message("session-1", "hello")
        self.manager.append_assistant_message("session-1", "hi")

        window = self.manager.reset_session("session-1")

        self.assertEqual(window.session_id, "session-1")
        self.assertEqual(window.messages, [])

    def test_reset_conversation_only_removes_target_conversation_messages(self) -> None:
        self.manager.append_user_message(
            "session-1",
            "message-1",
            metadata={"conversation_id": "c-1"},
        )
        self.manager.append_assistant_message(
            "session-1",
            "message-2",
            metadata={"conversation_id": "c-1"},
        )
        self.manager.append_user_message(
            "session-1",
            "keep-1",
            metadata={"conversation_id": "c-2"},
        )

        window = self.manager.reset_conversation("session-1", "c-1")

        self.assertEqual([message.content for message in window.messages], ["keep-1"])

    @unittest.skipIf(fakeredis is None, "未安装 fakeredis，跳过 Redis manager 测试。")
    def test_manager_behavior_is_consistent_on_redis_store(self) -> None:
        redis_client = fakeredis.FakeRedis(decode_responses=True)
        manager = ContextManager(
            store=RedisContextStore(
                redis_url="redis://localhost:6379/0",
                key_prefix="test:manager",
                session_ttl_seconds=120,
                redis_client=redis_client,
            )
        )

        manager.append_user_message("session-1", "hello", metadata={"conversation_id": "c-1"})
        manager.append_assistant_message("session-1", "hi", metadata={"conversation_id": "c-1"})
        manager.append_user_message("session-1", "keep", metadata={"conversation_id": "c-2"})
        manager.reset_conversation("session-1", "c-1")
        window = manager.get_context("session-1")

        self.assertEqual([message.content for message in window.messages], ["keep"])

        manager.reset_session("session-1")
        cleared = manager.get_context("session-1")
        self.assertEqual(cleared.messages, [])
