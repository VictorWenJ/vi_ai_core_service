"""Log4j-like formatter with business JSON payload."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from app.observability.context import CONTEXT_FIELD_NAMES, get_request_context

_BASE_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys())
_EXPLICIT_BUSINESS_FIELDS = {
    "event",
    "metadata",
    "route",
    "status_code",
    "latency_ms",
    "stream",
    "success",
    "message_count",
    "content_length",
    "finish_reason",
    "usage",
    "has_attachments",
    "has_tools",
    "has_response_format",
    "timeout_seconds",
    "endpoint",
    "error_type",
    "error_message",
}
_SYSTEM_ONLY_FIELDS = {"path", "method"}


class JSONLogFormatter(logging.Formatter):
    """Format records as log4j-style prefix + message JSON."""

    def format(self, record: logging.LogRecord) -> str:
        request_context = get_request_context()
        event = getattr(record, "event", "log.event")
        prefix = self._build_prefix(record, event)
        payload: dict[str, Any] = {}

        for key in CONTEXT_FIELD_NAMES:
            value = getattr(record, key, None) or request_context.get(key)
            if value is not None:
                payload[key] = _to_json_safe(value)

        for key in _EXPLICIT_BUSINESS_FIELDS - {"event", "metadata"}:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = _to_json_safe(value)

        metadata = getattr(record, "metadata", None)
        extra_payload = self._collect_extra_payload(record)
        if metadata is not None or extra_payload:
            if isinstance(metadata, dict):
                payload.update(_to_json_safe(metadata))
            elif metadata is not None:
                payload["metadata"] = _to_json_safe(metadata)
            if extra_payload:
                payload.update(extra_payload)

        message = f"{prefix} message={json.dumps(payload, ensure_ascii=False)}"

        if record.exc_info:
            exception_text = self.formatException(record.exc_info)
            return f"{message}\n{exception_text}"

        if record.stack_info:
            return f"{message}\n{self.formatStack(record.stack_info)}"

        return message

    def _build_prefix(self, record: logging.LogRecord, event: str) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[
            :-3
        ]
        level = f"{record.levelname:<5}"
        thread_name = record.threadName
        source = f"{record.filename}:{record.lineno}"
        return (
            f"{timestamp} {level} [{thread_name}] {record.name} "
            f"{source} event={event}"
        )

    def _collect_extra_payload(self, record: logging.LogRecord) -> dict[str, Any]:
        extra_payload: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in _BASE_RECORD_FIELDS:
                continue
            if key in _EXPLICIT_BUSINESS_FIELDS:
                continue
            if key in CONTEXT_FIELD_NAMES:
                continue
            if key in _SYSTEM_ONLY_FIELDS:
                continue
            extra_payload[key] = _to_json_safe(value)
        return extra_payload


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _to_json_safe(inner_value) for key, inner_value in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]
    return str(value)
