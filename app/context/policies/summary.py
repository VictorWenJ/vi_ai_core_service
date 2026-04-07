"""Summary/compaction policies for context history."""

from __future__ import annotations

from dataclasses import replace

from app.context.models import (
    ContextMessage,
    ContextSelectionResult,
    ContextSummaryResult,
    ContextTruncationResult,
    ContextWindow,
)
from app.context.policies.base import SummaryPolicy
from app.context.policies.tokenizer import (
    BaseTokenCounter,
    build_default_token_counter,
)


class NoOpSummaryPolicy(SummaryPolicy):
    """Keep truncation output unchanged."""

    name = "summary.noop"

    def summarize(
        self,
        *,
        window: ContextWindow,
        selection_result: ContextSelectionResult,
        truncation_result: ContextTruncationResult,
    ) -> ContextSummaryResult:
        del window, selection_result
        return ContextSummaryResult(
            session_id=truncation_result.session_id,
            source_message_count=truncation_result.source_message_count,
            source_token_count=truncation_result.source_token_count,
            input_message_count=truncation_result.final_message_count,
            input_token_count=truncation_result.final_token_count,
            token_budget=truncation_result.token_budget,
            messages=list(truncation_result.messages),
            summary_policy=self.name,
            summary_applied=False,
            summary_text=None,
            final_token_count=truncation_result.final_token_count,
        )


class DeterministicSummaryPolicy(SummaryPolicy):
    """Create a deterministic summary message for dropped history."""

    name = "summary.deterministic_compaction"

    def __init__(
        self,
        *,
        enabled: bool,
        max_summary_chars: int,
        fallback_behavior: str,
        token_counter: BaseTokenCounter | None = None,
    ) -> None:
        if max_summary_chars <= 0:
            raise ValueError("max_summary_chars must be greater than 0.")
        self._enabled = enabled
        self._max_summary_chars = max_summary_chars
        self._fallback_behavior = fallback_behavior
        self._token_counter = token_counter or build_default_token_counter()

    def summarize(
        self,
        *,
        window: ContextWindow,
        selection_result: ContextSelectionResult,
        truncation_result: ContextTruncationResult,
    ) -> ContextSummaryResult:

        # 不做总结
        if not self._enabled:
            return NoOpSummaryPolicy().summarize(
                window=window,
                selection_result=selection_result,
                truncation_result=truncation_result,
            )

        dropped_messages = (
            list(selection_result.dropped_messages) + list(truncation_result.dropped_messages)
        )
        if not dropped_messages:
            return NoOpSummaryPolicy().summarize(
                window=window,
                selection_result=selection_result,
                truncation_result=truncation_result,
            )

        summary_text = self._build_summary_text(dropped_messages)
        summary_message = ContextMessage(
            role="assistant",
            content=summary_text,
            metadata={"summary": True, "message_count": len(dropped_messages)},
        )
        composed_messages = [summary_message] + list(truncation_result.messages)
        bounded_messages = self._fit_to_budget(
            messages=composed_messages,
            token_budget=truncation_result.token_budget,
        )
        summary_applied = len(bounded_messages) > 0 and bounded_messages[0].metadata.get(
            "summary", False
        )
        final_token_count = self._token_counter.count_messages_tokens(bounded_messages)
        final_summary_text = bounded_messages[0].content if summary_applied else None

        return ContextSummaryResult(
            session_id=truncation_result.session_id,
            source_message_count=selection_result.source_message_count,
            source_token_count=selection_result.source_token_count,
            input_message_count=truncation_result.final_message_count,
            input_token_count=truncation_result.final_token_count,
            token_budget=truncation_result.token_budget,
            messages=bounded_messages,
            summary_policy=self.name,
            summary_applied=summary_applied,
            summary_text=final_summary_text,
            final_token_count=final_token_count,
        )

    def _build_summary_text(self, dropped_messages: list[ContextMessage]) -> str:
        preview_chunks = []
        for message in dropped_messages[-3:]:
            normalized = " ".join(message.content.split())
            if not normalized:
                continue
            preview_chunks.append(f"{message.role}: {normalized[:80]}")

        preview = " | ".join(preview_chunks)
        base_text = (
            f"[history_compacted] {len(dropped_messages)} earlier messages were compacted."
        )
        if preview:
            base_text = f"{base_text} preview={preview}"
        return base_text[: self._max_summary_chars]

    def _fit_to_budget(
        self,
        *,
        messages: list[ContextMessage],
        token_budget: int,
    ) -> list[ContextMessage]:
        bounded = list(messages)
        if not bounded:
            return bounded

        while (
            bounded
            and self._token_counter.count_messages_tokens(bounded) > token_budget
            and len(bounded) > 1
        ):
            # Summary stays as head; drop oldest non-summary message first.
            bounded.pop(1)

        total_tokens = self._token_counter.count_messages_tokens(bounded)
        if total_tokens <= token_budget:
            return bounded

        if bounded and bounded[0].metadata.get("summary", False):
            summary_head = bounded[0]
            truncated_summary = self._token_counter.truncate_message_content_to_fit(
                message=summary_head,
                max_message_tokens=token_budget,
                keep_tail=False,
            )
            if truncated_summary:
                bounded[0] = replace(summary_head, content=truncated_summary)

        if self._token_counter.count_messages_tokens(bounded) > token_budget:
            if self._fallback_behavior == "drop_oldest":
                return []
            return []

        return bounded
