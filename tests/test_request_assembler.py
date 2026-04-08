from __future__ import annotations

import unittest

from app.api.schemas import ChatRequest
from app.config import AppConfig, ProviderConfig
from app.context.manager import ContextManager
from app.context.models import ContextMessage
from app.context.policies.context_policy import ContextPolicyPipeline
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.summary import DeterministicSummaryPolicy
from app.context.policies.tokenizer import CharacterTokenCounter
from app.context.policies.truncation import TokenAwareTruncationPolicy
from app.context.policies.window_selection import TokenAwareWindowSelectionPolicy
from app.context.stores.in_memory import InMemoryContextStore
from app.context.stores.redis_store import RedisContextStore
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler

try:
    import fakeredis
except ImportError:  # pragma: no cover - 依赖缺失时跳过
    fakeredis = None


class StubPromptService(PromptService):
    def get_default_system_prompt(self) -> str:
        return "SYSTEM"


class RequestAssemblerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AppConfig(
            default_provider="openai",
            timeout_seconds=60.0,
            providers={
                "openai": ProviderConfig(name="openai", api_key="k1", default_model="gpt-test"),
                "deepseek": ProviderConfig(name="deepseek"),
                "gemini": ProviderConfig(name="gemini"),
                "doubao": ProviderConfig(name="doubao"),
                "tongyi": ProviderConfig(name="tongyi"),
            },
        )
        token_counter = CharacterTokenCounter()
        self.pipeline = ContextPolicyPipeline(
            selection_policy=TokenAwareWindowSelectionPolicy(
                max_tokens=24,
                token_counter=token_counter,
            ),
            truncation_policy=TokenAwareTruncationPolicy(
                max_tokens=18,
                token_counter=token_counter,
            ),
            summary_policy=DeterministicSummaryPolicy(
                enabled=True,
                max_summary_chars=120,
                fallback_behavior="summary_then_drop_oldest",
                token_counter=token_counter,
            ),
            serialization_policy=DefaultHistorySerializationPolicy(),
        )

    def test_assemble_without_session_does_not_use_server_history(self) -> None:
        manager = ContextManager(store=InMemoryContextStore())
        assembler = ChatRequestAssembler(
            app_config=self.config,
            prompt_service=StubPromptService(),
            context_policy_pipeline=self.pipeline,
        )

        request = assembler.assemble_from_user_prompt(
            ChatRequest(
                user_prompt="hello",
                provider="openai",
                stream=False,
            ),
            context_manager=manager,
        )

        self.assertEqual([message.role for message in request.messages], ["system", "user"])
        trace = request.metadata["context_assembly"]
        self.assertFalse(trace["enabled"])
        self.assertEqual(trace["source_message_count"], 0)
        self.assertEqual(trace["selection_selected_message_count"], 0)
        self.assertEqual(trace["serialized_message_count"], 0)
        self.assertIn("summary_policy", trace)
        self.assertIn("token_counter", trace)

    def test_assemble_with_session_uses_token_aware_pipeline_and_trace(self) -> None:
        manager = ContextManager(store=InMemoryContextStore())
        manager.replace_context_messages(
            "session-1",
            [
                ContextMessage(role="user", content="old-user-1"),
                ContextMessage(role="assistant", content="old-assistant-1"),
                ContextMessage(role="user", content="latest-user"),
            ],
        )
        assembler = ChatRequestAssembler(
            app_config=self.config,
            prompt_service=StubPromptService(),
            context_policy_pipeline=self.pipeline,
        )

        request = assembler.assemble_from_user_prompt(
            ChatRequest(
                user_prompt="new-input",
                provider="openai",
                stream=False,
                session_id="session-1",
                conversation_id="conversation-1",
                request_id="request-1",
            ),
            context_manager=manager,
        )

        self.assertEqual(request.messages[0].role, "system")
        self.assertEqual(request.messages[-1].role, "user")
        trace = request.metadata["context_assembly"]
        self.assertTrue(trace["enabled"])
        self.assertEqual(trace["session_id"], "session-1")
        self.assertEqual(trace["source_message_count"], 3)
        self.assertIn("selection_token_budget", trace)
        self.assertIn("truncation_applied", trace)
        self.assertIn("summary_applied", trace)
        self.assertEqual(trace["selection_policy"], "window_selection.token_aware")
        self.assertEqual(trace["truncation_policy"], "truncation.token_aware")
        self.assertEqual(trace["summary_policy"], "summary.deterministic_compaction")
        self.assertEqual(trace["serialization_policy"], "serialization.default_history")
        self.assertEqual(request.metadata["used_context_history"], trace)

    def test_assemble_does_not_keep_full_raw_history_metadata(self) -> None:
        manager = ContextManager(store=InMemoryContextStore())
        manager.replace_context_messages(
            "session-1",
            [
                ContextMessage(role="user", content="msg-1"),
                ContextMessage(role="assistant", content="msg-2"),
                ContextMessage(role="user", content="msg-3"),
                ContextMessage(role="assistant", content="msg-4"),
            ],
        )
        assembler = ChatRequestAssembler(
            app_config=self.config,
            prompt_service=StubPromptService(),
            context_policy_pipeline=self.pipeline,
        )

        request = assembler.assemble_from_user_prompt(
            ChatRequest(
                user_prompt="latest",
                provider="openai",
                stream=False,
                session_id="session-1",
            ),
            context_manager=manager,
        )

        trace = request.metadata["context_assembly"]
        self.assertNotIn("messages", trace)
        self.assertGreaterEqual(trace["dropped_message_count"], 0)
        self.assertEqual(
            trace["total_dropped_message_count"],
            trace["selection_dropped_message_count"]
            + trace["truncation_dropped_message_count"]
            + trace["summary_dropped_message_count"],
        )

    @unittest.skipIf(fakeredis is None, "未安装 fakeredis，跳过 Redis assembler 测试。")
    def test_assemble_can_read_history_from_redis_store(self) -> None:
        redis_client = fakeredis.FakeRedis(decode_responses=True)
        manager = ContextManager(
            store=RedisContextStore(
                redis_url="redis://localhost:6379/0",
                key_prefix="test:assembler",
                session_ttl_seconds=120,
                redis_client=redis_client,
            )
        )
        manager.replace_context_messages(
            "session-redis",
            [
                ContextMessage(role="user", content="redis-user-1"),
                ContextMessage(role="assistant", content="redis-assistant-1"),
            ],
        )
        assembler = ChatRequestAssembler(
            app_config=self.config,
            prompt_service=StubPromptService(),
            context_policy_pipeline=self.pipeline,
        )

        request = assembler.assemble_from_user_prompt(
            ChatRequest(
                user_prompt="new-input",
                provider="openai",
                stream=False,
                session_id="session-redis",
                conversation_id="conversation-redis",
                request_id="request-redis",
            ),
            context_manager=manager,
        )

        trace = request.metadata["context_assembly"]
        self.assertTrue(trace["enabled"])
        self.assertEqual(trace["session_id"], "session-redis")
        self.assertEqual(trace["source_message_count"], 2)
        self.assertGreaterEqual(trace["serialized_message_count"], 1)
