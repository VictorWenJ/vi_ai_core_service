"""流式聊天服务：负责 SSE 事件生命周期与会话收口。"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict
from time import perf_counter
from typing import Any
from uuid import uuid4

from app.api.schemas import ChatCancelRequest, ChatStreamOptions, ChatStreamRequest
from app.config import AppConfig
from app.context.manager import ContextManager
from app.context.models import normalize_conversation_scope, now_utc_iso
from app.observability.log_until import log_report
from app.providers.base import (
    ProviderConfigurationError,
    ProviderInvocationError,
    ProviderNotImplementedError,
    StreamNotImplementedError,
)
from app.providers.registry import ProviderRegistry
from app.schemas.llm_response import LLMStreamChunk, LLMUsage
from app.services.cancellation_registry import CancellationRegistry
from app.services.errors import ServiceNotImplementedError
from app.services.prompt_service import PromptService
from app.services.request_assembler import ChatRequestAssembler


class StreamingChatService:
    """流式聊天交付层。"""

    def __init__(
            self,
            *,
            app_config: AppConfig,
            registry: ProviderRegistry,
            prompt_service: PromptService,
            context_manager: ContextManager,
            request_assembler: ChatRequestAssembler,
            cancellation_registry: CancellationRegistry,
    ) -> None:
        self._app_config = app_config
        self._registry = registry
        self._prompt_service = prompt_service
        self._context_manager = context_manager
        self._request_assembler = request_assembler
        self._cancellation_registry = cancellation_registry

    def stream_chat_from_user_prompt(self, chat_request: ChatStreamRequest) -> Iterator[dict[str, Any]]:
        # 步骤 0：全局开关校验。若环境未开启 streaming，则直接拒绝。
        if not self._app_config.streaming_config.streaming_enabled:
            raise ServiceNotImplementedError("当前环境未开启流式能力。")

        # 步骤 1：初始化本次流式会话的核心标识。
        # request_id 用于请求维度追踪；assistant_message_id 用于消息生命周期追踪；
        # user_message_id 用于 completed 收口时精确关联本轮 user/assistant。
        started_at = perf_counter()
        request_id = (chat_request.request_id or f"req_{uuid4()}").strip()
        assistant_message_id = f"am_{uuid4()}"
        user_message_id = f"um_{uuid4()}"

        # 步骤 2：标准化会话作用域（session + conversation）。
        normalized_session_id = (chat_request.session_id or "").strip() or None
        normalized_conversation_id = (chat_request.conversation_id or "").strip() or None
        conversation_scope = normalize_conversation_scope(normalized_conversation_id)

        # 步骤 3：复用现有 assembler 组装并规范化请求。
        # 这里保持与同步链路一致的 request assembly 规则，只是把 stream 强制设为 True。
        llm_request = self._request_assembler.assemble_from_user_prompt(
            request=chat_request,
            context_manager=self._context_manager,
        )
        llm_request.request_id = request_id
        llm_request.stream = True
        llm_request = self._request_assembler.normalize_request(
            llm_request,
            provider_registry=self._registry,
            allow_stream=True,
        )

        provider_name = llm_request.provider or self._app_config.default_provider
        provider = self._registry.get_provider(provider_name)

        # 步骤 4：解析流式选项（超时、心跳、usage/trace 输出开关）。
        stream_options = self._resolve_stream_options(chat_request.stream_options)
        timeout_seconds = stream_options["stream_request_timeout_seconds"]
        heartbeat_interval = stream_options["stream_heartbeat_interval_seconds"]

        # 已累计的模型文本（用于 completed/cancelled/failed 收口落盘）。
        partial_output = ""
        # 当前 delta 序号（对外 response.delta 的 sequence 单调递增）。
        sequence = 0
        # 已发出的 SSE 事件计数（用于 trace 统计）。
        stream_event_count = 0
        # 上游返回的结束原因（例如 stop/length）。
        finish_reason: str | None = None
        # 上游返回的 token usage（若厂商支持）。
        usage: LLMUsage | None = None
        # 失败场景的错误码（统一收口到 response.error）。
        error_code: str | None = None
        # 失败场景的错误文案（避免直接泄漏内部堆栈）。
        error_message: str | None = None
        # 流式生命周期当前状态：streaming/completed/failed/cancelled。
        status = "streaming"
        # 是否已收到显式 cancel 信号。
        cancelled = False

        # 步骤 5：有 session 时先写入上下文占位（先 user，再 assistant placeholder）。
        # 这样在 started/delta 阶段就能定位到稳定 message_id，并支持取消/失败收口落盘。
        if normalized_session_id:
            message_metadata = {
                "request_id": request_id,
                "conversation_id": conversation_scope,
                "provider": llm_request.provider,
                "model": llm_request.model,
            }
            self._context_manager.append_user_message(
                session_id=normalized_session_id,
                conversation_id=conversation_scope,
                content=chat_request.user_prompt,
                metadata=message_metadata,
                message_id=user_message_id,
            )
            self._context_manager.create_assistant_placeholder(
                session_id=normalized_session_id,
                conversation_id=conversation_scope,
                assistant_message_id=assistant_message_id,
                metadata=message_metadata,
            )
            context_window = self._context_manager.finalize_assistant_message(
                session_id=normalized_session_id,
                conversation_id=conversation_scope,
                assistant_message_id=assistant_message_id,
                status=status,
                content="",
            )
            log_report("StreamingChatService.stream_chat_from_user_prompt.context_window", context_window)

        # 步骤 6：将本次流任务注册到取消注册表，支持 /chat_stream_cancel 显式取消。
        handle = self._cancellation_registry.register(
            request_id=request_id,
            assistant_message_id=assistant_message_id,
            session_id=normalized_session_id or "__stateless__",
            conversation_id=conversation_scope,
            provider=llm_request.provider,
            model=llm_request.model,
        )
        log_report(
            "StreamingChatService.stream_chat_from_user_prompt.handle",
            {
                "request_id": handle.request_id,
                "assistant_message_id": handle.assistant_message_id,
                "session_id": handle.session_id,
                "conversation_id": handle.conversation_id,
                "provider": handle.provider,
                "model": handle.model,
                "started_at": handle.started_at,
                "cancelled": handle.cancel_event.is_set(),
            },
        )

        # 步骤 7：先对外发 started 事件，声明流式生命周期开始。
        started_event = {
            "request_id": request_id,
            "session_id": normalized_session_id,
            "conversation_id": conversation_scope,
            "assistant_message_id": assistant_message_id,
            "provider": llm_request.provider,
            "model": llm_request.model,
            "created_at": now_utc_iso(),
        }
        stream_event_count += 1
        yield {"event": "response.started", "data": started_event}

        last_emit_at = perf_counter()

        # 步骤 8：消费 provider 流式 chunk。
        # 在循环内持续处理：取消检查、超时检查、心跳、delta 推送、done 收口标记。
        try:
            stream_iterator = provider.stream_chat(llm_request)
            for chunk in stream_iterator:
                log_report("StreamingChatService.stream_chat_from_user_prompt.chunk", chunk)

                now = perf_counter()
                # 8.1 显式取消优先级最高：命中后立即跳出循环，进入 cancelled 收口。
                if handle.cancel_event.is_set():
                    cancelled = True
                    status = "cancelled"
                    break

                # 8.2 超时保护：超过阈值则按 failed 收口。
                if now - started_at > timeout_seconds:
                    status = "failed"
                    error_code = "stream_timeout"
                    error_message = "流式请求超时。"
                    break

                # 8.3 心跳：在长时间没有业务事件输出时发 heartbeat 保活连接。
                if now - last_emit_at >= heartbeat_interval:
                    stream_event_count += 1
                    yield {
                        "event": "response.heartbeat",
                        "data": {
                            "request_id": request_id,
                            "assistant_message_id": assistant_message_id,
                            "ts": now_utc_iso(),
                        },
                    }
                    last_emit_at = now

                # 8.4 消费 chunk：累计文本与 sequence，记录 finish_reason/usage。
                partial_output, sequence = self._consume_chunk(
                    chunk=chunk,
                    partial_output=partial_output,
                    sequence=sequence,
                )
                log_report("StreamingChatService.stream_chat_from_user_prompt.consume_chunk",
                           dict(partial_output=partial_output, sequence=sequence))

                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
                if chunk.usage is not None:
                    usage = chunk.usage

                # 8.5 有 delta 时：更新上下文中的 streaming 消息，并对外发 response.delta。
                if chunk.delta:
                    if normalized_session_id:
                        self._context_manager.update_assistant_stream_delta(
                            session_id=normalized_session_id,
                            conversation_id=conversation_scope,
                            assistant_message_id=assistant_message_id,
                            delta=chunk.delta,
                        )
                    stream_event_count += 1
                    yield {
                        "event": "response.delta",
                        "data": {
                            "request_id": request_id,
                            "assistant_message_id": assistant_message_id,
                            "delta": chunk.delta,
                            "sequence": sequence,
                        },
                    }
                    last_emit_at = perf_counter()

                # 8.6 done 为真表示上游自然结束，进入 completed 收口分支。
                if chunk.done:
                    status = "completed"
                    break
            else:
                # 兼容分支：若迭代自然结束但未显式 done，也按 completed 处理。
                status = "completed"
        except (
                ProviderConfigurationError,
                ProviderNotImplementedError,
                StreamNotImplementedError,
        ) as exc:
            status = "failed"
            error_code = type(exc).__name__
            error_message = str(exc)
        except ProviderInvocationError as exc:
            status = "failed"
            error_code = type(exc).__name__
            error_message = str(exc)
        except Exception as exc:  # pragma: no cover - 运行时兜底
            status = "failed"
            error_code = type(exc).__name__
            error_message = str(exc)
        finally:
            # 步骤 9：无论成功/失败/取消，最终都要从注册表移除，避免“僵尸任务”。
            self._cancellation_registry.unregister(handle)

        # 步骤 10：取消收口。
        # 只更新消息状态与部分输出，不进入标准 completed memory pipeline。
        if cancelled:
            if normalized_session_id:
                self._context_manager.finalize_assistant_message(
                    session_id=normalized_session_id,
                    conversation_id=conversation_scope,
                    assistant_message_id=assistant_message_id,
                    status="cancelled",
                    content=partial_output,
                    error_code="cancelled_by_request",
                )
            stream_event_count += 1
            yield {
                "event": "response.cancelled",
                "data": {
                    "request_id": request_id,
                    "assistant_message_id": assistant_message_id,
                    "status": "cancelled",
                    "partial_output_chars": len(partial_output),
                    "trace": self._build_stream_trace(
                        request_id=request_id,
                        session_id=normalized_session_id,
                        conversation_id=conversation_scope,
                        assistant_message_id=assistant_message_id,
                        provider=llm_request.provider,
                        model=llm_request.model,
                        status="cancelled",
                        finish_reason=finish_reason,
                        started_at=started_at,
                        stream_event_count=stream_event_count,
                        cancelled=True,
                        error_code=None,
                    )
                    if stream_options["stream_emit_trace"]
                    else None,
                },
            }
            return

        # 步骤 11：失败收口。
        # 写回 failed 状态与错误码，不进入标准 completed memory pipeline。
        if status == "failed":
            if normalized_session_id:
                self._context_manager.finalize_assistant_message(
                    session_id=normalized_session_id,
                    conversation_id=conversation_scope,
                    assistant_message_id=assistant_message_id,
                    status="failed",
                    content=partial_output,
                    error_code=error_code,
                )
            stream_event_count += 1
            yield {
                "event": "response.error",
                "data": {
                    "request_id": request_id,
                    "assistant_message_id": assistant_message_id,
                    "status": "failed",
                    "error_code": error_code or "stream_failed",
                    "message": error_message or "流式响应失败。",
                    "trace": self._build_stream_trace(
                        request_id=request_id,
                        session_id=normalized_session_id,
                        conversation_id=conversation_scope,
                        assistant_message_id=assistant_message_id,
                        provider=llm_request.provider,
                        model=llm_request.model,
                        status="failed",
                        finish_reason=finish_reason,
                        started_at=started_at,
                        stream_event_count=stream_event_count,
                        cancelled=False,
                        error_code=error_code,
                    )
                    if stream_options["stream_emit_trace"]
                    else None,
                },
            }
            return

        # 步骤 12：完成收口（completed）。
        # 先把最终 assistant 内容与状态落盘，再触发 Phase 4 标准 memory update 闭环。
        if normalized_session_id:
            self._context_manager.finalize_assistant_message(
                session_id=normalized_session_id,
                conversation_id=conversation_scope,
                assistant_message_id=assistant_message_id,
                status="completed",
                content=partial_output,
                finish_reason=finish_reason,
            )
            self._context_manager.update_after_stream_completion(
                session_id=normalized_session_id,
                conversation_id=conversation_scope,
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
                memory_config=self._app_config.context_memory_config,
            )

        # 步骤 13：对外发 completed 事件，包含 finish_reason/usage/trace/latency。
        stream_event_count += 1
        yield {
            "event": "response.completed",
            "data": {
                "request_id": request_id,
                "assistant_message_id": assistant_message_id,
                "status": "completed",
                "finish_reason": finish_reason or "stop",
                "usage": self._usage_to_dict(usage) if stream_options["stream_emit_usage"] else None,
                "latency_ms": round((perf_counter() - started_at) * 1000, 2),
                "trace": self._build_stream_trace(
                    request_id=request_id,
                    session_id=normalized_session_id,
                    conversation_id=conversation_scope,
                    assistant_message_id=assistant_message_id,
                    provider=llm_request.provider,
                    model=llm_request.model,
                    status="completed",
                    finish_reason=finish_reason,
                    started_at=started_at,
                    stream_event_count=stream_event_count,
                    cancelled=False,
                    error_code=None,
                )
                if stream_options["stream_emit_trace"]
                else None,
            },
        }

    def cancel_stream(self, cancel_request: ChatCancelRequest) -> dict[str, object]:
        if not self._app_config.streaming_config.stream_cancel_enabled:
            raise ServiceNotImplementedError("当前环境未开启流式取消能力。")

        result = self._cancellation_registry.cancel(
            request_id=normalize_optional_text(cancel_request.request_id),
            assistant_message_id=normalize_optional_text(cancel_request.assistant_message_id),
            session_id=normalize_optional_text(cancel_request.session_id),
            conversation_id=normalize_optional_text(cancel_request.conversation_id),
        )
        log_report("StreamingChatService.cancel_stream", result)
        return result

    def _resolve_stream_options(self, stream_options: ChatStreamOptions | None) -> dict[str, Any]:
        default_config = self._app_config.streaming_config
        if stream_options is None:
            return {
                "stream_heartbeat_interval_seconds": default_config.stream_heartbeat_interval_seconds,
                "stream_request_timeout_seconds": default_config.stream_request_timeout_seconds,
                "stream_emit_usage": default_config.stream_emit_usage,
                "stream_emit_trace": default_config.stream_emit_trace,
            }

        return {
            "stream_heartbeat_interval_seconds": (
                stream_options.stream_heartbeat_interval_seconds
                if stream_options.stream_heartbeat_interval_seconds is not None
                else default_config.stream_heartbeat_interval_seconds
            ),
            "stream_request_timeout_seconds": (
                stream_options.stream_request_timeout_seconds
                if stream_options.stream_request_timeout_seconds is not None
                else default_config.stream_request_timeout_seconds
            ),
            "stream_emit_usage": (
                stream_options.stream_emit_usage
                if stream_options.stream_emit_usage is not None
                else default_config.stream_emit_usage
            ),
            "stream_emit_trace": (
                stream_options.stream_emit_trace
                if stream_options.stream_emit_trace is not None
                else default_config.stream_emit_trace
            ),
        }

    @staticmethod
    def _consume_chunk(
            *,
            chunk: LLMStreamChunk,
            partial_output: str,
            sequence: int,
    ) -> tuple[str, int]:
        next_partial_output = partial_output
        next_sequence = sequence
        if chunk.delta:
            next_partial_output = f"{next_partial_output}{chunk.delta}"
            next_sequence = chunk.sequence if chunk.sequence > 0 else sequence + 1
        return next_partial_output, next_sequence

    @staticmethod
    def _usage_to_dict(usage: LLMUsage | None) -> dict[str, Any] | None:
        if usage is None:
            return None
        return asdict(usage)

    @staticmethod
    def _build_stream_trace(
            *,
            request_id: str,
            session_id: str | None,
            conversation_id: str,
            assistant_message_id: str,
            provider: str | None,
            model: str | None,
            status: str,
            finish_reason: str | None,
            started_at: float,
            stream_event_count: int,
            cancelled: bool,
            error_code: str | None,
    ) -> dict[str, Any]:
        finished_at = perf_counter()
        return {
            "request_id": request_id,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "assistant_message_id": assistant_message_id,
            "streaming": True,
            "stream_event_count": stream_event_count,
            "stream_started_at": started_at,
            "stream_finished_at": finished_at,
            "status": status,
            "finish_reason": finish_reason,
            "provider": provider,
            "model": model,
            "latency_ms": round((finished_at - started_at) * 1000, 2),
            "cancelled": cancelled,
            "error_code": error_code,
        }


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
