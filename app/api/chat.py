"""Minimal chat API skeleton."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import AppConfig
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceNotImplementedError,
    ServiceValidationError,
)
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, description="Single-turn user prompt.")
    provider: str | None = Field(default=None, description="Optional provider override.")
    model: str | None = Field(default=None, description="Optional model override.")
    system: str | None = Field(default=None, description="Optional system prompt.")
    stream: bool = Field(default=False, description="Streaming response toggle (reserved).")
    session_id: str | None = Field(default=None, description="Optional stateful session id.")
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation id for cross-request continuity.",
    )
    request_id: str | None = Field(default=None, description="Optional external request id.")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional metadata.")


@lru_cache(maxsize=1)
def _get_chat_service() -> LLMService:
    config = AppConfig.from_env()
    prompt_service = PromptService()
    return LLMService(config=config, prompt_service=prompt_service)


@router.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    llm_service = _get_chat_service()

    try:
        response = llm_service.chat_from_user_prompt(
            user_prompt=request.prompt,
            provider=request.provider,
            model=request.model,
            system_prompt=request.system,
            stream=request.stream,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            request_id=request.request_id,
            metadata=request.metadata,
        )
    except (ServiceValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServiceConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServiceNotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ServiceDependencyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=500, detail="Internal server error.") from exc

    return response.to_dict()
