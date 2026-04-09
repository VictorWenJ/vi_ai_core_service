"""上下文策略管线的默认常量与构建器。"""

from __future__ import annotations

from setuptools.windows_support import windows_only
from torch.signal.windows.windows import window_common_args

from app.config import ContextPolicyConfig
from app.context.policies.context_policy import ContextPolicyPipeline
from app.context.policies.serialization import DefaultHistorySerializationPolicy
from app.context.policies.summary import DeterministicSummaryPolicy
from app.context.policies.tokenizer import BaseTokenCounter, build_default_token_counter
from app.context.policies.truncation import TokenAwareTruncationPolicy
from app.context.policies.window_selection import TokenAwareWindowSelectionPolicy

# 默认 token 预算：用于 token-aware 窗口选择。
DEFAULT_HISTORY_WINDOW_TOKEN_BUDGET = 1200
# 默认 token 预算：用于 token-aware 截断（需小于等于最大预算）。
DEFAULT_HISTORY_TRUNCATION_TOKEN_BUDGET = 900
# 是否默认启用确定性 summary/compaction 策略。
DEFAULT_HISTORY_SUMMARY_ENABLED = True
# 确定性 summary 策略的摘要文本最大字符数。
DEFAULT_HISTORY_SUMMARY_MAX_CHARS = 320
# 摘要后仍不满足预算约束时的回退行为。
DEFAULT_HISTORY_FALLBACK_BEHAVIOR = "summary_then_drop_oldest"
# 估算消息 token 时的固定消息开销（工程近似值）。
DEFAULT_HISTORY_MESSAGE_OVERHEAD_TOKENS = 4


def build_default_context_policy_pipeline(
    context_config: ContextPolicyConfig | None = None,
    token_counter: BaseTokenCounter | None = None,
) -> ContextPolicyPipeline:
    """装配默认上下文策略配置"""

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
