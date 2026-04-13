from __future__ import annotations

import unittest

from app.chat_runtime.engine import ChatRuntimeEngine
from app.chat_runtime.models import RuntimeTurnRequest
from app.config import AppConfig, ProviderConfig
from app.context.manager import ContextManager
from app.context.stores.in_memory import InMemoryContextStore
from app.providers.chat.base import BaseLLMProvider, ProviderInvocationError
from app.providers.chat.registry import ProviderRegistry
from app.rag.models import RetrievalResult, RetrievalTrace
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse, LLMStreamChunk
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler


class FakeSyncAndStreamProvider(BaseLLMProvider):
    provider_name = "openai"

    def chat(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=f"sync:{request.messages[-1].content}",
            provider=self.provider_name,
            model=request.model,
        )

    def stream_chat(self, request: LLMRequest):
        del request
        yield LLMStreamChunk(delta="你", sequence=1, done=False)
        yield LLMStreamChunk(delta="好", sequence=2, done=False)
        yield LLMStreamChunk(delta="", sequence=2, finish_reason="stop", done=True)


class FakeErrorStreamProvider(BaseLLMProvider):
    provider_name = "openai"

    def chat(self, request: LLMRequest) -> LLMResponse:
        del request
        return LLMResponse(content="ok", provider=self.provider_name, model="gpt-test")

    def stream_chat(self, request: LLMRequest):
        del request
        raise ProviderInvocationError("upstream stream failed")
        yield  # pragma: no cover


class StubRAGRuntime:
    def __init__(self, retrieval_result: RetrievalResult) -> None:
        self.enabled = True
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


class ChatRuntimeEngineTests(unittest.TestCase):
    def _build_engine(self, provider: BaseLLMProvider) -> ChatRuntimeEngine:
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
        assembler = ChatRequestAssembler(app_config=app_config, prompt_service=PromptService())
        rag_runtime = StubRAGRuntime(
            RetrievalResult(
                knowledge_block=None,
                citations=[],
                trace=RetrievalTrace(
                    status="succeeded",
                    query_text="hello",
                    top_k=4,
                    hit_count=0,
                    citation_count=0,
                ),
            )
        )
        return ChatRuntimeEngine(
            app_config=app_config,
            provider_registry=registry,
            context_manager=context_manager,
            request_assembler=assembler,
            rag_runtime=rag_runtime,  # type: ignore[arg-type]
        )

    def test_run_sync_executes_default_workflow_and_hooks(self) -> None:
        engine = self._build_engine(FakeSyncAndStreamProvider(ProviderConfig(name="openai", api_key="k1")))

        result = engine.run_sync(RuntimeTurnRequest(user_prompt="hello", provider_override="openai"))

        self.assertEqual(result.response_text, "sync:hello")
        self.assertEqual(result.provider, "openai")
        self.assertEqual(
            [event.step_name for event in result.trace.step_events],
            [
                "normalize_scope",
                "retrieve_knowledge",
                "assemble_llm_request",
                "normalize_llm_request",
                "select_provider",
                "invoke_model",
                "persist_context",
                "finalize_trace",
            ],
        )
        hook_event_names = {event.event_name for event in result.trace.hook_events}
        self.assertIn("before_request", hook_event_names)
        self.assertIn("after_retrieval", hook_event_names)
        self.assertIn("before_model_call", hook_event_names)
        self.assertIn("after_model_call", hook_event_names)

    def test_run_stream_completed_triggers_after_stream_completed_hook(self) -> None:
        engine = self._build_engine(FakeSyncAndStreamProvider(ProviderConfig(name="openai", api_key="k1")))

        events = list(engine.run_stream(RuntimeTurnRequest(user_prompt="你好", provider_override="openai", stream=True)))

        self.assertEqual(events[0]["event"], "response.started")
        self.assertEqual(events[-1]["event"], "response.completed")
        completed_trace = events[-1]["data"]["trace"]
        hook_event_names = {event["event_name"] for event in completed_trace["hook_events"]}
        self.assertIn("after_stream_completed", hook_event_names)

    def test_run_stream_failed_triggers_on_error_hook(self) -> None:
        engine = self._build_engine(FakeErrorStreamProvider(ProviderConfig(name="openai", api_key="k1")))

        events = list(engine.run_stream(RuntimeTurnRequest(user_prompt="你好", provider_override="openai", stream=True)))

        self.assertEqual(events[-1]["event"], "response.error")
        error_trace = events[-1]["data"]["trace"]
        hook_event_names = {event["event_name"] for event in error_trace["hook_events"]}
        self.assertIn("on_error", hook_event_names)

