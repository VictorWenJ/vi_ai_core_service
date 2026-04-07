from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import logging
import sys
from typing import Any

_LOGGER_NAME = "vi_ai_core_service.report"
_FORMAT = (
    "%(asctime)s.%(msecs)03d %(levelname)-5s [%(threadName)s] "
    "%(name)s %(filename)s:%(lineno)d %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _get_report_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_FORMAT, datefmt=_DATE_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_report(event: str, message: Any) -> None:
    report_logger = _get_report_logger()
    payload = _to_payload_dict(message)
    payload_json = json.dumps(payload, ensure_ascii=False)
    report_logger.info("event=%s message=%s", event, payload_json, stacklevel=2)


def _to_payload_dict(message: Any) -> dict[str, Any]:
    normalized = _normalize_for_json(message)
    if isinstance(normalized, dict):
        return normalized
    return {"value": normalized}


def _normalize_for_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if hasattr(value, "model_dump"):
        return _normalize_for_json(value.model_dump(mode="json"))

    if hasattr(value, "dict"):
        return _normalize_for_json(value.dict())

    if is_dataclass(value):
        return _normalize_for_json(asdict(value))

    if isinstance(value, dict):
        return {str(k): _normalize_for_json(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_normalize_for_json(v) for v in value]

    return str(value)
