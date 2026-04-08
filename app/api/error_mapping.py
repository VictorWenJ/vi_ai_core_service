"""聊天路由的 HTTP 错误映射辅助。"""

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
    return build_service_http_exception(
        exc,
        started_at=started_at,
        event_prefix="api.chat",
        context_payload={
            "stream": request.stream,
            "provider": request.provider,
            "model": request.model,
        },
    )


def build_service_http_exception(
    exc: Exception,
    *,
    started_at: float,
    event_prefix: str,
    context_payload: dict[str, object] | None = None,
) -> HTTPException:
    status_code = _resolve_status_code(exc)
    latency_ms = round((perf_counter() - started_at) * 1000, 2)
    payload = {
        "status_code": status_code,
        "latency_ms": latency_ms,
        "error_type": type(exc).__name__,
    }
    if context_payload:
        payload.update(context_payload)

    log_report(f"{event_prefix}.error_response", payload)

    if status_code == 500:
        error_payload = dict(payload)
        error_payload["error_message"] = str(exc)
        error_payload["traceback"] = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        log_report(f"{event_prefix}.error", error_payload)
        return HTTPException(status_code=500, detail="服务器内部错误。")

    return HTTPException(status_code=status_code, detail=str(exc))


def _resolve_status_code(exc: Exception) -> int:
    if isinstance(exc, (ServiceValidationError, ValueError, ServiceConfigurationError)):
        return 400
    if isinstance(exc, ServiceNotImplementedError):
        return 501
    if isinstance(exc, ServiceDependencyError):
        return 502
    return 500
