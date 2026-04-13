"""聊天运行时 Hook 骨架。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Literal

if TYPE_CHECKING:
    from app.chat_runtime.models import RuntimeTurnContext

# Hook 动作类型：继续、告警、修改、阻断。
HookAction = Literal["continue", "warn", "mutate", "block"]
# Hook 处理器签名定义。
HookHandler = Callable[["HookContext", "RuntimeTurnContext", dict[str, Any]], "HookDecision"]


@dataclass
class HookDecision:
    # Hook 决策动作。
    action: HookAction
    # Hook 决策说明信息。
    message: str | None = None
    # Hook 可选修改载荷，用于 mutate 动作。
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookContext:
    # 当前触发的生命周期事件名。
    event_name: str
    # 当前步骤名；非 step hook 场景可为空。
    step_name: str | None
    # 当前执行 workflow 名称。
    workflow_name: str


def request_audit(
    hook_ctx: HookContext,
    runtime_ctx: RuntimeTurnContext,
    payload: dict[str, Any],
) -> HookDecision:
    del hook_ctx, payload
    return HookDecision(
        action="continue",
        message=f"request_id={runtime_ctx.request.request_id}",
    )


def retrieval_trace(
    hook_ctx: HookContext,
    runtime_ctx: RuntimeTurnContext,
    payload: dict[str, Any],
) -> HookDecision:
    del hook_ctx
    retrieval_status = (
        runtime_ctx.retrieval_result.trace.status
        if runtime_ctx.retrieval_result is not None
        else "disabled"
    )
    return HookDecision(
        action="mutate",
        payload={
            **payload,
            "retrieval_status": retrieval_status,
        },
    )


def prompt_guard(
    hook_ctx: HookContext,
    runtime_ctx: RuntimeTurnContext,
    payload: dict[str, Any],
) -> HookDecision:
    del hook_ctx, payload
    if runtime_ctx.request.user_prompt.strip():
        return HookDecision(action="continue")
    return HookDecision(action="block", message="user_prompt 不能为空。")


def response_postprocess(
    hook_ctx: HookContext,
    runtime_ctx: RuntimeTurnContext,
    payload: dict[str, Any],
) -> HookDecision:
    del hook_ctx
    candidate = payload.get("response_text", runtime_ctx.response_text)
    if not isinstance(candidate, str):
        return HookDecision(action="continue")
    normalized_response_text = candidate.rstrip()
    if normalized_response_text == candidate:
        return HookDecision(action="continue")
    return HookDecision(
        action="mutate",
        payload={**payload, "response_text": normalized_response_text},
    )


def stream_finalize(
    hook_ctx: HookContext,
    runtime_ctx: RuntimeTurnContext,
    payload: dict[str, Any],
) -> HookDecision:
    del hook_ctx, runtime_ctx, payload
    return HookDecision(action="continue")


def error_audit(
    hook_ctx: HookContext,
    runtime_ctx: RuntimeTurnContext,
    payload: dict[str, Any],
) -> HookDecision:
    del hook_ctx, runtime_ctx
    return HookDecision(
        action="warn",
        message=str(payload.get("error_message") or "runtime error"),
    )


def build_default_hook_registry() -> dict[str, HookHandler]:
    return {
        "request_audit": request_audit,
        "retrieval_trace": retrieval_trace,
        "prompt_guard": prompt_guard,
        "response_postprocess": response_postprocess,
        "stream_finalize": stream_finalize,
        "error_audit": error_audit,
    }

