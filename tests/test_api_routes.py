from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import AppConfig, ProviderConfig
from app.context.manager import ContextManager
from app.context.stores.redis_store import RedisContextStore
from app.providers.base import BaseLLMProvider
from app.providers.registry import ProviderRegistry
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse
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
        self.assertEqual(fake_service.last_chat_request.user_prompt, "hello")
        self.assertEqual(fake_service.last_chat_request.session_id, "session-1")
        self.assertEqual(fake_service.last_chat_request.conversation_id, "conv-1")
        self.assertEqual(fake_service.last_chat_request.temperature, 0.3)
        self.assertEqual(fake_service.last_chat_request.max_tokens, 256)

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
                "/chat/reset",
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
                "/chat/reset",
                json={"session_id": "session-1"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"], "session")
        self.assertEqual(
            fake_service.last_reset_payload,
            {"session_id": "session-1", "conversation_id": None},
        )

    def test_chat_reset_maps_service_validation_error_to_400(self) -> None:
        class ValidationErrorResetService:
            def reset_context(self, *, session_id: str, conversation_id: str | None = None):
                del session_id, conversation_id
                raise ServiceValidationError("session_id required")

        with patch(
            "app.api.chat._get_chat_service",
            return_value=ValidationErrorResetService(),
        ):
            response = self.client.post("/chat/reset", json={"session_id": "session-1"})

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
                "/chat/reset",
                json={
                    "session_id": "session-redis",
                    "conversation_id": "conv-redis",
                },
            )

        self.assertEqual(chat_response.status_code, 200)
        self.assertEqual(chat_response.json()["content"], "echo:hello redis")
        self.assertEqual(reset_response.status_code, 200)
        self.assertEqual(reset_response.json()["scope"], "conversation")
