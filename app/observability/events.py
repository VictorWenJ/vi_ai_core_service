"""Reusable observability event emitters."""

from __future__ import annotations

from typing import Any

from app.config import AppConfig
from app.observability.logging_setup import get_logger, get_logging_settings


def build_startup_config_summary(config: AppConfig) -> dict[str, Any]:
    provider_summary: dict[str, dict[str, Any]] = {}
    for provider_name in sorted(config.providers.keys()):
        provider_config = config.providers[provider_name]
        provider_summary[provider_name] = {
            "has_api_key": bool(provider_config.api_key),
            "default_model": provider_config.default_model,
            "base_url": provider_config.base_url,
        }

    return {
        "default_provider": config.default_provider,
        "timeout_seconds": config.timeout_seconds,
        "observability": {
            "log_enabled": config.observability.log_enabled,
            "log_level": config.observability.log_level,
            "log_format": config.observability.log_format,
            "log_api_payload": config.observability.log_api_payload,
            "log_provider_payload": config.observability.log_provider_payload,
        },
        "providers": provider_summary,
    }


def log_startup_config_summary(config: AppConfig) -> None:
    logger = get_logger("startup")
    logger.info(
        "Startup configuration loaded.",
        extra={
            "event": "startup.config_summary",
            "metadata": build_startup_config_summary(config),
        },
        stacklevel=2,
    )


def log_api_request(
    *,
    route: str,
    stream: bool | None = None,
    provider: str | None = None,
    model: str | None = None,
    session_id: str | None = None,
    conversation_id: str | None = None,
    request_id: str | None = None,
    prompt: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    details: dict[str, Any] = {"route": route}
    if metadata:
        details["request_metadata"] = metadata

    settings = get_logging_settings()
    if settings.log_api_payload and prompt:
        details["prompt_preview"] = _truncate(prompt, 200)
        details["prompt_length"] = len(prompt)

    logger = get_logger("api")
    logger.info(
        "API request received.",
        extra={
            "event": "api.request",
            "stream": stream,
            "provider": provider,
            "model": model,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "request_id": request_id,
            "metadata": details,
        },
        stacklevel=2,
    )


def log_api_response(
    *,
    route: str,
    status_code: int,
    latency_ms: float,
    stream: bool | None = None,
    provider: str | None = None,
    model: str | None = None,
    response_content: str | None = None,
) -> None:
    details: dict[str, Any] = {"route": route}
    settings = get_logging_settings()
    if settings.log_api_payload and response_content:
        details["response_preview"] = _truncate(response_content, 200)
        details["response_length"] = len(response_content)

    logger = get_logger("api")
    logger.info(
        "API response sent.",
        extra={
            "event": "api.response",
            "status_code": status_code,
            "latency_ms": round(latency_ms, 2),
            "stream": stream,
            "provider": provider,
            "model": model,
            "success": status_code < 400,
            "metadata": details,
        },
        stacklevel=2,
    )


def log_service_request(
    *,
    provider: str | None,
    model: str | None,
    stream: bool,
    message_count: int,
    used_context_history: Any,
) -> None:
    logger = get_logger("services")
    logger.info(
        "Service request normalized.",
        extra={
            "event": "service.request",
            "provider": provider,
            "model": model,
            "stream": stream,
            "message_count": message_count,
            "metadata": {
                "used_context_history": used_context_history,
            },
        },
        stacklevel=2,
    )


def log_service_response(
    *,
    provider: str | None,
    model: str | None,
    latency_ms: float,
    content: str,
    finish_reason: str | None,
    usage: Any,
) -> None:
    usage_payload = None
    if usage is not None:
        usage_payload = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

    logger = get_logger("services")
    logger.info(
        "Service response ready.",
        extra={
            "event": "service.response",
            "provider": provider,
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "content_length": len(content),
            "finish_reason": finish_reason,
            "usage": usage_payload,
            "success": True,
        },
        stacklevel=2,
    )


def log_provider_request(
    *,
    provider: str,
    model: str | None,
    endpoint: str | None,
    stream: bool,
    message_count: int,
    has_attachments: bool,
    has_tools: bool,
    has_response_format: bool,
    timeout_seconds: float,
    request_payload: dict[str, Any] | None = None,
    payload_preview: dict[str, Any] | None = None,
) -> None:
    metadata: dict[str, Any] = {}
    if request_payload:
        metadata["request_payload"] = request_payload
    if payload_preview:
        metadata["payload_preview"] = payload_preview

    logger = get_logger("providers")
    logger.info(
        "Provider request dispatched.",
        extra={
            "event": "provider.request",
            "provider": provider,
            "model": model,
            "endpoint": endpoint,
            "stream": stream,
            "message_count": message_count,
            "has_attachments": has_attachments,
            "has_tools": has_tools,
            "has_response_format": has_response_format,
            "timeout_seconds": timeout_seconds,
            "metadata": metadata or None,
        },
        stacklevel=2,
    )


def log_provider_response(
    *,
    provider: str,
    model: str | None,
    finish_reason: str | None,
    usage: Any,
    latency_ms: float,
    success: bool,
    response_payload: dict[str, Any] | None = None,
) -> None:
    usage_payload = None
    if usage is not None:
        usage_payload = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

    logger = get_logger("providers")
    metadata: dict[str, Any] | None = None
    if response_payload:
        metadata = {"response_payload": response_payload}
    logger.info(
        "Provider response received.",
        extra={
            "event": "provider.response",
            "provider": provider,
            "model": model,
            "finish_reason": finish_reason,
            "usage": usage_payload,
            "latency_ms": round(latency_ms, 2),
            "success": success,
            "metadata": metadata,
        },
        stacklevel=2,
    )


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."
