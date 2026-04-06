"""Minimal chat API skeleton."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import get_chat_service
from app.api.error_mapping import build_chat_http_exception
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.observability.context import update_request_context
from app.observability.events import log_api_request, log_api_response

router = APIRouter(tags=["chat"])
# Backward-compatible alias used by existing API tests.
_get_chat_service = get_chat_service


@router.post("/chat", response_model=ChatResponse)
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
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system,
            stream=request.stream,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            request_id=request.request_id,
            metadata=request.metadata,
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise build_chat_http_exception(
            exc,
            request=request,
            started_at=started_at,
        ) from exc

    log_api_response(
        route="/chat",
        status_code=200,
        latency_ms=(perf_counter() - started_at) * 1000,
        stream=request.stream,
        provider=response.provider,
        model=response.model,
        response_content=response.content,
    )
    return response.to_dict()
