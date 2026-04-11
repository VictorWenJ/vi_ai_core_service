"""上下文策略管线的默认常量与构建器。"""

from __future__ import annotations

from app.config import ContextPolicyConfig
from app.context.policies.context_policy import ContextPolicyPipeline
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.summary import DeterministicSummaryPolicy
from app.context.policies.tokenizer import BaseTokenCounter, build_default_token_counter
from app.context.policies.truncation import TokenAwareTruncationPolicy
from app.context.policies.window_selection import TokenAwareWindowSelectionPolicy

# 历史窗口选择阶段默认 token 预算上限，单位为 token。
DEFAULT_HISTORY_WINDOW_TOKEN_BUDGET = 1200
# 历史截断阶段默认 token 预算上限，单位为 token。
DEFAULT_HISTORY_TRUNCATION_TOKEN_BUDGET = 900
# 默认是否启用摘要/压缩策略。
DEFAULT_HISTORY_SUMMARY_ENABLED = True
# 默认摘要最大长度，单位为字符数（chars）。
DEFAULT_HISTORY_SUMMARY_MAX_CHARS = 320
# 摘要后仍超预算时的默认回退策略。
DEFAULT_HISTORY_FALLBACK_BEHAVIOR = "summary_then_drop_oldest"
# 估算单条消息 token 时的默认固定开销，单位为 token。
DEFAULT_HISTORY_MESSAGE_OVERHEAD_TOKENS = 4


def build_default_context_policy_pipeline(
    context_config: ContextPolicyConfig | None = None,
    token_counter: BaseTokenCounter | None = None,
) -> ContextPolicyPipeline:
    """装配默认上下文策略管线。"""

    resolved_context = context_config or ContextPolicyConfig(
        windows_token_budget=DEFAULT_HISTORY_WINDOW_TOKEN_BUDGET,
        truncation_token_budget=DEFAULT_HISTORY_TRUNCATION_TOKEN_BUDGET,
        summary_enabled=DEFAULT_HISTORY_SUMMARY_ENABLED,
        summary_max_chars=DEFAULT_HISTORY_SUMMARY_MAX_CHARS,
        fallback_behavior=DEFAULT_HISTORY_FALLBACK_BEHAVIOR,
        message_overhead_tokens=DEFAULT_HISTORY_MESSAGE_OVERHEAD_TOKENS,
    )

    resolved_token_counter = token_counter or build_default_token_counter(
        message_overhead_tokens=resolved_context.message_overhead_tokens
    )

    return ContextPolicyPipeline(
        selection_policy=TokenAwareWindowSelectionPolicy(
            window_max_tokens=resolved_context.windows_token_budget,
            token_counter=resolved_token_counter,
        ),
        truncation_policy=TokenAwareTruncationPolicy(
            truncation_max_tokens=resolved_context.truncation_token_budget,
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
