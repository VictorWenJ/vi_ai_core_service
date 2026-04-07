"""Default constants and builders for context policy pipeline."""

from __future__ import annotations

from app.config import ContextPolicyConfig
from app.context.policies.context_policy import ContextPolicyPipeline
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.summary import DeterministicSummaryPolicy
from app.context.policies.tokenizer import BaseTokenCounter, build_default_token_counter
from app.context.policies.truncation import TokenAwareTruncationPolicy
from app.context.policies.window_selection import TokenAwareWindowSelectionPolicy

# 最近 N 条消息”策略使用的默认窗口大小。
DEFAULT_HISTORY_WINDOW_SIZE = 8
# 按字符截断策略使用的默认字符预算。
DEFAULT_HISTORY_CHAR_BUDGET = 4000
# 默认 token 预算：用于 token-aware 窗口选择。
DEFAULT_HISTORY_MAX_TOKEN_BUDGET = 1200
# 默认 token 预算：用于 token-aware 截断（必须小于等于最大 token 预算）。
DEFAULT_HISTORY_TRUNCATION_TOKEN_BUDGET = 900
# 是否默认启用确定性 summary/compaction 策略。
DEFAULT_HISTORY_SUMMARY_ENABLED = True
# 确定性 summary 策略的摘要文本最大字符数。
DEFAULT_HISTORY_SUMMARY_MAX_CHARS = 320
# 当摘要后仍不满足预算约束时的回退行为。
DEFAULT_HISTORY_FALLBACK_BEHAVIOR = "summary_then_drop_oldest"


def build_default_context_policy_pipeline(
    context_config: ContextPolicyConfig | None = None,
    token_counter: BaseTokenCounter | None = None,
) -> ContextPolicyPipeline:
    resolved_context = context_config or ContextPolicyConfig(
        max_token_budget=DEFAULT_HISTORY_MAX_TOKEN_BUDGET,
        truncation_token_budget=DEFAULT_HISTORY_TRUNCATION_TOKEN_BUDGET,
        summary_enabled=DEFAULT_HISTORY_SUMMARY_ENABLED,
        summary_max_chars=DEFAULT_HISTORY_SUMMARY_MAX_CHARS,
        fallback_behavior=DEFAULT_HISTORY_FALLBACK_BEHAVIOR,
    )
    resolved_token_counter = token_counter or build_default_token_counter()

    return ContextPolicyPipeline(
        selection_policy=TokenAwareWindowSelectionPolicy(
            max_tokens=resolved_context.max_token_budget,
            token_counter=resolved_token_counter,
        ),
        truncation_policy=TokenAwareTruncationPolicy(
            max_tokens=resolved_context.truncation_token_budget,
            token_counter=resolved_token_counter,
        ),
        summary_policy=DeterministicSummaryPolicy(
            enabled=resolved_context.summary_enabled,
            max_summary_chars=resolved_context.summary_max_chars,
            fallback_behavior=resolved_context.fallback_behavior,
            token_counter=resolved_token_counter,
        ),
        serialization_policy=DefaultHistorySerializationPolicy(),
    )
