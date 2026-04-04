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
from app.observability.events import build_startup_config_summary, log_startup_config_summary
from app.observability.exception_logging import log_exception
from app.observability.logging_setup import configure_logging, get_logger
from app.observability.middleware import request_logging_middleware


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

    def test_json_log_formatter_outputs_required_fields(self) -> None:
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

        payload = json.loads(self.stream.getvalue().strip().splitlines()[0])
        self.assertEqual(payload["event"], "test.event")
        self.assertEqual(payload["message"], "hello observability")
        self.assertEqual(payload["request_id"], "req-123")
        self.assertEqual(payload["provider"], "openai")
        self.assertEqual(payload["model"], "gpt-test")
        self.assertEqual(payload["level"], "info")
        self.assertIn("timestamp", payload)
        self.assertIn("logger", payload)

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
        payload = json.loads(lines[0])
        self.assertEqual(payload["event"], "test.error")
        self.assertEqual(payload["level"], "error")

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

        payload = json.loads(self.stream.getvalue().strip().splitlines()[0])
        self.assertEqual(payload["event"], "test.exception")
        self.assertEqual(payload["level"], "error")
        self.assertIn("exception", payload)
        self.assertIn("RuntimeError", payload["exception"])


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

        events = [
            json.loads(line)["event"]
            for line in self.stream.getvalue().splitlines()
            if line.strip()
        ]
        self.assertIn("api.http.request", events)
        self.assertIn("api.http.response", events)


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

        payload = json.loads(stream.getvalue().strip().splitlines()[0])
        self.assertEqual(payload["event"], "startup.config_summary")
