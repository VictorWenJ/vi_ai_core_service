"""Prompt renderer skeleton."""

from __future__ import annotations

from app.prompts.registry import get_prompt_template_path


def render_prompt(template_id: str, variables: dict[str, str] | None = None) -> str:
    template_path = get_prompt_template_path(template_id)
    template_content = template_path.read_text(encoding="utf-8")

    rendered_content = template_content
    for key, value in (variables or {}).items():
        rendered_content = rendered_content.replace(f"{{{{{key}}}}}", value)

    return rendered_content
