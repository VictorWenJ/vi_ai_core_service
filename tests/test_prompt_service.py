from __future__ import annotations

import unittest

from app.schemas.llm_request import LLMMessage
from app.services.prompt_service import PromptService


class PromptServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prompt_service = PromptService()

    def test_build_messages_with_system_and_user_prompt(self) -> None:
        messages = self.prompt_service.build_messages(
            system_prompt="You are helpful.",
            user_prompt="Hello",
        )

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[0].content, "You are helpful.")
        self.assertEqual(messages[1].role, "user")
        self.assertEqual(messages[1].content, "Hello")

    def test_build_messages_preserves_existing_messages(self) -> None:
        messages = self.prompt_service.build_messages(
            system_prompt="System rule",
            messages=[LLMMessage(role="user", content="Ping")],
        )

        self.assertEqual([message.role for message in messages], ["system", "user"])

    def test_build_messages_requires_input(self) -> None:
        with self.assertRaises(ValueError):
            self.prompt_service.build_messages()
