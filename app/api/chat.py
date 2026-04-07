"""Minimal chat API skeleton."""

from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter

from app.api.deps import get_chat_service
from app.api.error_mapping import build_chat_http_exception
from app.api.schemas.chat import ChatRequest, ChatResponse
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
