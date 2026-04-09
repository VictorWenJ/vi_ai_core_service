"""最小化聊天 API 路由。"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import get_chat_service, get_streaming_chat_service
from app.api.error_mapping import build_chat_http_exception, build_service_http_exception
from app.api.schemas.chat import (
    ChatCancelRequest,
    ChatCancelResponse,
    ChatRequest,
    ChatResetRequest,
    ChatResetResponse,
    ChatResponse,
    ChatStreamRequest,
)
from app.api.sse import format_sse_event
from app.observability.log_until import log_report
from app.schemas import LLMResponse

router = APIRouter(tags=["chat"])
# 供现有 API 测试使用的向后兼容别名。
_get_chat_service = get_chat_service
_get_streaming_chat_service = get_streaming_chat_service


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
    log_report("Chat.chat.latency_ms", {"latency_ms": (perf_counter() - started_at) * 1000})

    return chat_response


@router.post("/chat_stream")
def stream_chat(chat_stream_request: ChatStreamRequest) -> StreamingResponse:
    started_at = perf_counter()
    streaming_service = _get_streaming_chat_service()

    log_report("Chat.stream_chat.chat_stream_request", chat_stream_request)

    def event_generator():
        try:
            chat_stream_response = streaming_service.stream_chat_from_user_prompt(chat_stream_request)
            for event in chat_stream_response:
                yield format_sse_event(event=event["event"], data=_remove_none_fields(event["data"]))
        except Exception as exc:
            http_exception = build_chat_http_exception(
                exc,
                request=ChatRequest(**chat_stream_request.model_dump(exclude={"stream_options"})),
                started_at=started_at,
            )
            yield format_sse_event(
                event="response.error",
                data={
                    "request_id": chat_stream_request.request_id,
                    "status": "failed",
                    "error_code": type(exc).__name__,
                    "message": str(http_exception.detail),
                },
            )

    return StreamingResponse(
        event_generator(),
        # 声明响应类型是 SSE
        media_type="text/event-stream",
        # Cache-Control: no-cache：不要缓存这条流，保证拿到实时事件。
        # Connection: keep-alive：保持连接不断开，服务端可以持续推送 delta/heartbeat/completed 事件。
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/chat_stream_cancel", response_model=ChatCancelResponse)
def cancel_chat_stream(cancel_request: ChatCancelRequest) -> ChatCancelResponse:
    started_at = perf_counter()
    streaming_service = _get_streaming_chat_service()

    log_report("Chat.cancel.request", cancel_request)

    try:
        result = streaming_service.cancel_stream(cancel_request)
    except Exception as exc:
        raise build_service_http_exception(
            exc,
            started_at=started_at,
            event_prefix="api.chat.cancel",
            context_payload={
                "request_id": cancel_request.request_id,
                "assistant_message_id": cancel_request.assistant_message_id,
                "session_id": cancel_request.session_id,
                "conversation_id": cancel_request.conversation_id,
            },
        ) from exc

    log_report("Chat.cancel.response", result)
    return ChatCancelResponse(**result)


@router.post("/chat_reset", response_model=ChatResetResponse)
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


def _remove_none_fields(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}
