from __future__ import annotations

import unittest

from app.context.models import (
    ContextMessage,
    ContextWindow,
    RollingSummaryState,
    WorkingMemoryState,
)
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
        window = self.store.get_window("session-1", "conversation-1")

        self.assertEqual(window.session_id, "session-1")
        self.assertEqual(window.conversation_id, "conversation-1")
        self.assertEqual(window.message_count, 0)

    def test_append_and_get_window_are_conversation_scoped(self) -> None:
        self.store.append_message(
            "session-1",
            "conversation-1",
            ContextMessage(role="user", content="hello-c1"),
        )
        self.store.append_message(
            "session-1",
            "conversation-2",
            ContextMessage(role="user", content="hello-c2"),
        )

        c1_window = self.store.get_window("session-1", "conversation-1")
        c2_window = self.store.get_window("session-1", "conversation-2")
        self.assertEqual([m.content for m in c1_window.messages], ["hello-c1"])
        self.assertEqual([m.content for m in c2_window.messages], ["hello-c2"])

    def test_upsert_window_persists_layered_state(self) -> None:
        window = ContextWindow(
            session_id="session-1",
            conversation_id="conversation-1",
            messages=[ContextMessage(role="user", content="u1")],
            rolling_summary=RollingSummaryState(
                text="[rolling] summary",
                updated_at="2026-01-01T00:00:00+00:00",
                source_message_count=3,
            ),
            working_memory=WorkingMemoryState(
                active_goal="完成 Phase 4",
                constraints=["只做短期记忆"],
                decisions=["使用 Redis 持久化"],
                open_questions=["是否需要更精细 token 计数"],
                next_step="补齐测试",
                updated_at="2026-01-01T00:00:01+00:00",
            ),
            runtime_meta={"compaction_applied": True},
        )

        self.store.upsert_window(window)
        loaded = self.store.get_window("session-1", "conversation-1")

        self.assertEqual(loaded.message_count, 1)
        self.assertTrue(loaded.rolling_summary.has_content)
        self.assertEqual(loaded.rolling_summary.source_message_count, 3)
        self.assertEqual(loaded.working_memory.active_goal, "完成 Phase 4")
        self.assertEqual(loaded.runtime_meta.get("compaction_applied"), True)

    def test_reset_conversation_only_removes_target_scope(self) -> None:
        self.store.replace_messages(
            "session-1",
            "conversation-1",
            [ContextMessage(role="user", content="drop-c1")],
        )
        self.store.replace_messages(
            "session-1",
            "conversation-2",
            [ContextMessage(role="user", content="keep-c2")],
        )

        reset_window = self.store.reset_conversation("session-1", "conversation-1")
        c1_window = self.store.get_window("session-1", "conversation-1")
        c2_window = self.store.get_window("session-1", "conversation-2")

        self.assertEqual(reset_window.conversation_id, "conversation-1")
        self.assertEqual(c1_window.message_count, 0)
        self.assertEqual([m.content for m in c2_window.messages], ["keep-c2"])

    def test_reset_session_clears_all_conversations(self) -> None:
        self.store.append_message("session-1", "conversation-1", ContextMessage(role="user", content="c1"))
        self.store.append_message("session-1", "conversation-2", ContextMessage(role="user", content="c2"))

        self.store.reset_session("session-1")

        self.assertEqual(self.store.get_window("session-1", "conversation-1").message_count, 0)
        self.assertEqual(self.store.get_window("session-1", "conversation-2").message_count, 0)

    def test_ttl_is_set_after_write(self) -> None:
        self.store.append_message(
            "session-1",
            "conversation-1",
            ContextMessage(role="user", content="hello"),
        )

        conversation_key = "test:context:session:session-1:conversation:conversation-1"
        index_key = "test:context:session:session-1:conversations"
        conversation_ttl = self.redis_client.ttl(conversation_key)
        index_ttl = self.redis_client.ttl(index_key)
        self.assertGreater(conversation_ttl, 0)
        self.assertGreater(index_ttl, 0)
        self.assertLessEqual(conversation_ttl, 120)
        self.assertLessEqual(index_ttl, 120)

    def test_cross_instance_can_restore_history_before_ttl_expire(self) -> None:
        self.store.append_message(
            "session-1",
            "conversation-1",
            ContextMessage(role="user", content="hello"),
        )
        another_store = RedisContextStore(
            redis_url="redis://localhost:6379/0",
            key_prefix="test:context",
            session_ttl_seconds=120,
            redis_client=self.redis_client,
        )

        window = another_store.get_window("session-1", "conversation-1")

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
        "conversation-1",
        ContextMessage(role="user", content="u-1"),
    )
    store.append_message(
        "session-1",
        "conversation-1",
        ContextMessage(role="assistant", content="a-1"),
    )
    store.append_message(
        "session-1",
        "conversation-2",
        ContextMessage(role="user", content="u-2"),
    )

    after_append_c1 = [m.content for m in store.get_window("session-1", "conversation-1").messages]
    after_append_c2 = [m.content for m in store.get_window("session-1", "conversation-2").messages]

    store.reset_conversation("session-1", "conversation-1")
    after_reset_c1 = [m.content for m in store.get_window("session-1", "conversation-1").messages]
    after_reset_c2 = [m.content for m in store.get_window("session-1", "conversation-2").messages]

    store.replace_messages(
        "session-1",
        "conversation-2",
        [
            ContextMessage(role="user", content="replace-1"),
            ContextMessage(role="assistant", content="replace-2"),
        ],
    )
    after_replace_c2 = [m.content for m in store.get_window("session-1", "conversation-2").messages]

    store.reset_session("session-1")
    after_reset_session_c1 = [m.content for m in store.get_window("session-1", "conversation-1").messages]
    after_reset_session_c2 = [m.content for m in store.get_window("session-1", "conversation-2").messages]

    return {
        "after_append_c1": after_append_c1,
        "after_append_c2": after_append_c2,
        "after_reset_c1": after_reset_c1,
        "after_reset_c2": after_reset_c2,
        "after_replace_c2": after_replace_c2,
        "after_reset_session_c1": after_reset_session_c1,
        "after_reset_session_c2": after_reset_session_c2,
    }
