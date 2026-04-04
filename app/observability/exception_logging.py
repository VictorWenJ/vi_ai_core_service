"""Unified exception logging helpers."""

from __future__ import annotations

import logging
from typing import Any

from app.observability.logging_setup import get_logger


def log_exception(
    exc: BaseException,
    *,
    event: str,
    message: str,
    logger: logging.Logger | None = None,
    **fields: Any,
) -> None:
    """Emit an error-level log entry with traceback and structured context."""

    target_logger = logger or get_logger("exceptions")
    target_logger.error(
        message,
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "event": event,
            **fields,
        },
    )
