from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.providers.base import ProviderInvocationError, StreamNotImplementedError
from app.schemas.llm_response import LLMResponse
from app.server import app


class FakeChatService:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, object] | None = None

    def chat_from_user_prompt(self, **kwargs):
        self.last_kwargs = kwargs
        return LLMResponse(
            content="ok",
            provider="openai",
            model="gpt-test",
            metadata={"trace_id": "trace-1"},
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
                    "prompt": "hello",
                    "provider": "openai",
                    "model": "gpt-test",
                    "session_id": "session-1",
                    "conversation_id": "conv-1",
                    "request_id": "req-1",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "ok")
        self.assertEqual(fake_service.last_kwargs["user_prompt"], "hello")
        self.assertEqual(fake_service.last_kwargs["session_id"], "session-1")
        self.assertEqual(fake_service.last_kwargs["conversation_id"], "conv-1")

    def test_chat_maps_stream_not_supported_to_501(self) -> None:
        class StreamErrorService:
            def chat_from_user_prompt(self, **kwargs):
                raise StreamNotImplementedError("stream not ready")

        with patch("app.api.chat._get_chat_service", return_value=StreamErrorService()):
            response = self.client.post(
                "/chat",
                json={"prompt": "hello", "stream": True},
            )

        self.assertEqual(response.status_code, 501)
        self.assertIn("stream not ready", response.json()["detail"])

    def test_chat_maps_provider_invocation_error_to_502(self) -> None:
        class ProviderErrorService:
            def chat_from_user_prompt(self, **kwargs):
                raise ProviderInvocationError("upstream failure")

        with patch("app.api.chat._get_chat_service", return_value=ProviderErrorService()):
            response = self.client.post("/chat", json={"prompt": "hello"})

        self.assertEqual(response.status_code, 502)
        self.assertIn("upstream failure", response.json()["detail"])
