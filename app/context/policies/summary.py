"""上下文历史的摘要/压缩策略。"""

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
    """保持截断结果不变。"""

    name = "summary.noop"

    def summarize(
        self,
        *,
        window: ContextWindow,
        selection: ContextSelectionResult,
        truncation: ContextTruncationResult,
    ) -> ContextSummaryResult:
        del window, selection
        return ContextSummaryResult(
            session_id=truncation.session_id,
            conversation_id=truncation.conversation_id,
            source_message_count=truncation.source_message_count,
            source_token_count=truncation.source_token_count,
            input_message_count=truncation.final_message_count,
            input_token_count=truncation.final_token_count,
            token_budget=truncation.truncation_token_budget,
            messages=list(truncation.messages),
            dropped_messages=[],
            summary_policy=self.name,
            summary_applied=False,
            summary_text=None,
            final_token_count=truncation.final_token_count,
        )


class DeterministicSummaryPolicy(SummaryPolicy):
    """为被丢弃历史生成确定性摘要消息。"""

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
            raise ValueError("max_summary_chars 必须大于 0。")
        if fallback_behavior not in {"summary_then_drop_oldest", "drop_oldest"}:
            raise ValueError(
                "fallback_behavior 必须是以下之一："
                "summary_then_drop_oldest, drop_oldest。"
            )
        self._enabled = enabled
        self._max_summary_chars = max_summary_chars
        self._fallback_behavior = fallback_behavior
        self._token_counter = token_counter or build_default_token_counter()

    def summarize(
        self,
        *,
        window: ContextWindow,
        selection: ContextSelectionResult,
        truncation: ContextTruncationResult,
    ) -> ContextSummaryResult:
        # 1. 开关关闭时，直接走 no-op，保持截断结果不变。
        # 这是 summary 阶段的最小短路路径，不引入额外行为。

        # 开关控制不做总结
        if not self._enabled:
            return NoOpSummaryPolicy().summarize(
                window=window,
                selection=selection,
                truncation=truncation,
            )

        # 2. 收集“在 selection 和 truncation 阶段被移出的历史消息”。
        # 只有这部分历史才是 summary 需要压缩承接的对象。
        dropped_messages = (
                list(selection.dropped_messages) + list(truncation.dropped_messages)
        )

        # 3. 没有被移出的历史时，不需要做 summary，直接返回 no-op。
        # 只有真的有“被丢掉的历史”时，才会做 summary
        if not dropped_messages:
            return NoOpSummaryPolicy().summarize(
                window=window,
                selection=selection,
                truncation=truncation,
            )

        # 4. 基于被移出历史构建确定性摘要文本，并封装成一条 summary 消息。
        # 该消息会放在消息列表头部，用于承接旧历史语义。
        # 规则化压缩 + 最近几条 preview
        summary_text = self._build_summary_text(dropped_messages)
        summary_message = ContextMessage(
            role="assistant",
            content=summary_text,
            metadata={"summary": True, "message_count": len(dropped_messages)},
        )

        # 5. 组合“summary + 当前截断后保留消息”，形成 summary 阶段输入。
        composed_messages = [summary_message] + list(truncation.messages)

        # 6. 再次按 truncation 预算做收敛（summary 也要受总预算约束）。
        # 根据 fallback 行为，可能压缩 summary、丢最旧消息、或继续裁剪最新消息。
        bounded_messages, summary_dropped_messages = self._fit_to_budget(
            messages=composed_messages,
            token_budget=truncation.truncation_token_budget,
        )

        # 7. 判断最终结果是否真的保留了 summary 头消息，并计算最终 token 成本。
        # 如果 summary 头被预算淘汰，summary_text 应视为未生效。
        summary_applied = len(bounded_messages) > 0 and bounded_messages[0].metadata.get(
            "summary", False
        )
        final_token_count = self._token_counter.count_messages_tokens(bounded_messages)
        final_summary_text = bounded_messages[0].content if summary_applied else None

        # 8. 输出标准化 summary 结果：
        # - messages: summary 阶段最终保留消息
        # - dropped_messages: summary 阶段额外淘汰消息
        # - summary_applied/summary_text: summary 是否实际落地
        return ContextSummaryResult(
            session_id=truncation.session_id,
            conversation_id=truncation.conversation_id,
            source_message_count=selection.source_message_count,
            source_token_count=selection.source_token_count,
            input_message_count=truncation.final_message_count,
            input_token_count=truncation.final_token_count,
            token_budget=truncation.truncation_token_budget,
            messages=bounded_messages,
            dropped_messages=summary_dropped_messages,
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
    ) -> tuple[list[ContextMessage], list[ContextMessage]]:

        if self._fallback_behavior == "drop_oldest":
            return self._fit_drop_oldest(messages=messages, token_budget=token_budget)

        return self._fit_summary_then_drop_oldest(
            messages=messages,
            token_budget=token_budget,
        )

    def _fit_drop_oldest(
        self,
        *,
        messages: list[ContextMessage],
        token_budget: int,
    ) -> tuple[list[ContextMessage], list[ContextMessage]]:
        bounded = list(messages)
        dropped: list[ContextMessage] = []
        while bounded and self._token_counter.count_messages_tokens(bounded) > token_budget:
            dropped.append(bounded.pop(0))

        if not bounded:
            return [], dropped

        total_tokens = self._token_counter.count_messages_tokens(bounded)
        if total_tokens <= token_budget:
            return bounded, dropped

        # 仅剩单条消息仍超预算时，截断内容以适配预算。
        only_message = bounded[0]
        truncated_content = self._token_counter.truncate_message_content_to_fit(
            message=only_message,
            max_message_tokens=token_budget,
            keep_tail=True,
        )
        if not truncated_content:
            dropped.append(only_message)
            return [], dropped

        bounded[0] = replace(
            only_message,
            content=truncated_content,
            metadata={
                **only_message.metadata,
                "truncated": True,
                "original_content_length": len(only_message.content),
            },
        )
        if self._token_counter.count_messages_tokens(bounded) > token_budget:
            dropped.extend(bounded)
            return [], dropped
        return bounded, dropped

    def _fit_summary_then_drop_oldest(
        self,
        *,
        messages: list[ContextMessage],
        token_budget: int,
    ) -> tuple[list[ContextMessage], list[ContextMessage]]:
        if not messages:
            return [], []

        dropped: list[ContextMessage] = []
        summary_message = (
            messages[0] if messages and messages[0].metadata.get("summary", False) else None
        )
        raw_messages = list(messages[1:] if summary_message else messages)
        latest_raw = raw_messages[-1] if raw_messages else None
        older_raw = list(raw_messages[:-1]) if latest_raw else []

        while True:
            bounded = []
            if summary_message is not None:
                bounded.append(summary_message)
            bounded.extend(older_raw)
            if latest_raw is not None:
                bounded.append(latest_raw)

            total_tokens = self._token_counter.count_messages_tokens(bounded)
            if total_tokens <= token_budget:
                return bounded, dropped

            # 第 1 步：优先压缩 summary（默认保留最新原始消息）。
            if summary_message is not None:
                reserved_messages = list(older_raw)
                if latest_raw is not None:
                    reserved_messages.append(latest_raw)
                reserved_tokens = self._token_counter.count_messages_tokens(reserved_messages)
                summary_budget = max(token_budget - reserved_tokens, 0)
                truncated_summary = self._token_counter.truncate_message_content_to_fit(
                    message=summary_message,
                    max_message_tokens=summary_budget,
                    keep_tail=False,
                )
                if truncated_summary and truncated_summary != summary_message.content:
                    summary_message = replace(
                        summary_message,
                        content=truncated_summary,
                        metadata={
                            **summary_message.metadata,
                            "truncated": True,
                            "original_content_length": len(summary_message.content),
                        },
                    )
                    continue

            # 第 2 步：若仍超预算，先丢弃更旧的原始消息。
            if older_raw:
                dropped.append(older_raw.pop(0))
                continue

            # 第 3 步：若仅剩 summary 与最新原始消息，先移除 summary。
            if summary_message is not None:
                dropped.append(summary_message)
                summary_message = None
                continue

            # 第 4 步：若最新原始消息仍过长，截断其内容。
            if latest_raw is not None:
                truncated_latest = self._token_counter.truncate_message_content_to_fit(
                    message=latest_raw,
                    max_message_tokens=token_budget,
                    keep_tail=True,
                )
                if truncated_latest and truncated_latest != latest_raw.content:
                    latest_raw = replace(
                        latest_raw,
                        content=truncated_latest,
                        metadata={
                            **latest_raw.metadata,
                            "truncated": True,
                            "original_content_length": len(latest_raw.content),
                        },
                    )
                    continue
                dropped.append(latest_raw)
                latest_raw = None
                continue

            return [], dropped
