"""Default history window selection policies."""

from __future__ import annotations

from app.context.models import ContextSelectionResult, ContextWindow
from app.context.policies.base import WindowSelectionPolicy


class LastNMessagesSelectionPolicy(WindowSelectionPolicy):
    """Select the most recent N messages while preserving chronological order."""

    name = "window_selection.last_n_messages"

    def __init__(self, max_messages: int) -> None:
        if max_messages <= 0:
            raise ValueError("max_messages must be greater than 0.")
        self._max_messages = max_messages

    def select(self, window: ContextWindow) -> ContextSelectionResult:
        selected_messages = list(window.messages[-self._max_messages :])
        return ContextSelectionResult(
            session_id=window.session_id,
            source_message_count=window.message_count,
            selected_messages=selected_messages,
            selection_policy=self.name,
        )
