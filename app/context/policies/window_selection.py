"""Default history window selection policies."""

from __future__ import annotations

from app.context.models import ContextSelectionResult, ContextWindow
from app.context.policies.base import WindowSelectionPolicy
from app.context.policies.tokenizer import (
    BaseTokenCounter,
    build_default_token_counter,
)


class LastNMessagesSelectionPolicy(WindowSelectionPolicy):
    """Select the most recent N messages while preserving chronological order."""

    name = "window_selection.last_n_messages"

    def __init__(
        self,
        max_messages: int,
        token_counter: BaseTokenCounter | None = None,
    ) -> None:
        if max_messages <= 0:
            raise ValueError("max_messages must be greater than 0.")
        self._max_messages = max_messages
        self._token_counter = token_counter or build_default_token_counter()

    def select(self, window: ContextWindow) -> ContextSelectionResult:
        selected_messages = list(window.messages[-self._max_messages :])
        source_token_count = self._token_counter.count_messages_tokens(window.messages)
        selected_token_count = self._token_counter.count_messages_tokens(selected_messages)
        dropped_messages = list(window.messages[: max(window.message_count - len(selected_messages), 0)])
        return ContextSelectionResult(
            session_id=window.session_id,
            source_message_count=window.message_count,
            source_token_count=source_token_count,
            token_budget=selected_token_count,
            selected_messages=selected_messages,
            dropped_messages=dropped_messages,
            selected_token_count=selected_token_count,
            selection_policy=self.name,
        )


class TokenAwareWindowSelectionPolicy(WindowSelectionPolicy):
    """Select recent history according to a max token budget."""

    name = "window_selection.token_aware"

    def __init__(
        self,
        max_tokens: int,
        token_counter: BaseTokenCounter | None = None,
    ) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than 0.")
        self._max_tokens = max_tokens
        self._token_counter = token_counter or build_default_token_counter()

    def select(self, window: ContextWindow) -> ContextSelectionResult:
        selected_reversed = []
        dropped_reversed = []
        selected_tokens = 0

        for message in reversed(window.messages):
            message_tokens = self._token_counter.count_message_tokens(message)
            if not selected_reversed and message_tokens > self._max_tokens:
                # 保留最新的超大消息，以便截断策略对其进行压缩。
                selected_reversed.append(message)
                selected_tokens = message_tokens
                continue

            if selected_tokens + message_tokens <= self._max_tokens:
                selected_reversed.append(message)
                selected_tokens += message_tokens
                continue

            dropped_reversed.append(message)

        selected_messages = list(reversed(selected_reversed))
        dropped_messages = list(reversed(dropped_reversed))
        source_token_count = self._token_counter.count_messages_tokens(window.messages)
        selected_token_count = self._token_counter.count_messages_tokens(selected_messages)
        return ContextSelectionResult(
            session_id=window.session_id,
            source_message_count=window.message_count,
            source_token_count=source_token_count,
            token_budget=self._max_tokens,
            selected_messages=selected_messages,
            dropped_messages=dropped_messages,
            selected_token_count=selected_token_count,
            selection_policy=self.name,
        )
