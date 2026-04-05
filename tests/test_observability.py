from __future__ import annotations

import io
import json
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import AppConfig, ObservabilityConfig, ProviderConfig
from app.observability.context import (
    clear_request_context,
    get_request_context,
    set_request_context,
    update_request_context,
)
from app.observability.events import (
    build_startup_config_summary,
    log_api_request,
    log_provider_request,
    log_provider_response,
    log_startup_config_summary,
)
from app.observability.exception_logging import log_exception
from app.observability.logging_setup import configure_logging, get_logger
from app.observability.middleware import request_logging_middleware


def _parse_log_line(line: str) -> tuple[str, dict[str, object]]:
    prefix, message_part = line.split(" message=", maxsplit=1)
    return prefix, json.loads(message_part)


def _extract_event(prefix: str) -> str:
    return prefix.split(" event=", maxsplit=1)[1]


class ObservabilityContextTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_request_context()

    def test_context_set_update_and_clear(self) -> None:
        set_request_context(request_id="req-1", session_id="session-1")
        update_request_context(conversation_id="conv-1", provider="openai", model="gpt-test")

        context = get_request_context()
        self.assertEqual(context["request_id"], "req-1")
        self.assertEqual(context["session_id"], "session-1")
        self.assertEqual(context["conversation_id"], "conv-1")
        self.assertEqual(context["provider"], "openai")
        self.assertEqual(context["model"], "gpt-test")

        clear_request_context()
        self.assertEqual(get_request_context(), {})


class ObservabilityLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_request_context()
        self.stream = io.StringIO()

    def test_formatter_outputs_prefix_and_business_json(self) -> None:
        configure_logging(
            ObservabilityConfig(
                log_enabled=True,
                log_level="INFO",
                log_format="json",
                log_api_payload=False,
                log_provider_payload=False,
            ),
            stream=self.stream,
        )
        set_request_context(request_id="req-123", provider="openai", model="gpt-test")

        logger = get_logger("tests.json")
        logger.info("hello observability", extra={"event": "test.event"})

        line = self.stream.getvalue().strip().splitlines()[0]
        prefix, payload = _parse_log_line(line)
        self.assertIn("INFO", prefix)
        self.assertIn("[MainThread]", prefix)
        self.assertIn("vi_ai_core_service.tests.json", prefix)
        self.assertIn("test_observability.py", prefix)
        self.assertEqual(_extract_event(prefix), "test.event")
        self.assertEqual(payload["request_id"], "req-123")
        self.assertEqual(payload["provider"], "openai")
        self.assertEqual(payload["model"], "gpt-test")

    def test_log_enabled_false_suppresses_info_but_keeps_error(self) -> None:
        configure_logging(
            ObservabilityConfig(
                log_enabled=False,
                log_level="INFO",
                log_format="json",
                log_api_payload=False,
                log_provider_payload=False,
            ),
            stream=self.stream,
        )

        logger = get_logger("tests.level_filter")
        logger.info("should_not_be_logged", extra={"event": "test.info"})
        logger.error("must_be_logged", extra={"event": "test.error"})

        lines = [line for line in self.stream.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        prefix, payload = _parse_log_line(lines[0])
        self.assertEqual(_extract_event(prefix), "test.error")
        self.assertEqual(payload, {})

    def test_exception_logging_keeps_traceback(self) -> None:
        configure_logging(
            ObservabilityConfig(
                log_enabled=False,
                log_level="INFO",
                log_format="json",
                log_api_payload=False,
                log_provider_payload=False,
            ),
            stream=self.stream,
        )

        try:
            raise RuntimeError("boom")
        except RuntimeError as exc:
            log_exception(
                exc,
                event="test.exception",
                message="Captured exception.",
                logger=get_logger("tests.exception"),
            )

        raw_text = self.stream.getvalue().strip()
        first_line = raw_text.splitlines()[0]
        prefix, payload = _parse_log_line(first_line)
        self.assertEqual(_extract_event(prefix), "test.exception")
        self.assertEqual(payload, {})
        self.assertIn("RuntimeError", raw_text)

    def test_event_helper_uses_caller_file_line(self) -> None:
        configure_logging(ObservabilityConfig(), stream=self.stream)
        set_request_context(request_id="req-caller")

        log_api_request(route="/chat", stream=False)

        line = self.stream.getvalue().strip().splitlines()[0]
        prefix, payload = _parse_log_line(line)
        self.assertIn("test_observability.py", prefix)
        self.assertNotIn("events.py", prefix)
        self.assertEqual(_extract_event(prefix), "api.request")
        self.assertEqual(payload["route"], "/chat")
        self.assertEqual(payload["request_id"], "req-caller")
        self.assertNotIn("method", payload)
        self.assertNotIn("path", payload)

    def test_provider_payload_is_hidden_when_switch_disabled(self) -> None:
        configure_logging(
            ObservabilityConfig(
                log_enabled=True,
                log_level="INFO",
                log_format="json",
                log_api_payload=False,
                log_provider_payload=False,
            ),
            stream=self.stream,
        )

        log_provider_request(
            provider="openai",
            model="gpt-test",
            endpoint="https://api.openai.com",
            stream=False,
            message_count=1,
            has_attachments=False,
            has_tools=False,
            has_response_format=False,
            timeout_seconds=60.0,
            request_payload={"messages": [{"role": "user", "content": "secret"}]},
        )
        log_provider_response(
            provider="openai",
            model="gpt-test",
            finish_reason="stop",
            usage=None,
            latency_ms=12.3,
            success=True,
            response_payload={"content": "secret result"},
        )

        entries = [_parse_log_line(line) for line in self.stream.getvalue().splitlines() if line]
        self.assertEqual(_extract_event(entries[0][0]), "provider.request")
        self.assertEqual(_extract_event(entries[1][0]), "provider.response")
        self.assertNotIn("request_payload", entries[0][1])
        self.assertNotIn("response_payload", entries[1][1])

    def test_provider_payload_is_included_when_switch_enabled(self) -> None:
        configure_logging(
            ObservabilityConfig(
                log_enabled=True,
                log_level="INFO",
                log_format="json",
                log_api_payload=False,
                log_provider_payload=True,
            ),
            stream=self.stream,
        )

        log_provider_request(
            provider="openai",
            model="gpt-test",
            endpoint="https://api.openai.com",
            stream=False,
            message_count=1,
            has_attachments=False,
            has_tools=False,
            has_response_format=False,
            timeout_seconds=60.0,
            request_payload={"messages": [{"role": "user", "content": "visible"}]},
        )
        log_provider_response(
            provider="openai",
            model="gpt-test",
            finish_reason="stop",
            usage=None,
            latency_ms=9.8,
            success=True,
            response_payload={"content": "visible result"},
        )

        entries = [_parse_log_line(line) for line in self.stream.getvalue().splitlines() if line]
        self.assertIn("request_payload", entries[0][1])
        self.assertIn("response_payload", entries[1][1])


class ObservabilityMiddlewareTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_request_context()
        self.stream = io.StringIO()
        configure_logging(
            ObservabilityConfig(
                log_enabled=True,
                log_level="INFO",
                log_format="json",
                log_api_payload=False,
                log_provider_payload=False,
            ),
            stream=self.stream,
        )

    def test_request_logging_middleware_adds_request_id_and_logs(self) -> None:
        app = FastAPI()
        app.middleware("http")(request_logging_middleware)

        @app.get("/demo")
        def demo() -> dict[str, bool]:
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/demo")

        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response.headers)
        self.assertEqual(get_request_context(), {})

        entries = [_parse_log_line(line) for line in self.stream.getvalue().splitlines() if line]
        events = [_extract_event(prefix) for prefix, _ in entries]
        self.assertIn("api.http.request", events)
        self.assertIn("api.http.response", events)
        for _, payload in entries:
            self.assertNotIn("method", payload)
            self.assertNotIn("path", payload)


class StartupSummaryTests(unittest.TestCase):
    def test_startup_summary_masks_sensitive_values(self) -> None:
        config = AppConfig(
            default_provider="openai",
            timeout_seconds=60.0,
            providers={
                "openai": ProviderConfig(
                    name="openai",
                    api_key="secret-key",
                    default_model="gpt-test",
                ),
                "deepseek": ProviderConfig(
                    name="deepseek",
                    api_key=None,
                    base_url="https://api.deepseek.com",
                    default_model="deepseek-chat",
                ),
            },
            observability=ObservabilityConfig(
                log_enabled=True,
                log_level="INFO",
                log_format="json",
                log_api_payload=False,
                log_provider_payload=False,
            ),
        )

        summary = build_startup_config_summary(config)
        serialized = json.dumps(summary)
        self.assertNotIn("secret-key", serialized)
        self.assertTrue(summary["providers"]["openai"]["has_api_key"])
        self.assertFalse(summary["providers"]["deepseek"]["has_api_key"])

    def test_startup_summary_log_event(self) -> None:
        stream = io.StringIO()
        configure_logging(ObservabilityConfig(), stream=stream)

        config = AppConfig(
            default_provider="openai",
            timeout_seconds=60.0,
            providers={"openai": ProviderConfig(name="openai")},
            observability=ObservabilityConfig(),
        )
        log_startup_config_summary(config)

        line = stream.getvalue().strip().splitlines()[0]
        prefix, payload = _parse_log_line(line)
        self.assertEqual(_extract_event(prefix), "startup.config_summary")
        self.assertIn("providers", payload)
