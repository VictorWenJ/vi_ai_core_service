"""Minimal chat API skeleton."""

from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter

from app.api.deps import get_chat_service
from app.api.error_mapping import build_chat_http_exception, build_service_http_exception
from app.api.schemas.chat import (
    ChatRequest,
    ChatResetRequest,
    ChatResetResponse,
    ChatResponse,
)
from app.observability.log_until import log_report
from app.schemas import LLMResponse

router = APIRouter(tags=["chat"])
# Backward-compatible alias used by existing API tests.
_get_chat_service = get_chat_service


@router.post("/chat", response_model=ChatResponse)
def chat(chat_request: ChatRequest) -> LLMResponse:
    started_at = perf_counter()
    llm_service = _get_chat_service()

    log_report("Chat.chat.chat_request", chat_request)

    try:
        chat_response = llm_service.chat_from_user_prompt(chat_request)
    except Exception as exc:
        raise build_chat_http_exception(
            exc,
            request=chat_request,
            started_at=started_at,
        ) from exc

    log_report("Chat.chat.chat_response", chat_response)
    log_report("Chat.chat.latency_ms", dict(latency_ms=(perf_counter() - started_at) * 1000))

    return chat_response


@router.post("/chat/reset", response_model=ChatResetResponse)
def reset_chat_context(reset_request: ChatResetRequest) -> ChatResetResponse:
    started_at = perf_counter()
    llm_service = _get_chat_service()

    log_report("Chat.reset.request", reset_request)

    try:
        result = llm_service.reset_context(
            session_id=reset_request.session_id,
            conversation_id=reset_request.conversation_id,
        )
    except Exception as exc:
        raise build_service_http_exception(
            exc,
            started_at=started_at,
            event_prefix="api.chat.reset",
            context_payload={
                "session_id": reset_request.session_id,
                "conversation_id": reset_request.conversation_id,
            },
        ) from exc

    log_report("Chat.reset.response", result)
    return ChatResetResponse(
        session_id=result["session_id"],
        conversation_id=result["conversation_id"],
        remaining_message_count=result["remaining_message_count"],
        scope=result["scope"],
    )
