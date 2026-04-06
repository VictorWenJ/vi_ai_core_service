"""HTTP error mapping helpers for chat route."""

from __future__ import annotations

from time import perf_counter

from fastapi import HTTPException

from app.api.schemas.chat import ChatRequest
from app.observability.events import log_api_response
from app.observability.exception_logging import log_exception
from app.observability.logging_setup import get_logger
from app.services.errors import (
    ServiceConfigurationError,
    ServiceDependencyError,
    ServiceNotImplementedError,
    ServiceValidationError,
)

_api_logger = get_logger("api.chat")


def build_chat_http_exception(
    exc: Exception,
    *,
    request: ChatRequest,
    started_at: float,
) -> HTTPException:
    status_code = _resolve_status_code(exc)
    log_api_response(
        route="/chat",
        status_code=status_code,
        latency_ms=(perf_counter() - started_at) * 1000,
        stream=request.stream,
        provider=request.provider,
        model=request.model,
    )

    if status_code == 500:
        log_exception(
            exc,
            event="api.chat.error",
            message="Unhandled exception in /chat handler.",
            logger=_api_logger,
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

