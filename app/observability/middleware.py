"""FastAPI request logging middleware."""

from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

from app.observability.context import clear_request_context, set_request_context
from app.observability.exception_logging import log_exception
from app.observability.logging_setup import get_logger

_REQUEST_ID_HEADER = "X-Request-ID"
_SESSION_ID_HEADER = "X-Session-ID"
_CONVERSATION_ID_HEADER = "X-Conversation-ID"
_middleware_logger = get_logger("api.middleware")


async def request_logging_middleware(request: Request, call_next) -> Response:
    """Attach request_id context and emit lightweight API boundary logs."""

    request_id = _normalize_header_value(request.headers.get(_REQUEST_ID_HEADER)) or str(uuid4())
    session_id = _normalize_header_value(request.headers.get(_SESSION_ID_HEADER))
    conversation_id = _normalize_header_value(request.headers.get(_CONVERSATION_ID_HEADER))

    set_request_context(
        request_id=request_id,
        session_id=session_id,
        conversation_id=conversation_id,
    )
    request.state.request_id = request_id

    path = request.url.path
    started_at = perf_counter()
    should_log_health = path != "/health"

    if should_log_health:
        _middleware_logger.info(
            "HTTP request started.",
            extra={
                "event": "api.http.request",
                "route": path,
                "request_id": request_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
            },
        )

    try:
        response = await call_next(request)
    except Exception as exc:
        latency_ms = (perf_counter() - started_at) * 1000
        log_exception(
            exc,
            event="api.middleware.error",
            message="Unhandled exception while processing HTTP request.",
            logger=_middleware_logger,
            route=path,
            latency_ms=round(latency_ms, 2),
            request_id=request_id,
        )
        clear_request_context()
        raise

    response.headers.setdefault(_REQUEST_ID_HEADER, request_id)
    latency_ms = (perf_counter() - started_at) * 1000
    if should_log_health:
        _middleware_logger.info(
            "HTTP request completed.",
            extra={
                "event": "api.http.response",
                "route": path,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "success": response.status_code < 400,
                "request_id": request_id,
            },
        )

    clear_request_context()
    return response


def _normalize_header_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
