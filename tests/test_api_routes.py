from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import AppConfig, ProviderConfig
from app.context.manager import ContextManager
from app.context.stores.redis_store import RedisContextStore
from app.providers.base import BaseLLMProvider
from app.providers.registry import ProviderRegistry
from app.rag.models import Citation, RetrievalTrace
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse
from app.services.chat_result import ChatServiceResult
from app.server import app
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceNotImplementedError,
    ServiceValidationError,
)
from app.services.llm_service import LLMService

try:
    import fakeredis
except ImportError:  # pragma: no cover - 依赖缺失时跳过
    fakeredis = None


class FakeChatService:
    def __init__(self) -> None:
        self.last_chat_request = None
        self.last_reset_payload: dict[str, object] | None = None

    def chat_from_user_prompt(self, chat_request):
        self.last_chat_request = chat_request
        return LLMResponse(
            content="ok",
            provider="openai",
            model="gpt-test",
            metadata={"trace_id": "trace-1"},
        )

    def reset_context(self, *, session_id: str, conversation_id: str | None = None):
        self.last_reset_payload = {
            "session_id": session_id,
            "conversation_id": conversation_id,
        }
        return {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "remaining_message_count": 0,
            "scope": "conversation" if conversation_id else "session",
        }


class FakeChatServiceWithCitations(FakeChatService):
    def chat_with_citations_from_user_prompt(self, chat_request):
        self.last_chat_request = chat_request
        return ChatServiceResult(
            llm_response=LLMResponse(
                content="ok-with-citations",
                provider="openai",
                model="gpt-test",
                metadata={"trace_id": "trace-2"},
            ),
            citations=[
                Citation(
                    citation_id="c-1",
                    document_id="doc-1",
                    chunk_id="chk-1",
                    title="Doc One",
                    snippet="Doc snippet",
                    origin_uri="file:///doc-1.md",
                    source_type="markdown_file",
                    updated_at="2026-04-10T00:00:00+00:00",
                    metadata={"score": 0.91},
                )
            ],
            retrieval_trace=RetrievalTrace(
                status="succeeded",
                query_text=chat_request.user_prompt,
                top_k=4,
                hit_count=1,
                citation_count=1,
            ),
        )


class FakeChatServiceDegraded(FakeChatService):
    def chat_with_citations_from_user_prompt(self, chat_request):
        self.last_chat_request = chat_request
        return ChatServiceResult(
            llm_response=LLMResponse(
                content="ok-degraded",
                provider="openai",
                model="gpt-test",
                metadata={"retrieval_status": "degraded"},
            ),
            citations=[],
            retrieval_trace=RetrievalTrace(
                status="degraded",
                query_text=chat_request.user_prompt,
                top_k=4,
                hit_count=0,
                citation_count=0,
                error_type="RuntimeError",
                error_message="retrieval failed",
            ),
        )


class FakeStreamingChatService:
    def stream_chat_from_user_prompt(self, chat_request):
        del chat_request
        yield {
            "event": "response.started",
            "data": {
                "request_id": "req-1",
                "conversation_id": "conv-1",
                "assistant_message_id": "am-1",
                "provider": "openai",
                "model": "gpt-test",
                "created_at": "2026-04-09T00:00:00+00:00",
            },
        }
        yield {
            "event": "response.delta",
            "data": {
                "assistant_message_id": "am-1",
                "delta": "hello",
                "sequence": 1,
            },
        }
        yield {
            "event": "response.completed",
            "data": {
                "assistant_message_id": "am-1",
                "status": "completed",
                "finish_reason": "stop",
                "latency_ms": 12.3,
            },
        }

    def cancel_stream(self, cancel_request):
        return {
            "found": True,
            "cancelled": True,
            "already_cancelled": False,
            "request_id": cancel_request.request_id,
            "assistant_message_id": cancel_request.assistant_message_id,
            "session_id": cancel_request.session_id,
            "conversation_id": cancel_request.conversation_id,
        }


class FakeStreamingChatServiceWithCitations(FakeStreamingChatService):
    def stream_chat_from_user_prompt(self, chat_request):
        del chat_request
        yield {
            "event": "response.started",
            "data": {
                "request_id": "req-1",
                "conversation_id": "conv-1",
                "assistant_message_id": "am-1",
                "provider": "openai",
                "model": "gpt-test",
                "created_at": "2026-04-09T00:00:00+00:00",
            },
        }
        yield {
            "event": "response.delta",
            "data": {
                "assistant_message_id": "am-1",
                "delta": "hello",
                "sequence": 1,
            },
        }
        yield {
            "event": "response.completed",
            "data": {
                "assistant_message_id": "am-1",
                "status": "completed",
                "finish_reason": "stop",
                "latency_ms": 12.3,
                "citations": [
                    {
                        "citation_id": "c-1",
                        "document_id": "doc-1",
                        "chunk_id": "chk-1",
                        "title": "Doc One",
                        "snippet": "Doc snippet",
                        "origin_uri": "file:///doc-1.md",
                        "source_type": "markdown_file",
                        "updated_at": "2026-04-10T00:00:00+00:00",
                        "metadata": {"score": 0.91},
                    }
                ],
            },
        }


class FakeStreamingChatServiceDegraded(FakeStreamingChatService):
    def stream_chat_from_user_prompt(self, chat_request):
        del chat_request
        yield {
            "event": "response.started",
            "data": {
                "request_id": "req-1",
                "conversation_id": "conv-1",
                "assistant_message_id": "am-1",
                "provider": "openai",
                "model": "gpt-test",
                "created_at": "2026-04-09T00:00:00+00:00",
            },
        }
        yield {
            "event": "response.completed",
            "data": {
                "assistant_message_id": "am-1",
                "status": "completed",
                "finish_reason": "stop",
                "latency_ms": 8.2,
                "citations": [],
                "trace": {"retrieval": {"status": "degraded"}},
            },
        }


class FakeOpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def chat(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=f"echo:{request.messages[-1].content}",
            provider=self.provider_name,
            model=request.model,
        )


class APIRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "vi_ai_core_service"},
        )

    def test_chat_delegates_to_service(self) -> None:
        fake_service = FakeChatService()
        with patch("app.api.chat._get_chat_service", return_value=fake_service):
            response = self.client.post(
                "/chat",
                json={
                    "user_prompt": "hello",
                    "provider": "openai",
                    "model": "gpt-test",
                    "temperature": 0.3,
                    "max_tokens": 256,
                    "session_id": "session-1",
                    "conversation_id": "conv-1",
                    "request_id": "req-1",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["content"], "ok")
        self.assertEqual(body["citations"], [])
        self.assertEqual(fake_service.last_chat_request.user_prompt, "hello")
        self.assertEqual(fake_service.last_chat_request.session_id, "session-1")
        self.assertEqual(fake_service.last_chat_request.conversation_id, "conv-1")
        self.assertEqual(fake_service.last_chat_request.temperature, 0.3)
        self.assertEqual(fake_service.last_chat_request.max_tokens, 256)

    def test_chat_returns_citations_when_service_provides_chat_service_result(self) -> None:
        fake_service = FakeChatServiceWithCitations()
        with patch("app.api.chat._get_chat_service", return_value=fake_service):
            response = self.client.post(
                "/chat",
                json={
                    "user_prompt": "hello",
                    "provider": "openai",
                    "model": "gpt-test",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["content"], "ok-with-citations")
        self.assertEqual(len(body["citations"]), 1)
        self.assertEqual(body["citations"][0]["citation_id"], "c-1")

    def test_chat_retrieval_degraded_still_returns_success_with_empty_citations(self) -> None:
        fake_service = FakeChatServiceDegraded()
        with patch("app.api.chat._get_chat_service", return_value=fake_service):
            response = self.client.post(
                "/chat",
                json={
                    "user_prompt": "hello",
                    "provider": "openai",
                    "model": "gpt-test",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["content"], "ok-degraded")
        self.assertEqual(body["citations"], [])

    def test_chat_rejects_invalid_input(self) -> None:
        response = self.client.post("/chat", json={"user_prompt": ""})

        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())

    def test_chat_maps_service_validation_error_to_400(self) -> None:
        class ValidationErrorService:
            def chat_from_user_prompt(self, chat_request):
                del chat_request
                raise ServiceValidationError("invalid request")

        with patch("app.api.chat._get_chat_service", return_value=ValidationErrorService()):
            response = self.client.post("/chat", json={"user_prompt": "hello"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid request", response.json()["detail"])

    def test_chat_maps_service_configuration_error_to_400(self) -> None:
        class ConfigErrorService:
            def chat_from_user_prompt(self, chat_request):
                del chat_request
                raise ServiceConfigurationError("missing provider config")

        with patch("app.api.chat._get_chat_service", return_value=ConfigErrorService()):
            response = self.client.post("/chat", json={"user_prompt": "hello"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("missing provider config", response.json()["detail"])

    def test_chat_maps_service_not_implemented_error_to_501(self) -> None:
        class NotImplementedService:
            def chat_from_user_prompt(self, chat_request):
                del chat_request
                raise ServiceNotImplementedError("stream not ready")

        with patch("app.api.chat._get_chat_service", return_value=NotImplementedService()):
            response = self.client.post("/chat", json={"user_prompt": "hello"})

        self.assertEqual(response.status_code, 501)
        self.assertIn("stream not ready", response.json()["detail"])

    def test_chat_maps_service_dependency_error_to_502(self) -> None:
        class UpstreamErrorService:
            def chat_from_user_prompt(self, chat_request):
                del chat_request
                raise ServiceDependencyError("upstream failure")

        with patch("app.api.chat._get_chat_service", return_value=UpstreamErrorService()):
            response = self.client.post("/chat", json={"user_prompt": "hello"})

        self.assertEqual(response.status_code, 502)
        self.assertIn("upstream failure", response.json()["detail"])

    def test_chat_maps_unexpected_error_to_500_without_internal_detail(self) -> None:
        class UnexpectedErrorService:
            def chat_from_user_prompt(self, chat_request):
                del chat_request
                raise RuntimeError("sensitive internals")

        with patch("app.api.chat._get_chat_service", return_value=UnexpectedErrorService()):
            response = self.client.post("/chat", json={"user_prompt": "hello"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "服务器内部错误。")

    def test_chat_reset_delegates_to_service(self) -> None:
        fake_service = FakeChatService()
        with patch("app.api.chat._get_chat_service", return_value=fake_service):
            response = self.client.post(
                "/chat_reset",
                json={
                    "session_id": "session-1",
                    "conversation_id": "conv-1",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"], "conversation")
        self.assertEqual(
            fake_service.last_reset_payload,
            {"session_id": "session-1", "conversation_id": "conv-1"},
        )

    def test_chat_reset_session_scope_without_conversation_id(self) -> None:
        fake_service = FakeChatService()
        with patch("app.api.chat._get_chat_service", return_value=fake_service):
            response = self.client.post(
                "/chat_reset",
                json={"session_id": "session-1"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"], "session")
        self.assertEqual(
            fake_service.last_reset_payload,
            {"session_id": "session-1", "conversation_id": None},
        )

    def test_chat_stream_returns_sse(self) -> None:
        with patch(
            "app.api.chat._get_streaming_chat_service",
            return_value=FakeStreamingChatService(),
        ):
            response = self.client.post(
                "/chat_stream",
                json={
                    "user_prompt": "hello",
                    "provider": "openai",
                    "model": "gpt-test",
                    "session_id": "session-1",
                    "conversation_id": "conv-1",
                    "request_id": "req-1",
                    "stream": True,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        self.assertIn("event: response.started", response.text)
        self.assertIn("event: response.delta", response.text)
        self.assertIn("event: response.completed", response.text)

    def test_chat_stream_completed_includes_citations_and_delta_does_not(self) -> None:
        with patch(
            "app.api.chat._get_streaming_chat_service",
            return_value=FakeStreamingChatServiceWithCitations(),
        ):
            response = self.client.post(
                "/chat_stream",
                json={
                    "user_prompt": "hello",
                    "provider": "openai",
                    "model": "gpt-test",
                    "session_id": "session-1",
                    "conversation_id": "conv-1",
                    "request_id": "req-1",
                    "stream": True,
                },
            )

        self.assertEqual(response.status_code, 200)
        events = self._parse_sse_events(response.text)
        delta_event = next(event for event in events if event["event"] == "response.delta")
        completed_event = next(event for event in events if event["event"] == "response.completed")
        self.assertNotIn("citations", delta_event["data"])
        self.assertEqual(len(completed_event["data"]["citations"]), 1)
        self.assertEqual(completed_event["data"]["citations"][0]["citation_id"], "c-1")

    def test_chat_stream_retrieval_degraded_still_completes(self) -> None:
        with patch(
            "app.api.chat._get_streaming_chat_service",
            return_value=FakeStreamingChatServiceDegraded(),
        ):
            response = self.client.post(
                "/chat_stream",
                json={
                    "user_prompt": "hello",
                    "provider": "openai",
                    "model": "gpt-test",
                    "session_id": "session-1",
                    "conversation_id": "conv-1",
                    "request_id": "req-1",
                    "stream": True,
                },
            )

        self.assertEqual(response.status_code, 200)
        events = self._parse_sse_events(response.text)
        self.assertIn("response.completed", [event["event"] for event in events])
        self.assertNotIn("response.error", [event["event"] for event in events])
        completed_event = next(event for event in events if event["event"] == "response.completed")
        self.assertEqual(completed_event["data"]["citations"], [])

    def test_chat_cancel_delegates_to_streaming_service(self) -> None:
        with patch(
            "app.api.chat._get_streaming_chat_service",
            return_value=FakeStreamingChatService(),
        ):
            response = self.client.post(
                "/chat_stream_cancel",
                json={
                    "request_id": "req-1",
                    "assistant_message_id": "am-1",
                    "session_id": "session-1",
                    "conversation_id": "conv-1",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["found"])
        self.assertTrue(body["cancelled"])
        self.assertEqual(body["request_id"], "req-1")

    def test_chat_reset_maps_service_validation_error_to_400(self) -> None:
        class ValidationErrorResetService:
            def reset_context(self, *, session_id: str, conversation_id: str | None = None):
                del session_id, conversation_id
                raise ServiceValidationError("session_id required")

        with patch(
            "app.api.chat._get_chat_service",
            return_value=ValidationErrorResetService(),
        ):
            response = self.client.post("/chat_reset", json={"session_id": "session-1"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("session_id required", response.json()["detail"])

    @unittest.skipIf(fakeredis is None, "未安装 fakeredis，跳过 Redis API 测试。")
    def test_chat_and_reset_work_with_redis_backend_service(self) -> None:
        provider_configs = {
            "openai": ProviderConfig(name="openai", api_key="k1", default_model="gpt-test"),
            "deepseek": ProviderConfig(name="deepseek"),
            "gemini": ProviderConfig(name="gemini"),
            "doubao": ProviderConfig(name="doubao"),
            "tongyi": ProviderConfig(name="tongyi"),
        }
        app_config = AppConfig(
            default_provider="openai",
            providers=provider_configs,
        )
        registry = ProviderRegistry(
            config=app_config,
            provider_overrides={"openai": FakeOpenAIProvider(provider_configs["openai"])},
        )
        redis_client = fakeredis.FakeRedis(decode_responses=True)
        context_manager = ContextManager(
            store=RedisContextStore(
                redis_url="redis://localhost:6379/0",
                key_prefix="test:api",
                session_ttl_seconds=120,
                redis_client=redis_client,
            )
        )
        llm_service = LLMService(
            app_config=app_config,
            registry=registry,
            context_manager=context_manager,
        )

        with patch("app.api.chat._get_chat_service", return_value=llm_service):
            chat_response = self.client.post(
                "/chat",
                json={
                    "user_prompt": "hello redis",
                    "provider": "openai",
                    "session_id": "session-redis",
                    "conversation_id": "conv-redis",
                },
            )
            reset_response = self.client.post(
                "/chat_reset",
                json={
                    "session_id": "session-redis",
                    "conversation_id": "conv-redis",
                },
            )

        self.assertEqual(chat_response.status_code, 200)
        self.assertEqual(chat_response.json()["content"], "echo:hello redis")
        self.assertEqual(reset_response.status_code, 200)
        self.assertEqual(reset_response.json()["scope"], "conversation")

    @staticmethod
    def _parse_sse_events(payload: str) -> list[dict[str, object]]:
        events: list[dict[str, object]] = []
        current_event: str | None = None
        current_data: str | None = None
        for raw_line in payload.splitlines():
            line = raw_line.strip()
            if line.startswith("event:"):
                current_event = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                current_data = line.removeprefix("data:").strip()
            elif not line and current_event and current_data:
                import json

                events.append(
                    {
                        "event": current_event,
                        "data": json.loads(current_data),
                    }
                )
                current_event = None
                current_data = None
        if current_event and current_data:
            import json

            events.append(
                {
                    "event": current_event,
                    "data": json.loads(current_data),
                }
            )
        return events
