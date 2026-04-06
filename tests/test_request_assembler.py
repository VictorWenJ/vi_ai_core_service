from __future__ import annotations

import unittest

from app.config import AppConfig, ProviderConfig
from app.context.manager import ContextManager
from app.context.models import ContextMessage
from app.context.policies.context_policy import ContextPolicyPipeline
from app.context.policies.defaults import DEFAULT_HISTORY_WINDOW_SIZE
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.truncation import CharacterBudgetTruncationPolicy
from app.context.policies.window_selection import LastNMessagesSelectionPolicy
from app.context.stores.in_memory import InMemoryContextStore
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler


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

    def test_assemble_without_session_does_not_use_server_history(self) -> None:
        manager = ContextManager(store=InMemoryContextStore())
        assembler = ChatRequestAssembler(
            config=self.config,
            prompt_service=StubPromptService(),
        )

        request, normalized_session_id = assembler.assemble_from_user_prompt(
            user_prompt="hello",
            provider="openai",
            model=None,
            temperature=None,
            max_tokens=None,
            system_prompt=None,
            stream=False,
            session_id=None,
            conversation_id=None,
            request_id=None,
            metadata=None,
            context_manager=manager,
        )

        self.assertIsNone(normalized_session_id)
        self.assertEqual([message.role for message in request.messages], ["system", "user"])
        trace = request.metadata["context_assembly"]
        self.assertFalse(trace["enabled"])
        self.assertEqual(trace["raw_message_count"], 0)
        self.assertEqual(trace["selected_message_count"], 0)
        self.assertEqual(trace["serialized_message_count"], 0)

    def test_assemble_with_session_uses_recent_history_window_and_trace(self) -> None:
        manager = ContextManager(store=InMemoryContextStore())
        for index in range(12):
            role = "user" if index % 2 == 0 else "assistant"
            manager.append_message("session-1", role, f"msg-{index + 1}")
        assembler = ChatRequestAssembler(
            config=self.config,
            prompt_service=StubPromptService(),
        )

        request, normalized_session_id = assembler.assemble_from_user_prompt(
            user_prompt="latest",
            provider="openai",
            model=None,
            temperature=None,
            max_tokens=None,
            system_prompt=None,
            stream=False,
            session_id="session-1",
            conversation_id=None,
            request_id=None,
            metadata=None,
            context_manager=manager,
        )

        self.assertEqual(normalized_session_id, "session-1")
        self.assertEqual(request.messages[0].role, "system")
        self.assertEqual(request.messages[-1].role, "user")
        selected_history = request.messages[1:-1]
        self.assertEqual(len(selected_history), DEFAULT_HISTORY_WINDOW_SIZE)
        self.assertEqual(selected_history[0].content, "msg-5")
        self.assertEqual(selected_history[-1].content, "msg-12")

        trace = request.metadata["context_assembly"]
        self.assertTrue(trace["enabled"])
        self.assertEqual(trace["raw_message_count"], 12)
        self.assertEqual(trace["selected_message_count"], DEFAULT_HISTORY_WINDOW_SIZE)
        self.assertEqual(trace["dropped_message_count"], 4)
        self.assertEqual(trace["serialized_message_count"], DEFAULT_HISTORY_WINDOW_SIZE)
        self.assertIn("selection_policy", trace)
        self.assertIn("truncation_policy", trace)
        self.assertIn("serialization_policy", trace)
        self.assertEqual(trace, request.metadata["used_context_history"])

    def test_assemble_applies_truncation_policy_placeholder(self) -> None:
        manager = ContextManager(store=InMemoryContextStore())
        manager.replace_context_messages(
            "session-1",
            [
                ContextMessage(role="user", content="12345"),
                ContextMessage(role="assistant", content="67890"),
                ContextMessage(role="user", content="abcde"),
            ],
        )
        pipeline = ContextPolicyPipeline(
            selection_policy=LastNMessagesSelectionPolicy(max_messages=3),
            truncation_policy=CharacterBudgetTruncationPolicy(max_characters=10),
            serialization_policy=DefaultHistorySerializationPolicy(),
        )
        assembler = ChatRequestAssembler(
            config=self.config,
            prompt_service=StubPromptService(),
            context_policy_pipeline=pipeline,
        )

        request, _ = assembler.assemble_from_user_prompt(
            user_prompt="latest",
            provider="openai",
            model=None,
            temperature=None,
            max_tokens=None,
            system_prompt=None,
            stream=False,
            session_id="session-1",
            conversation_id=None,
            request_id=None,
            metadata=None,
            context_manager=manager,
        )

        selected_history = request.messages[1:-1]
        self.assertEqual([message.content for message in selected_history], ["67890", "abcde"])
        trace = request.metadata["context_assembly"]
        self.assertEqual(trace["selected_message_count"], 3)
        self.assertEqual(trace["serialized_message_count"], 2)
        self.assertEqual(trace["truncated_message_count"], 1)
