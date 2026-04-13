"""聊天运行时执行轨迹模型。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class HookTraceEvent:
    # Hook 生命周期事件名（如 before_request）。
    event_name: str
    # 触发的 Hook 名称。
    hook_name: str
    # Hook 决策动作（continue/warn/mutate/block）。
    action: str
    # Hook 补充说明信息。
    message: str | None = None


@dataclass
class StepTraceEvent:
    # 执行步骤名称（如 retrieve_knowledge）。
    step_name: str
    # 步骤执行状态（succeeded/failed）。
    status: str
    # 步骤执行耗时，单位为毫秒（ms）。
    latency_ms: float
    # 步骤失败时的错误类型。
    error_type: str | None = None


@dataclass
class ExecutionTrace:
    # 当前执行使用的 workflow 名称。
    workflow_name: str
    # 执行开始时间（UTC ISO 字符串）。
    started_at: str
    # 执行完成时间（UTC ISO 字符串）；未完成时为空。
    completed_at: str | None
    # 总执行耗时，单位为毫秒（ms）；未完成时为空。
    latency_ms: float | None
    # 实际调用的 provider 名称。
    provider: str | None
    # 实际调用的模型名称。
    model: str | None
    # 是否为流式执行。
    stream: bool
    # 是否启用了检索能力。
    retrieval_enabled: bool
    # 检索命中数量，单位为条（count）。
    retrieval_hit_count: int
    # 组装阶段上下文消息数量，单位为条（count）。
    context_message_count: int
    # Hook 触发明细事件列表。
    hook_events: list[HookTraceEvent] = field(default_factory=list)
    # Step 执行明细事件列表。
    step_events: list[StepTraceEvent] = field(default_factory=list)
    # 结束原因（如 stop/length/cancelled）。
    finish_reason: str | None = None
    # 失败时的错误类型标识。
    error_type: str | None = None
    # 内部高精度开始时间戳，单位为秒（seconds）。
    started_perf_seconds: float = field(default_factory=perf_counter, repr=False)

    @classmethod
    def create(cls, *, workflow_name: str, stream: bool) -> "ExecutionTrace":
        return cls(
            workflow_name=workflow_name,
            started_at=_now_utc_iso(),
            completed_at=None,
            latency_ms=None,
            provider=None,
            model=None,
            stream=stream,
            retrieval_enabled=False,
            retrieval_hit_count=0,
            context_message_count=0,
        )

    def record_hook(
        self,
        *,
        event_name: str,
        hook_name: str,
        action: str,
        message: str | None = None,
    ) -> None:
        self.hook_events.append(
            HookTraceEvent(
                event_name=event_name,
                hook_name=hook_name,
                action=action,
                message=message,
            )
        )

    def record_step(
        self,
        *,
        step_name: str,
        status: str,
        latency_ms: float,
        error_type: str | None = None,
    ) -> None:
        self.step_events.append(
            StepTraceEvent(
                step_name=step_name,
                status=status,
                latency_ms=latency_ms,
                error_type=error_type,
            )
        )

    def complete(
        self,
        *,
        provider: str | None,
        model: str | None,
        finish_reason: str | None,
        error_type: str | None,
    ) -> None:
        self.completed_at = _now_utc_iso()
        self.latency_ms = round((perf_counter() - self.started_perf_seconds) * 1000, 2)
        self.provider = provider
        self.model = model
        self.finish_reason = finish_reason
        self.error_type = error_type

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

