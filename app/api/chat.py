"""Minimal chat API skeleton."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import AppConfig
from app.schemas.llm_request import LLMRequest
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, description="Single-turn user prompt.")
    provider: str | None = Field(default=None, description="Optional provider override.")
    model: str | None = Field(default=None, description="Optional model override.")
    system: str | None = Field(default=None, description="Optional system prompt.")


@lru_cache(maxsize=1)
def _get_chat_service() -> LLMService:
    config = AppConfig.from_env()
    prompt_service = PromptService()
    return LLMService(config=config, prompt_service=prompt_service)


@router.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    llm_service = _get_chat_service()
    prompt_service = PromptService()

    try:
        messages = prompt_service.build_messages(
            system_prompt=request.system,
            user_prompt=request.prompt,
        )
        llm_request = LLMRequest(
            provider=request.provider,
            model=request.model,
            messages=messages,
        )
        response = llm_service.chat(llm_request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return response.to_dict()
