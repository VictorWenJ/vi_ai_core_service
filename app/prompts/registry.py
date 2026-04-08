"""提示词资产注册表骨架。"""

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
        raise ValueError(f"未知的提示词模板 '{template_id}'。") from exc
