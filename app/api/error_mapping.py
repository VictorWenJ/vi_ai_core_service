"""HTTP error mapping helpers for chat route."""

from __future__ import annotations

from time import perf_counter
import traceback

from fastapi import HTTPException

from app.api.schemas.chat import ChatRequest
from app.observability.log_until import log_report
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceNotImplementedError,
    ServiceValidationError,
)


def build_chat_http_exception(
    exc: Exception,
    *,
    request: ChatRequest,
    started_at: float,
) -> HTTPException:
    status_code = _resolve_status_code(exc)
    latency_ms = round((perf_counter() - started_at) * 1000, 2)
    log_report(
        "api.chat.error_response",
        {
            "status_code": status_code,
            "latency_ms": latency_ms,
            "stream": request.stream,
            "provider": request.provider,
            "model": request.model,
            "error_type": type(exc).__name__,
        },
    )

    if status_code == 500:
        log_report(
            "api.chat.error",
            {
                "status_code": 500,
                "latency_ms": latency_ms,
                "stream": request.stream,
                "provider": request.provider,
                "model": request.model,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": "".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__)
                ),
            },
        )
        return HTTPException(status_code=500, detail="Internal server error.")

    return HTTPException(status_code=status_code, detail=str(exc))


def _resolve_status_code(exc: Exception) -> int:
    if isinstance(exc, (ServiceValidationError, ValueError, ServiceConfigurationError)):
        return 400
    if isinstance(exc, ServiceNotImplementedError):
        return 501
    if isinstance(exc, ServiceDependencyError):
        return 502
    return 500
