"""Repository 层通用工具。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def datetime_to_iso(value: datetime | None) -> str | None:
    """将 datetime 安全转换为 ISO 字符串。"""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def copy_json_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    """拷贝 JSON 字典，避免可变对象泄漏。"""
    return dict(value or {})


def copy_json_list(value: list[Any] | None) -> list[Any]:
    """拷贝 JSON 列表，避免可变对象泄漏。"""
    return list(value or [])

