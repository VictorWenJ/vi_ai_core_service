from __future__ import annotations

import unittest

from app.context.models import ContextMessage
from app.context.manager import ContextManager


class ContextManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = ContextManager()

    def test_get_context_returns_empty_window_when_missing(self) -> None:
        window = self.manager.get_context("session-1")

        self.assertEqual(window.session_id, "session-1")
        self.assertEqual(window.messages, [])

    def test_append_user_and_assistant_messages(self) -> None:
        self.manager.append_user_message("session-1", "hello")
        self.manager.append_assistant_message("session-1", "hi")

        window = self.manager.get_context("session-1")
        self.assertEqual([message.role for message in window.messages], ["user", "assistant"])
        self.assertEqual([message.content for message in window.messages], ["hello", "hi"])

    def test_clear_context_resets_window_messages(self) -> None:
        self.manager.append_user_message("session-1", "hello")
        cleared_window = self.manager.clear_context("session-1")

        self.assertEqual(cleared_window.session_id, "session-1")
        self.assertEqual(cleared_window.messages, [])

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
