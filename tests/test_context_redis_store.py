from __future__ import annotations

import unittest

from app.context.models import ContextMessage
from app.context.stores.in_memory import InMemoryContextStore
from app.context.stores.redis_store import RedisContextStore

try:
    import fakeredis
except ImportError:  # pragma: no cover - 依赖缺失时跳过
    fakeredis = None


@unittest.skipIf(fakeredis is None, "未安装 fakeredis，跳过 Redis store 测试。")
class RedisContextStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.redis_client = fakeredis.FakeRedis(decode_responses=True)
        self.store = RedisContextStore(
            redis_url="redis://localhost:6379/0",
            key_prefix="test:context",
            session_ttl_seconds=120,
            redis_client=self.redis_client,
        )

    def test_get_window_returns_empty_when_missing(self) -> None:
        window = self.store.get_window("session-1")

        self.assertEqual(window.session_id, "session-1")
        self.assertEqual(window.message_count, 0)

    def test_append_and_get_window(self) -> None:
        self.store.append_message(
            "session-1",
            ContextMessage(
                role="user",
                content="hello",
                metadata={"conversation_id": "c-1"},
            ),
        )
        self.store.append_message(
            "session-1",
            ContextMessage(
                role="assistant",
                content="hi",
                metadata={"conversation_id": "c-1"},
            ),
        )

        window = self.store.get_window("session-1")
        self.assertEqual(window.message_count, 2)
        self.assertEqual([message.role for message in window.messages], ["user", "assistant"])
        self.assertEqual(window.messages[0].metadata["conversation_id"], "c-1")

    def test_replace_messages(self) -> None:
        replaced = self.store.replace_messages(
            "session-1",
            [
                ContextMessage(role="user", content="n1"),
                ContextMessage(role="assistant", content="n2"),
            ],
        )

        self.assertEqual([message.content for message in replaced.messages], ["n1", "n2"])
        self.assertEqual(
            [message.content for message in self.store.get_window("session-1").messages],
            ["n1", "n2"],
        )

    def test_reset_conversation_only_removes_target_messages(self) -> None:
        self.store.replace_messages(
            "session-1",
            [
                ContextMessage(role="user", content="drop-1", metadata={"conversation_id": "c-1"}),
                ContextMessage(role="assistant", content="drop-2", metadata={"conversation_id": "c-1"}),
                ContextMessage(role="user", content="keep-1", metadata={"conversation_id": "c-2"}),
            ],
        )

        window = self.store.reset_conversation("session-1", "c-1")

        self.assertEqual([message.content for message in window.messages], ["keep-1"])

    def test_reset_session_clears_window(self) -> None:
        self.store.append_message("session-1", ContextMessage(role="user", content="hello"))

        cleared = self.store.clear_window("session-1")

        self.assertEqual(cleared.message_count, 0)
        self.assertEqual(self.store.get_window("session-1").message_count, 0)

    def test_ttl_is_set_after_write(self) -> None:
        self.store.append_message("session-1", ContextMessage(role="user", content="hello"))

        ttl = self.redis_client.ttl("test:context:session:session-1")
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, 120)

    def test_cross_instance_can_restore_history_before_ttl_expire(self) -> None:
        self.store.append_message("session-1", ContextMessage(role="user", content="hello"))
        another_store = RedisContextStore(
            redis_url="redis://localhost:6379/0",
            key_prefix="test:context",
            session_ttl_seconds=120,
            redis_client=self.redis_client,
        )

        window = another_store.get_window("session-1")

        self.assertEqual(window.message_count, 1)
        self.assertEqual(window.messages[0].content, "hello")

    def test_backend_parity_between_memory_and_redis(self) -> None:
        memory_store = InMemoryContextStore()
        redis_store = RedisContextStore(
            redis_url="redis://localhost:6379/0",
            key_prefix="test:parity",
            session_ttl_seconds=120,
            redis_client=self.redis_client,
        )

        memory_snapshot = _run_store_sequence(memory_store)
        redis_snapshot = _run_store_sequence(redis_store)

        self.assertEqual(memory_snapshot, redis_snapshot)


def _run_store_sequence(store) -> dict[str, object]:
    store.append_message(
        "session-1",
        ContextMessage(role="user", content="u-1", metadata={"conversation_id": "c-1"}),
    )
    store.append_message(
        "session-1",
        ContextMessage(role="assistant", content="a-1", metadata={"conversation_id": "c-1"}),
    )
    store.append_message(
        "session-1",
        ContextMessage(role="user", content="u-2", metadata={"conversation_id": "c-2"}),
    )
    after_append = [message.content for message in store.get_window("session-1").messages]

    store.reset_conversation("session-1", "c-1")
    after_conversation_reset = [
        message.content for message in store.get_window("session-1").messages
    ]

    store.replace_messages(
        "session-1",
        [
            ContextMessage(role="user", content="replace-1"),
            ContextMessage(role="assistant", content="replace-2"),
        ],
    )
    after_replace = [message.content for message in store.get_window("session-1").messages]

    store.clear_window("session-1")
    after_clear = [message.content for message in store.get_window("session-1").messages]

    return {
        "after_append": after_append,
        "after_conversation_reset": after_conversation_reset,
        "after_replace": after_replace,
        "after_clear": after_clear,
    }
