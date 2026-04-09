"""分层短期记忆块渲染。"""

from __future__ import annotations

from app.context.models import RollingSummaryState, WorkingMemoryState


def render_working_memory_block(working_memory: WorkingMemoryState) -> str | None:
    lines: list[str] = []
    if working_memory.active_goal:
        lines.append(f"- active_goal: {working_memory.active_goal}")
    if working_memory.constraints:
        lines.append(f"- constraints: {' | '.join(working_memory.constraints)}")
    if working_memory.decisions:
        lines.append(f"- decisions: {' | '.join(working_memory.decisions)}")
    if working_memory.open_questions:
        lines.append(f"- open_questions: {' | '.join(working_memory.open_questions)}")
    if working_memory.next_step:
        lines.append(f"- next_step: {working_memory.next_step}")
    if not lines:
        return None
    return "[working_memory]\n" + "\n".join(lines)


def render_rolling_summary_block(summary: RollingSummaryState) -> str | None:
    if not summary.has_content:
        return None
    source_message_count = max(summary.source_message_count, 0)
    return (
        "[rolling_summary]\n"
        f"source_message_count={source_message_count}\n"
        f"text={summary.text}"
    )
