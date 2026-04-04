"""Request-scoped observability context based on contextvars."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

CONTEXT_FIELD_NAMES = (
    "request_id",
    "session_id",
    "conversation_id",
    "provider",
    "model",
)

_request_context_var: ContextVar[dict[str, str]] = ContextVar(
    "observability_request_context",
    default={},
)


def set_request_context(
    *,
    request_id: str | None = None,
    session_id: str | None = None,
    conversation_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    """Replace the whole request context with normalized non-empty values."""

    normalized: dict[str, str] = {}
    candidates = {
        "request_id": request_id,
        "session_id": session_id,
        "conversation_id": conversation_id,
        "provider": provider,
        "model": model,
    }
    for key, value in candidates.items():
        normalized_value = _normalize_text(value)
        if normalized_value is not None:
            normalized[key] = normalized_value

    _request_context_var.set(normalized)


def update_request_context(**kwargs: Any) -> None:
    """Merge non-empty context fields into current request context."""

    current = get_request_context()
    for key in CONTEXT_FIELD_NAMES:
        if key not in kwargs:
            continue

        normalized_value = _normalize_text(kwargs[key])
        if normalized_value is None:
            continue
        current[key] = normalized_value

    _request_context_var.set(current)


def get_request_context() -> dict[str, str]:
    """Return a copy of current request context."""

    return dict(_request_context_var.get())


def clear_request_context() -> None:
    """Clear all request-scoped context fields."""

    _request_context_var.set({})


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
