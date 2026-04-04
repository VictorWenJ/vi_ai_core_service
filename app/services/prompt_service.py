"""Minimal prompt assembly helpers."""

from __future__ import annotations

from app.prompts.renderer import render_prompt
from app.schemas.llm_request import LLMMessage

DEFAULT_CHAT_SYSTEM_TEMPLATE_ID = "chat.default_system"


class PromptService:
    """Phase 1 prompt helper: only message assembly, nothing more."""

    def get_default_system_prompt(self) -> str:
        return render_prompt(DEFAULT_CHAT_SYSTEM_TEMPLATE_ID).strip()

    def build_messages(
        self,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        messages: list[LLMMessage] | None = None,
    ) -> list[LLMMessage]:
        assembled_messages = list(messages or [])

        if system_prompt:
            assembled_messages.insert(0, LLMMessage(role="system", content=system_prompt))

        if user_prompt:
            assembled_messages.append(LLMMessage(role="user", content=user_prompt))

        if not assembled_messages:
            raise ValueError("At least one message or user_prompt is required.")

        return assembled_messages

    def build_chat_messages(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        messages: list[LLMMessage] | None = None,
    ) -> list[LLMMessage]:
        resolved_system_prompt = system_prompt
        if resolved_system_prompt is None:
            resolved_system_prompt = self.get_default_system_prompt()

        return self.build_messages(
            system_prompt=resolved_system_prompt,
            user_prompt=user_prompt,
            messages=messages,
        )
