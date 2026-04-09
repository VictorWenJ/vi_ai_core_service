"""API 路由依赖装配辅助。"""

from __future__ import annotations

from functools import lru_cache

from app.config import AppConfig
from app.context.manager import ContextManager
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService


@lru_cache(maxsize=1)
def get_chat_service() -> LLMService:
    app_config = AppConfig.from_env()
    prompt_service = PromptService()
    context_manager = ContextManager.from_app_config(app_config)
    return LLMService(
        app_config=app_config,
        prompt_service=prompt_service,
        context_manager=context_manager,
    )
