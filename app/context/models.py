"""Minimal context models for future session memory support."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ContextMessage:
    role: str
    content: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ContextWindow:
    session_id: str
    messages: list[ContextMessage] = field(default_factory=list)
