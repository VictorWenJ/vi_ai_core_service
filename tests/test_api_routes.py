from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.schemas.llm_response import LLMResponse
from app.server import app
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceNotImplementedError,
    ServiceValidationError,
)


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
        self.assertEqual(response.json()["detail"], "Internal server error.")

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

