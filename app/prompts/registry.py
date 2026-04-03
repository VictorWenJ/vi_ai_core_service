"""Prompt asset registry skeleton."""

from __future__ import annotations

from pathlib import Path

PROMPT_TEMPLATE_MAP = {
    "chat.default_system": Path(__file__).resolve().parent
    / "templates"
    / "chat"
    / "default_system.md",
}


def get_prompt_template_path(template_id: str) -> Path:
    try:
        return PROMPT_TEMPLATE_MAP[template_id]
    except KeyError as exc:
        raise ValueError(f"Unknown prompt template '{template_id}'.") from exc
