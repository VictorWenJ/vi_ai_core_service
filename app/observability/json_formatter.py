"""JSON formatter for standardized observability logs."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.observability.context import CONTEXT_FIELD_NAMES, get_request_context

_BASE_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys())
_EXPLICIT_LOG_FIELDS = {
    "event",
    "metadata",
    "status_code",
    "latency_ms",
    "path",
    "method",
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
}


class JSONLogFormatter(logging.Formatter):
    """Format log records into stable JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        request_context = get_request_context()
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": getattr(record, "event", "log.event"),
            "message": record.getMessage(),
        }

        for key in CONTEXT_FIELD_NAMES:
            value = getattr(record, key, None) or request_context.get(key)
            if value is not None:
                payload[key] = value

        for key in _EXPLICIT_LOG_FIELDS - {"event", "metadata"}:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = _to_json_safe(value)

        metadata = getattr(record, "metadata", None)
        extra_payload = self._collect_extra_payload(record)
        if metadata is not None or extra_payload:
            metadata_payload: dict[str, Any] = {}
            if isinstance(metadata, dict):
                metadata_payload.update(_to_json_safe(metadata))
            elif metadata is not None:
                metadata_payload["value"] = _to_json_safe(metadata)
            if extra_payload:
                metadata_payload.update(extra_payload)
            payload["metadata"] = metadata_payload

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)

    def _collect_extra_payload(self, record: logging.LogRecord) -> dict[str, Any]:
        extra_payload: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in _BASE_RECORD_FIELDS:
                continue
            if key in _EXPLICIT_LOG_FIELDS:
                continue
            if key in CONTEXT_FIELD_NAMES:
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
