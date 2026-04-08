"""已选历史的截断策略。"""

from __future__ import annotations

from dataclasses import replace

from app.context.models import ContextSelectionResult, ContextTruncationResult
from app.context.policies.base import TruncationPolicy
from app.context.policies.tokenizer import (
    BaseTokenCounter,
    build_default_token_counter,
)


class NoOpTruncationPolicy(TruncationPolicy):
    """保持已选历史不变。"""

    name = "truncation.noop"

    def truncate(self, selection_result: ContextSelectionResult) -> ContextTruncationResult:
        return ContextTruncationResult(
            session_id=selection_result.session_id,
            source_message_count=selection_result.source_message_count,
            source_token_count=selection_result.source_token_count,
            input_message_count=selection_result.selected_message_count,
            input_token_count=selection_result.selected_token_count,
            token_budget=selection_result.selected_token_count,
            messages=list(selection_result.selected_messages),
            final_token_count=selection_result.selected_token_count,
            truncation_policy=self.name,
        )


class CharacterBudgetTruncationPolicy(TruncationPolicy):
    """基于字符预算的轻量截断占位策略。"""

    name = "truncation.character_budget"

    def __init__(self, max_characters: int) -> None:
        if max_characters <= 0:
            raise ValueError("max_characters 必须大于 0。")
        self._max_characters = max_characters

    def truncate(self, selection_result: ContextSelectionResult) -> ContextTruncationResult:
        budget_used = 0
        kept_reversed = []
        dropped_reversed = []
        for message in reversed(selection_result.selected_messages):
            message_length = len(message.content)
            if budget_used + message_length > self._max_characters:
                dropped_reversed.append(message)
                continue
            kept_reversed.append(message)
            budget_used += message_length

        kept_messages = list(reversed(kept_reversed))
        dropped_messages = list(reversed(dropped_reversed))
        return ContextTruncationResult(
            session_id=selection_result.session_id,
            source_message_count=selection_result.source_message_count,
            source_token_count=selection_result.source_token_count,
            input_message_count=selection_result.selected_message_count,
            input_token_count=selection_result.selected_token_count,
            token_budget=self._max_characters,
            messages=kept_messages,
            dropped_messages=dropped_messages,
            final_token_count=budget_used,
            truncation_policy=self.name,
        )


class TokenAwareTruncationPolicy(TruncationPolicy):
    """基于 token 预算的截断：优先保留最近内容，并优先截断更旧内容。"""

    name = "truncation.token_aware"

    def __init__(
        self,
        max_tokens: int,
        token_counter: BaseTokenCounter | None = None,
    ) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens 必须大于 0。")
        self._max_tokens = max_tokens
        self._token_counter = token_counter or build_default_token_counter()

    def truncate(self, selection_result: ContextSelectionResult) -> ContextTruncationResult:
        if selection_result.selected_token_count <= self._max_tokens:
            return ContextTruncationResult(
                session_id=selection_result.session_id,
                source_message_count=selection_result.source_message_count,
                source_token_count=selection_result.source_token_count,
                input_message_count=selection_result.selected_message_count,
                input_token_count=selection_result.selected_token_count,
                token_budget=self._max_tokens,
                messages=list(selection_result.selected_messages),
                final_token_count=selection_result.selected_token_count,
                truncation_policy=self.name,
            )

        # 最终保留的消息
        kept_reversed = []
        # 被丢弃的消息
        dropped_reversed = []
        # 剩余 token 预算
        remaining_budget = self._max_tokens

        # 优先保留最近历史。
        # 如果整条消息放不下，尝试将其内容截断到剩余预算。
        for message in reversed(selection_result.selected_messages):
            message_tokens = self._token_counter.count_message_tokens(message)
            if message_tokens <= remaining_budget:
                kept_reversed.append(message)
                remaining_budget -= message_tokens
                continue

            if remaining_budget <= 0:
                dropped_reversed.append(message)
                continue

            truncated_content = self._token_counter.truncate_message_content_to_fit(
                message=message,
                max_message_tokens=remaining_budget,
            )
            if not truncated_content:
                dropped_reversed.append(message)
                continue

            truncated_message = replace(
                message,
                content=truncated_content,
                metadata={
                    **message.metadata,
                    "truncated": True,
                    "original_content_length": len(message.content),
                },
            )
            truncated_message_tokens = self._token_counter.count_message_tokens(
                truncated_message
            )
            if truncated_message_tokens <= 0:
                dropped_reversed.append(message)
                continue

            kept_reversed.append(truncated_message)
            remaining_budget -= truncated_message_tokens

        kept_messages = list(reversed(kept_reversed))
        dropped_messages = list(reversed(dropped_reversed))
        final_token_count = self._token_counter.count_messages_tokens(kept_messages)

        return ContextTruncationResult(
            session_id=selection_result.session_id,
            source_message_count=selection_result.source_message_count,
            source_token_count=selection_result.source_token_count,
            input_message_count=selection_result.selected_message_count,
            input_token_count=selection_result.selected_token_count,
            token_budget=self._max_tokens,
            messages=kept_messages,
            dropped_messages=dropped_messages,
            final_token_count=final_token_count,
            truncation_policy=self.name,
        )
