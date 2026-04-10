from __future__ import annotations

import unittest

from app.api.schemas import ChatCancelRequest, ChatStreamRequest
from app.config import AppConfig, ProviderConfig
from app.context.manager import ContextManager
from app.context.stores.in_memory import InMemoryContextStore
from app.providers.base import BaseLLMProvider
from app.providers.registry import ProviderRegistry
from app.rag.models import Citation, RetrievalResult, RetrievalTrace
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse, LLMStreamChunk
from app.services.cancellation_registry import CancellationRegistry
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler
from app.services.streaming_chat_service import StreamingChatService


class FakeStreamingProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, provider_config: ProviderConfig) -> None:
        super().__init__(provider_config)
        self.last_request: LLMRequest | None = None

    def chat(self, request: LLMRequest) -> LLMResponse:
        del request
        return LLMResponse(content="ok", provider=self.provider_name, model="gpt-test")

    def stream_chat(self, request: LLMRequest):
        self.last_request = request
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


class StubRAGRuntime:
    def __init__(self, retrieval_result: RetrievalResult) -> None:
        self._retrieval_result = retrieval_result

    def retrieve_for_chat(
        self,
        *,
        query_text: str,
        metadata_filter: dict | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        del query_text, metadata_filter, top_k
        return self._retrieval_result


class StreamingChatServiceTests(unittest.TestCase):
    def _build_service(
        self,
        provider: BaseLLMProvider,
        *,
        rag_runtime: StubRAGRuntime | None = None,
    ) -> tuple[StreamingChatService, ContextManager]:
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
            rag_runtime=rag_runtime,  # type: ignore[arg-type]
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

    def test_stream_completed_includes_citations_and_delta_has_no_citations(self) -> None:
        provider = FakeStreamingProvider(ProviderConfig(name="openai", api_key="k1"))
        rag_runtime = StubRAGRuntime(
            RetrievalResult(
                knowledge_block="[knowledge_block]\n1. title=Doc One; source=file:///doc-1.md; score=0.9000\n   snippet=snippet",
                citations=[
                    Citation(
                        citation_id="c-1",
                        document_id="doc-1",
                        chunk_id="chk-1",
                        title="Doc One",
                        snippet="snippet",
                        origin_uri="file:///doc-1.md",
                        source_type="markdown_file",
                        updated_at="2026-04-10T00:00:00+00:00",
                        metadata={"score": 0.9},
                    )
                ],
                trace=RetrievalTrace(
                    status="succeeded",
                    query_text="你好",
                    top_k=4,
                    hit_count=1,
                    citation_count=1,
                ),
            )
        )
        service, _ = self._build_service(provider, rag_runtime=rag_runtime)

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

        delta_events = [event for event in events if event["event"] == "response.delta"]
        completed_event = [event for event in events if event["event"] == "response.completed"][0]
        self.assertTrue(delta_events)
        for event in delta_events:
            self.assertNotIn("citations", event["data"])
        self.assertEqual(len(completed_event["data"]["citations"]), 1)
        self.assertEqual(completed_event["data"]["citations"][0]["citation_id"], "c-1")
        assert provider.last_request is not None
        self.assertIn("[knowledge_block]", provider.last_request.messages[1].content)

    def test_stream_retrieval_degraded_still_completed_with_empty_citations(self) -> None:
        provider = FakeStreamingProvider(ProviderConfig(name="openai", api_key="k1"))
        rag_runtime = StubRAGRuntime(
            RetrievalResult.degraded(
                query_text="你好",
                top_k=4,
                error_type="RuntimeError",
                error_message="retrieval failed",
                latency_ms=10.1,
            )
        )
        service, _ = self._build_service(provider, rag_runtime=rag_runtime)

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

        self.assertEqual(events[-1]["event"], "response.completed")
        self.assertEqual(events[-1]["data"]["citations"], [])
        self.assertEqual(events[-1]["data"]["trace"]["retrieval"]["status"], "degraded")
