from __future__ import annotations

import io
import json
import unittest

from app.context.models import ContextMessage
from app.context.manager import ContextManager
from app.config import ObservabilityConfig
from app.observability.context import clear_request_context
from app.observability.logging_setup import configure_logging


class ContextManagerTests(unittest.TestCase):
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
        self.manager = ContextManager()

    def tearDown(self) -> None:
        clear_request_context()

    def test_get_context_returns_empty_window_when_missing(self) -> None:
        window = self.manager.get_context("session-1")

        self.assertEqual(window.session_id, "session-1")
        self.assertEqual(window.messages, [])
        prefix, payload = self._parse_first_log_line()
        self.assertEqual(self._extract_event(prefix), "context.window.get")
        self.assertEqual(payload["session_id"], "session-1")
        self.assertFalse(payload["window_exists"])
        self.assertEqual(payload["message_count"], 0)
        self.assertEqual(payload["messages"], [])

    def test_append_user_and_assistant_messages(self) -> None:
        self.manager.append_user_message("session-1", "hello")
        self.manager.append_assistant_message("session-1", "hi")

        window = self.manager.get_context("session-1")
        self.assertEqual([message.role for message in window.messages], ["user", "assistant"])
        self.assertEqual([message.content for message in window.messages], ["hello", "hi"])

        entries = [
            self._parse_log_line(line)
            for line in self.stream.getvalue().splitlines()
            if line.strip()
        ]
        events = [self._extract_event(prefix) for prefix, _ in entries]
        self.assertEqual(events, ["context.window.append", "context.window.append", "context.window.get"])

        first_append_payload = entries[0][1]
        second_append_payload = entries[1][1]
        self.assertEqual(first_append_payload["appended_role"], "user")
        self.assertEqual(first_append_payload["appended_content"], "hello")
        self.assertEqual(first_append_payload["message_count"], 1)
        self.assertEqual(second_append_payload["appended_role"], "assistant")
        self.assertEqual(second_append_payload["appended_content"], "hi")
        self.assertEqual(second_append_payload["message_count"], 2)

    def test_clear_context_resets_window_messages(self) -> None:
        self.manager.append_user_message("session-1", "hello")
        cleared_window = self.manager.clear_context("session-1")

        self.assertEqual(cleared_window.session_id, "session-1")
        self.assertEqual(cleared_window.messages, [])

        entries = [
            self._parse_log_line(line)
            for line in self.stream.getvalue().splitlines()
            if line.strip()
        ]
        last_prefix, last_payload = entries[-1]
        self.assertEqual(self._extract_event(last_prefix), "context.window.clear")
        self.assertEqual(last_payload["session_id"], "session-1")
        self.assertEqual(last_payload["message_count"], 0)

    def test_replace_context_messages_overwrites_existing_messages(self) -> None:
        self.manager.append_user_message("session-1", "stale")
        replaced = self.manager.replace_context_messages(
            "session-1",
            [
                ContextMessage(role="user", content="new-user"),
                ContextMessage(role="assistant", content="new-assistant"),
            ],
        )

        self.assertEqual([message.content for message in replaced.messages], ["new-user", "new-assistant"])
        window = self.manager.get_context("session-1")
        self.assertEqual([message.content for message in window.messages], ["new-user", "new-assistant"])

    def _parse_first_log_line(self) -> tuple[str, dict[str, object]]:
        first_line = next(line for line in self.stream.getvalue().splitlines() if line.strip())
        return self._parse_log_line(first_line)

    @staticmethod
    def _parse_log_line(line: str) -> tuple[str, dict[str, object]]:
        prefix, message_part = line.split(" message=", maxsplit=1)
        return prefix, json.loads(message_part)

    @staticmethod
    def _extract_event(prefix: str) -> str:
        return prefix.split(" event=", maxsplit=1)[1]
