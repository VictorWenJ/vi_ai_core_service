"""Minimal chat API skeleton."""

from __future__ import annotations

from functools import lru_cache
from time import perf_counter
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import AppConfig
from app.observability.context import update_request_context
from app.observability.events import log_api_request, log_api_response
from app.observability.exception_logging import log_exception
from app.observability.logging_setup import get_logger
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceNotImplementedError,
    ServiceValidationError,
)
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService

router = APIRouter(tags=["chat"])
_api_logger = get_logger("api.chat")


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
    started_at = perf_counter()
    llm_service = _get_chat_service()

    update_request_context(
        request_id=request.request_id,
        session_id=request.session_id,
        conversation_id=request.conversation_id,
        provider=request.provider,
        model=request.model,
    )
    log_api_request(
        route="/chat",
        method="POST",
        stream=request.stream,
        provider=request.provider,
        model=request.model,
        session_id=request.session_id,
        conversation_id=request.conversation_id,
        request_id=request.request_id,
        prompt=request.prompt,
        metadata=request.metadata,
    )

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
        _log_error_response(status_code=400, request=request, started_at=started_at)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServiceConfigurationError as exc:
        _log_error_response(status_code=400, request=request, started_at=started_at)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServiceNotImplementedError as exc:
        _log_error_response(status_code=501, request=request, started_at=started_at)
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ServiceDependencyError as exc:
        _log_error_response(status_code=502, request=request, started_at=started_at)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_error_response(status_code=500, request=request, started_at=started_at)
        log_exception(
            exc,
            event="api.chat.error",
            message="Unhandled exception in /chat handler.",
            logger=_api_logger,
        )
        raise HTTPException(status_code=500, detail="Internal server error.") from exc

    log_api_response(
        route="/chat",
        method="POST",
        status_code=200,
        latency_ms=(perf_counter() - started_at) * 1000,
        stream=request.stream,
        provider=response.provider,
        model=response.model,
        response_content=response.content,
    )
    return response.to_dict()


def _log_error_response(*, status_code: int, request: ChatRequest, started_at: float) -> None:
    log_api_response(
        route="/chat",
        method="POST",
        status_code=status_code,
        latency_ms=(perf_counter() - started_at) * 1000,
        stream=request.stream,
        provider=request.provider,
        model=request.model,
    )
