from __future__ import annotations

import unittest

from app.api.schemas import ChatCancelRequest, ChatStreamRequest
from app.config import AppConfig, ProviderConfig
from app.context.manager import ContextManager
from app.context.stores.in_memory import InMemoryContextStore
from app.providers.base import BaseLLMProvider
from app.providers.registry import ProviderRegistry
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse, LLMStreamChunk
from app.services.cancellation_registry import CancellationRegistry
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler
from app.services.streaming_chat_service import StreamingChatService


class FakeStreamingProvider(BaseLLMProvider):
    provider_name = "openai"

    def chat(self, request: LLMRequest) -> LLMResponse:
        del request
        return LLMResponse(content="ok", provider=self.provider_name, model="gpt-test")

    def stream_chat(self, request: LLMRequest):
        del request
        yield LLMStreamChunk(delta="你", sequence=1, done=False)
        yield LLMStreamChunk(delta="好", sequence=2, done=False)
        yield LLMStreamChunk(delta="", sequence=2, finish_reason="stop", done=True)


class SlowStreamingProvider(BaseLLMProvider):
    provider_name = "openai"

    def chat(self, request: LLMRequest) -> LLMResponse:
        del request
        return LLMResponse(content="ok", provider=self.provider_name, model="gpt-test")

    def stream_chat(self, request: LLMRequest):
        del request
        for idx in range(1, 6):
            yield LLMStreamChunk(delta=str(idx), sequence=idx, done=False)
        yield LLMStreamChunk(delta="", sequence=5, finish_reason="stop", done=True)


class StreamingChatServiceTests(unittest.TestCase):
    def _build_service(self, provider: BaseLLMProvider) -> tuple[StreamingChatService, ContextManager]:
        providers = {
            "openai": ProviderConfig(name="openai", api_key="k1", default_model="gpt-test"),
            "deepseek": ProviderConfig(name="deepseek"),
            "gemini": ProviderConfig(name="gemini"),
            "doubao": ProviderConfig(name="doubao"),
            "tongyi": ProviderConfig(name="tongyi"),
        }
        app_config = AppConfig(
            default_provider="openai",
            providers=providers,
        )
        registry = ProviderRegistry(config=app_config, provider_overrides={"openai": provider})
        context_manager = ContextManager(store=InMemoryContextStore())
        assembler = ChatRequestAssembler(
            app_config=app_config,
            prompt_service=PromptService(),
        )
        service = StreamingChatService(
            app_config=app_config,
            registry=registry,
            prompt_service=PromptService(),
            context_manager=context_manager,
            request_assembler=assembler,
            cancellation_registry=CancellationRegistry(),
        )
        return service, context_manager

    def test_stream_completed_flow_updates_context(self) -> None:
        service, context_manager = self._build_service(FakeStreamingProvider(ProviderConfig(name="openai", api_key="k1")))

        events = list(
            service.stream_chat_from_user_prompt(
                ChatStreamRequest(
                    user_prompt="你好",
                    provider="openai",
                    session_id="session-1",
                    conversation_id="conv-1",
                )
            )
        )

        event_names = [event["event"] for event in events]
        self.assertEqual(event_names[0], "response.started")
        self.assertIn("response.delta", event_names)
        self.assertEqual(event_names[-1], "response.completed")

        window = context_manager.get_context("session-1", "conv-1")
        assistant_messages = [message for message in window.messages if message.role == "assistant"]
        self.assertTrue(assistant_messages)
        self.assertEqual(assistant_messages[-1].status, "completed")
        self.assertEqual(assistant_messages[-1].content, "你好")

    def test_stream_cancelled_flow_marks_message_cancelled(self) -> None:
        service, context_manager = self._build_service(SlowStreamingProvider(ProviderConfig(name="openai", api_key="k1")))

        generator = service.stream_chat_from_user_prompt(
            ChatStreamRequest(
                user_prompt="请慢慢回答",
                provider="openai",
                session_id="session-1",
                conversation_id="conv-1",
            )
        )
        started_event = next(generator)
        self.assertEqual(started_event["event"], "response.started")

        cancel_result = service.cancel_stream(
            ChatCancelRequest(request_id=started_event["data"]["request_id"])
        )
        self.assertTrue(cancel_result["found"])

        remaining_events = list(generator)
        self.assertEqual(remaining_events[-1]["event"], "response.cancelled")

        window = context_manager.get_context("session-1", "conv-1")
        assistant_messages = [message for message in window.messages if message.role == "assistant"]
        self.assertTrue(assistant_messages)
        self.assertEqual(assistant_messages[-1].status, "cancelled")
