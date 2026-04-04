"""Central logging setup for observability."""

from __future__ import annotations

import logging
import sys
from typing import TextIO

from app.config import ObservabilityConfig
from app.observability.json_formatter import JSONLogFormatter

LOGGER_NAMESPACE = "vi_ai_core_service"

_active_settings = ObservabilityConfig()

_bootstrap_logger = logging.getLogger(LOGGER_NAMESPACE)
if not _bootstrap_logger.handlers:
    _bootstrap_logger.addHandler(logging.NullHandler())


class _ObservabilityFilter(logging.Filter):
    def __init__(self, settings: ObservabilityConfig) -> None:
        super().__init__()
        self._settings = settings
        resolved_level = logging.getLevelName(settings.log_level.upper())
        self._level_no = resolved_level if isinstance(resolved_level, int) else logging.INFO

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.ERROR:
            return True
        if not self._settings.log_enabled:
            return False
        return record.levelno >= self._level_no


def configure_logging(
    settings: ObservabilityConfig,
    stream: TextIO | None = None,
) -> logging.Logger:
    """Configure project logger with JSON output and level gating."""

    if settings.log_format.lower() != "json":
        raise ValueError("Only JSON log format is supported in the current stage.")

    logger = logging.getLogger(LOGGER_NAMESPACE)
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JSONLogFormatter())
    handler.addFilter(_ObservabilityFilter(settings))
    logger.addHandler(handler)

    global _active_settings
    _active_settings = settings
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a namespaced project logger."""

    if not name:
        return logging.getLogger(LOGGER_NAMESPACE)
    return logging.getLogger(f"{LOGGER_NAMESPACE}.{name}")


def get_logging_settings() -> ObservabilityConfig:
    """Return the latest active logging settings."""

    return _active_settings
