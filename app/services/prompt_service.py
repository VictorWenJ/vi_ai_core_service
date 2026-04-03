"""Minimal prompt assembly helpers."""

from __future__ import annotations

from app.schemas.llm_request import LLMMessage


class PromptService:
    """Phase 1 prompt helper: only message assembly, nothing more."""

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
