"""Dependency wiring helpers for API routes."""

from __future__ import annotations

from functools import lru_cache

from app.config import AppConfig
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService


@lru_cache(maxsize=1)
def get_chat_service() -> LLMService:
    config = AppConfig.from_env()
    prompt_service = PromptService()
    return LLMService(config=config, prompt_service=prompt_service)

