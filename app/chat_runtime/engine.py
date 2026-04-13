"""聊天运行时统一执行引擎。"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict
from time import perf_counter
from typing import TYPE_CHECKING, Any, Callable
from uuid import uuid4

from app.api.schemas import ChatRequest
from app.chat_runtime.hooks import HookDecision, HookHandler, build_default_hook_registry
from app.chat_runtime.models import (
    RuntimeStreamOptions,
    RuntimeTurnContext,
    RuntimeTurnRequest,
    RuntimeTurnResult,
)
from app.chat_runtime.trace import ExecutionTrace
from app.chat_runtime.workflows import (
    DEFAULT_CHAT_HOOKS,
    DEFAULT_CHAT_SKILLS,
    DEFAULT_CHAT_STEP_HOOKS,
    DEFAULT_CHAT_WORKFLOW,
)
from app.config import AppConfig
from app.context.manager import ContextManager
from app.context.models import normalize_conversation_scope, now_utc_iso
from app.observability.log_until import log_report
from app.providers.chat.base import (
    ProviderConfigurationError,
    ProviderInvocationError,
    ProviderNotImplementedError,
    StreamNotImplementedError,
)
from app.providers.chat.registry import ProviderRegistry
from app.rag.models import RetrievalResult
from app.rag.runtime import RAGRuntime
from app.schemas.llm_response import LLMStreamChunk

if TYPE_CHECKING:
    from app.services.request_assembler import ChatRequestAssembler

StepHandler = Callable[[RuntimeTurnContext, bool], Iterator[dict[str, Any]] | None]


class ChatRuntimeBlockedError(ValueError):
    """运行时被 Hook 阻断时抛出。"""


class ChatRuntimeEngine:
    """统一 chat 与 chat_stream 主链路语义的执行引擎。"""

    def __init__(
        self,
        *,
        app_config: AppConfig,
        provider_registry: ProviderRegistry,
        context_manager: ContextManager,
        request_assembler: ChatRequestAssembler,
        rag_runtime: RAGRuntime,
        workflow_name: str = "default_chat",
        workflow: list[str] | None = None,
        hooks: dict[str, list[str]] | None = None,
        step_hooks: dict[str, list[str]] | None = None,
        skills: list[str] | None = None,
        hook_registry: dict[str, HookHandler] | None = None,
    ) -> None:
        self._app_config = app_config
        self._provider_registry = provider_registry
        self._context_manager = context_manager
        self._request_assembler = request_assembler
        self._rag_runtime = rag_runtime
        self._workflow_name = workflow_name

        self._workflow = list(workflow or DEFAULT_CHAT_WORKFLOW)
        self._hooks = {
            event_name: list(hook_names)
            for event_name, hook_names in (hooks or DEFAULT_CHAT_HOOKS).items()
        }
        self._step_hooks = {
            event_name: list(hook_names)
            for event_name, hook_names in (step_hooks or DEFAULT_CHAT_STEP_HOOKS).items()
        }
        self._skills = list(skills or DEFAULT_CHAT_SKILLS)

        # Step Registry：统一维护步骤名到实现函数映射。
        self._step_registry: dict[str, StepHandler] = {
            "normalize_scope": self._normalize_scope,
            "retrieve_knowledge": self._retrieve_knowledge,
            "assemble_llm_request": self._assemble_llm_request,
            "normalize_llm_request": self._normalize_llm_request,
            "select_provider": self._select_provider,
            "invoke_model": self._invoke_model,
            "persist_context": self._persist_context,
            "finalize_trace": self._finalize_trace,
        }
        # Hook Registry：统一维护 hook 名到处理函数映射。
        self._hook_registry = hook_registry or build_default_hook_registry()

    def run_sync(self, request: RuntimeTurnRequest) -> RuntimeTurnResult:
        runtime_ctx = self._build_runtime_context(request=request, stream=False)
        try:
            for _ in self._run_workflow(runtime_ctx=runtime_ctx, stream=False):
                pass
        except Exception as exc:
            self._run_hooks(
                "on_error",
                runtime_ctx,
                {
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise

        return RuntimeTurnResult(
            response_text=runtime_ctx.response_text,
            citations=list(runtime_ctx.citations),
            provider=runtime_ctx.selected_provider_name or self._app_config.default_provider,
            model=runtime_ctx.selected_model,
            usage=runtime_ctx.usage,
            finish_reason=runtime_ctx.finish_reason,
            retrieval_trace=runtime_ctx.retrieval_trace,
            trace=runtime_ctx.trace,
            metadata=dict(runtime_ctx.llm_response.metadata if runtime_ctx.llm_response else {}),
            raw_response=(
                dict(runtime_ctx.llm_response.raw_response)
                if runtime_ctx.llm_response and runtime_ctx.llm_response.raw_response
                else None
            ),
        )

    def run_stream(self, request: RuntimeTurnRequest) -> Iterator[dict[str, Any]]:
        runtime_ctx = self._build_runtime_context(request=request, stream=True)

        try:
            for stream_event in self._run_workflow(runtime_ctx=runtime_ctx, stream=True):
                yield stream_event
        except Exception as exc:
            runtime_ctx.status = "failed"
            runtime_ctx.error_code = type(exc).__name__
            runtime_ctx.error_message = str(exc)
            self._run_hooks(
                "on_error",
                runtime_ctx,
                {
                    "error_type": runtime_ctx.error_code,
                    "error_message": runtime_ctx.error_message,
                },
            )
            runtime_ctx.trace.complete(
                provider=runtime_ctx.selected_provider_name,
                model=runtime_ctx.selected_model,
                finish_reason=runtime_ctx.finish_reason,
                error_type=runtime_ctx.error_code,
            )
            yield self._build_error_event(runtime_ctx)
            return

        if runtime_ctx.status == "cancelled":
            yield self._build_cancelled_event(runtime_ctx)
            return
        if runtime_ctx.status == "failed":
            self._run_hooks(
                "on_error",
                runtime_ctx,
                {
                    "error_type": runtime_ctx.error_code,
                    "error_message": runtime_ctx.error_message,
                },
            )
            yield self._build_error_event(runtime_ctx)
            return
        yield self._build_completed_event(runtime_ctx)

    def _build_runtime_context(
        self,
        *,
        request: RuntimeTurnRequest,
        stream: bool,
    ) -> RuntimeTurnContext:
        trace = ExecutionTrace.create(workflow_name=self._workflow_name, stream=stream)
        return RuntimeTurnContext(
            request=request,
            workflow_name=self._workflow_name,
            trace=trace,
            skills=list(self._skills),
        )

    def _run_workflow(
        self,
        *,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> Iterator[dict[str, Any]]:
        self._run_hooks(
            "before_request",
            runtime_ctx,
            {"request_id": runtime_ctx.request.request_id},
        )
        for step_name in self._workflow:
            maybe_stream_iterator = self._run_step(
                step_name=step_name,
                runtime_ctx=runtime_ctx,
                stream=stream,
            )
            if stream and maybe_stream_iterator is not None:
                yield from maybe_stream_iterator

    def _run_step(
        self,
        *,
        step_name: str,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> Iterator[dict[str, Any]] | None:
        try:
            step_handler = self._step_registry[step_name]
        except KeyError as exc:
            raise RuntimeError(f"未知 workflow step: {step_name}") from exc

        self._run_hooks(
            f"before_step:{step_name}",
            runtime_ctx,
            {"step_name": step_name},
            step_name=step_name,
        )

        started_perf_seconds = perf_counter()
        try:
            result = step_handler(runtime_ctx, stream)
            runtime_ctx.trace.record_step(
                step_name=step_name,
                status="succeeded",
                latency_ms=round((perf_counter() - started_perf_seconds) * 1000, 2),
            )
        except Exception as exc:
            runtime_ctx.trace.record_step(
                step_name=step_name,
                status="failed",
                latency_ms=round((perf_counter() - started_perf_seconds) * 1000, 2),
                error_type=type(exc).__name__,
            )
            raise

        self._run_hooks(
            f"after_step:{step_name}",
            runtime_ctx,
            {"step_name": step_name},
            step_name=step_name,
        )
        return result

    def _run_hooks(
        self,
        event_name: str,
        runtime_ctx: RuntimeTurnContext,
        payload: dict[str, Any] | None = None,
        *,
        step_name: str | None = None,
    ) -> dict[str, Any]:
        mutable_payload = dict(payload or {})
        hook_names = [
            *self._hooks.get(event_name, []),
            *self._step_hooks.get(event_name, []),
        ]
        for hook_name in hook_names:
            hook_handler = self._hook_registry.get(hook_name)
            if hook_handler is None:
                runtime_ctx.trace.record_hook(
                    event_name=event_name,
                    hook_name=hook_name,
                    action="warn",
                    message="hook_not_found",
                )
                continue

            decision = hook_handler(
                hook_ctx=self._build_hook_context(
                    event_name=event_name,
                    step_name=step_name,
                    workflow_name=runtime_ctx.workflow_name,
                ),
                runtime_ctx=runtime_ctx,
                payload=mutable_payload,
            )
            self._apply_hook_decision(
                runtime_ctx=runtime_ctx,
                event_name=event_name,
                hook_name=hook_name,
                decision=decision,
                payload=mutable_payload,
            )
        return mutable_payload

    @staticmethod
    def _build_hook_context(
        *,
        event_name: str,
        step_name: str | None,
        workflow_name: str,
    ):
        from app.chat_runtime.hooks import HookContext

        return HookContext(
            event_name=event_name,
            step_name=step_name,
            workflow_name=workflow_name,
        )

    def _apply_hook_decision(
        self,
        *,
        runtime_ctx: RuntimeTurnContext,
        event_name: str,
        hook_name: str,
        decision: HookDecision,
        payload: dict[str, Any],
    ) -> None:
        runtime_ctx.trace.record_hook(
            event_name=event_name,
            hook_name=hook_name,
            action=decision.action,
            message=decision.message,
        )
        if decision.action == "mutate":
            payload.update(decision.payload)
            return
        if decision.action == "block":
            raise ChatRuntimeBlockedError(decision.message or f"hook '{hook_name}' blocked")

    def _normalize_scope(
        self,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> None:
        request = runtime_ctx.request
        request.stream = stream
        request.request_id = request.request_id or f"req_{uuid4()}"
        request.stream_options = resolve_stream_options(
            app_config=self._app_config,
            request_stream_options=request.stream_options,
        )
        runtime_ctx.normalized_session_id = request.session_id
        runtime_ctx.normalized_conversation_id = normalize_conversation_scope(request.conversation_id)
        runtime_ctx.user_message_id = request.user_message_id or f"um_{uuid4()}"
        runtime_ctx.assistant_message_id = request.assistant_message_id or f"am_{uuid4()}"

    def _retrieve_knowledge(
        self,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> None:
        del stream
        retrieval_filter = _extract_retrieval_filter(runtime_ctx.request.metadata)
        retrieval_result = self._rag_runtime.retrieve_for_chat(
            query_text=runtime_ctx.request.user_prompt,
            metadata_filter=retrieval_filter,
        )
        runtime_ctx.retrieval_result = retrieval_result
        runtime_ctx.citations = list(retrieval_result.citations)
        runtime_ctx.trace.retrieval_enabled = bool(
            getattr(self._rag_runtime, "enabled", retrieval_result.trace.status != "disabled")
        )
        runtime_ctx.trace.retrieval_hit_count = retrieval_result.trace.hit_count
        self._run_hooks(
            "after_retrieval",
            runtime_ctx,
            retrieval_result.trace.to_dict(),
        )

    def _assemble_llm_request(
        self,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> None:
        request = runtime_ctx.request
        chat_request = ChatRequest(
            user_prompt=request.user_prompt,
            provider=request.provider_override,
            model=request.model_override,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system_prompt,
            stream=stream,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            request_id=request.request_id,
            metadata=dict(request.metadata),
        )
        retrieval_result = runtime_ctx.retrieval_result or RetrievalResult.disabled(
            query_text=request.user_prompt,
            top_k=self._app_config.rag_config.retrieval_top_k,
        )
        runtime_ctx.llm_request = self._request_assembler.assemble_from_user_prompt(
            request=chat_request,
            context_manager=self._context_manager,
            knowledge_block=retrieval_result.knowledge_block,
        )
        runtime_ctx.llm_request.metadata["retrieval"] = retrieval_result.trace.to_dict()

    def _normalize_llm_request(
        self,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> None:
        if runtime_ctx.llm_request is None:
            raise RuntimeError("llm_request 未初始化，无法执行 normalize_llm_request。")
        runtime_ctx.normalized_llm_request = self._request_assembler.normalize_request(
            runtime_ctx.llm_request,
            provider_registry=self._provider_registry,
            allow_stream=stream,
        )
        runtime_ctx.selected_provider_name = runtime_ctx.normalized_llm_request.provider
        runtime_ctx.selected_model = runtime_ctx.normalized_llm_request.model
        context_assembly = runtime_ctx.normalized_llm_request.metadata.get("context_assembly")
        if isinstance(context_assembly, dict):
            runtime_ctx.trace.context_message_count = int(
                context_assembly.get("serialized_message_count", 0)
            )

    def _select_provider(
        self,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> None:
        del stream
        normalized_llm_request = runtime_ctx.normalized_llm_request
        if normalized_llm_request is None:
            raise RuntimeError("normalized_llm_request 未初始化，无法执行 select_provider。")
        provider_name = normalized_llm_request.provider or self._app_config.default_provider
        runtime_ctx.selected_provider = self._provider_registry.get_provider(provider_name)
        runtime_ctx.selected_provider_name = provider_name
        runtime_ctx.selected_model = normalized_llm_request.model
        self._run_hooks(
            "before_model_call",
            runtime_ctx,
            {"provider": provider_name, "model": normalized_llm_request.model},
        )

    def _invoke_model(
        self,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> Iterator[dict[str, Any]] | None:
        if stream:
            return self._invoke_model_stream(runtime_ctx)
        self._invoke_model_sync(runtime_ctx)
        return None

    def _invoke_model_sync(self, runtime_ctx: RuntimeTurnContext) -> None:
        provider = runtime_ctx.selected_provider
        normalized_llm_request = runtime_ctx.normalized_llm_request
        if provider is None or normalized_llm_request is None:
            raise RuntimeError("provider 或 normalized_llm_request 未初始化。")

        llm_response = provider.chat(normalized_llm_request)
        runtime_ctx.llm_response = llm_response
        runtime_ctx.response_text = llm_response.content
        runtime_ctx.usage = llm_response.usage
        runtime_ctx.finish_reason = llm_response.finish_reason
        runtime_ctx.status = "completed"
        runtime_ctx.selected_provider_name = llm_response.provider
        runtime_ctx.selected_model = llm_response.model or normalized_llm_request.model

        hook_payload = self._run_hooks(
            "after_model_call",
            runtime_ctx,
            {"response_text": runtime_ctx.response_text},
        )
        mutated_response_text = hook_payload.get("response_text")
        if isinstance(mutated_response_text, str):
            runtime_ctx.response_text = mutated_response_text

    def _invoke_model_stream(self, runtime_ctx: RuntimeTurnContext) -> Iterator[dict[str, Any]]:
        provider = runtime_ctx.selected_provider
        normalized_llm_request = runtime_ctx.normalized_llm_request
        if provider is None or normalized_llm_request is None:
            raise RuntimeError("provider 或 normalized_llm_request 未初始化。")

        self._prepare_stream_context(runtime_ctx)
        runtime_ctx.status = "streaming"

        runtime_ctx.stream_event_count += 1
        yield {
            "event": "response.started",
            "data": {
                "request_id": runtime_ctx.request.request_id,
                "session_id": runtime_ctx.normalized_session_id,
                "conversation_id": runtime_ctx.normalized_conversation_id,
                "assistant_message_id": runtime_ctx.assistant_message_id,
                "provider": runtime_ctx.selected_provider_name,
                "model": runtime_ctx.selected_model,
                "created_at": now_utc_iso(),
            },
        }

        options = runtime_ctx.request.stream_options
        if options is None:
            raise RuntimeError("stream_options 未初始化。")
        timeout_seconds = options.stream_request_timeout_seconds
        heartbeat_interval_seconds = options.stream_heartbeat_interval_seconds
        last_emit_at = perf_counter()

        try:
            for chunk in provider.stream_chat(normalized_llm_request):
                now = perf_counter()
                if runtime_ctx.request.cancel_event is not None and runtime_ctx.request.cancel_event.is_set():
                    runtime_ctx.status = "cancelled"
                    runtime_ctx.finish_reason = "cancelled"
                    break

                if now - runtime_ctx.stream_started_perf_seconds > timeout_seconds:
                    runtime_ctx.status = "failed"
                    runtime_ctx.error_code = "stream_timeout"
                    runtime_ctx.error_message = "流式请求超时。"
                    break

                if now - last_emit_at >= heartbeat_interval_seconds:
                    runtime_ctx.stream_event_count += 1
                    yield {
                        "event": "response.heartbeat",
                        "data": {
                            "request_id": runtime_ctx.request.request_id,
                            "assistant_message_id": runtime_ctx.assistant_message_id,
                            "ts": now_utc_iso(),
                        },
                    }
                    last_emit_at = now

                runtime_ctx.partial_output, runtime_ctx.stream_sequence = self._consume_chunk(
                    chunk=chunk,
                    partial_output=runtime_ctx.partial_output,
                    sequence=runtime_ctx.stream_sequence,
                )
                if chunk.finish_reason:
                    runtime_ctx.finish_reason = chunk.finish_reason
                if chunk.usage is not None:
                    runtime_ctx.usage = chunk.usage

                if chunk.delta:
                    if runtime_ctx.normalized_session_id and runtime_ctx.stream_placeholder_created:
                        self._context_manager.update_assistant_stream_delta(
                            session_id=runtime_ctx.normalized_session_id,
                            conversation_id=runtime_ctx.normalized_conversation_id,
                            assistant_message_id=runtime_ctx.assistant_message_id or "",
                            delta=chunk.delta,
                        )
                    runtime_ctx.stream_event_count += 1
                    yield {
                        "event": "response.delta",
                        "data": {
                            "request_id": runtime_ctx.request.request_id,
                            "assistant_message_id": runtime_ctx.assistant_message_id,
                            "delta": chunk.delta,
                            "sequence": runtime_ctx.stream_sequence,
                        },
                    }
                    last_emit_at = perf_counter()

                if chunk.done:
                    runtime_ctx.status = "completed"
                    break
            else:
                runtime_ctx.status = "completed"
        except (
            ProviderConfigurationError,
            ProviderNotImplementedError,
            StreamNotImplementedError,
            ProviderInvocationError,
        ) as exc:
            runtime_ctx.status = "failed"
            runtime_ctx.error_code = type(exc).__name__
            runtime_ctx.error_message = str(exc)
        except Exception as exc:  # pragma: no cover - 兜底保护分支
            runtime_ctx.status = "failed"
            runtime_ctx.error_code = type(exc).__name__
            runtime_ctx.error_message = str(exc)

        runtime_ctx.response_text = runtime_ctx.partial_output
        hook_payload = self._run_hooks(
            "after_model_call",
            runtime_ctx,
            {
                "status": runtime_ctx.status,
                "response_text": runtime_ctx.response_text,
            },
        )
        mutated_response_text = hook_payload.get("response_text")
        if isinstance(mutated_response_text, str):
            runtime_ctx.response_text = mutated_response_text
            runtime_ctx.partial_output = mutated_response_text

        if runtime_ctx.status == "completed":
            self._run_hooks(
                "after_stream_completed",
                runtime_ctx,
                {"request_id": runtime_ctx.request.request_id},
            )

    def _prepare_stream_context(self, runtime_ctx: RuntimeTurnContext) -> None:
        if not runtime_ctx.normalized_session_id:
            return
        retrieval_trace = runtime_ctx.retrieval_trace
        message_metadata = {
            "request_id": runtime_ctx.request.request_id,
            "conversation_id": runtime_ctx.normalized_conversation_id,
            "provider": runtime_ctx.selected_provider_name,
            "model": runtime_ctx.selected_model,
            "retrieval_status": retrieval_trace.status if retrieval_trace else "disabled",
            "citation_count": len(runtime_ctx.citations),
        }
        self._context_manager.append_user_message(
            session_id=runtime_ctx.normalized_session_id,
            conversation_id=runtime_ctx.normalized_conversation_id,
            content=runtime_ctx.request.user_prompt,
            metadata=message_metadata,
            message_id=runtime_ctx.user_message_id,
        )
        self._context_manager.create_assistant_placeholder(
            session_id=runtime_ctx.normalized_session_id,
            conversation_id=runtime_ctx.normalized_conversation_id,
            assistant_message_id=runtime_ctx.assistant_message_id,
            metadata=message_metadata,
        )
        self._context_manager.finalize_assistant_message(
            session_id=runtime_ctx.normalized_session_id,
            conversation_id=runtime_ctx.normalized_conversation_id,
            assistant_message_id=runtime_ctx.assistant_message_id or "",
            status="streaming",
            content="",
        )
        runtime_ctx.stream_placeholder_created = True

    def _persist_context(
        self,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> None:
        if not runtime_ctx.normalized_session_id:
            return

        if stream:
            if not runtime_ctx.stream_placeholder_created:
                return
            if runtime_ctx.status == "completed":
                self._context_manager.finalize_assistant_message(
                    session_id=runtime_ctx.normalized_session_id,
                    conversation_id=runtime_ctx.normalized_conversation_id,
                    assistant_message_id=runtime_ctx.assistant_message_id or "",
                    status="completed",
                    content=runtime_ctx.response_text,
                    finish_reason=runtime_ctx.finish_reason,
                )
                self._context_manager.update_after_stream_completion(
                    session_id=runtime_ctx.normalized_session_id,
                    conversation_id=runtime_ctx.normalized_conversation_id,
                    user_message_id=runtime_ctx.user_message_id or "",
                    assistant_message_id=runtime_ctx.assistant_message_id or "",
                    memory_config=self._app_config.context_memory_config,
                )
                return

            if runtime_ctx.status == "cancelled":
                self._context_manager.finalize_assistant_message(
                    session_id=runtime_ctx.normalized_session_id,
                    conversation_id=runtime_ctx.normalized_conversation_id,
                    assistant_message_id=runtime_ctx.assistant_message_id or "",
                    status="cancelled",
                    content=runtime_ctx.response_text,
                    error_code="cancelled_by_request",
                )
                return

            self._context_manager.finalize_assistant_message(
                session_id=runtime_ctx.normalized_session_id,
                conversation_id=runtime_ctx.normalized_conversation_id,
                assistant_message_id=runtime_ctx.assistant_message_id or "",
                status="failed",
                content=runtime_ctx.response_text,
                error_code=runtime_ctx.error_code,
            )
            return

        retrieval_trace = runtime_ctx.retrieval_trace
        self._context_manager.update_after_chat_turn(
            session_id=runtime_ctx.normalized_session_id,
            conversation_id=runtime_ctx.request.conversation_id,
            user_content=runtime_ctx.request.user_prompt,
            assistant_content=runtime_ctx.response_text,
            metadata={
                "conversation_id": runtime_ctx.request.conversation_id,
                "request_id": runtime_ctx.request.request_id,
                "provider": runtime_ctx.selected_provider_name,
                "model": runtime_ctx.selected_model,
                "retrieval_status": retrieval_trace.status if retrieval_trace else "disabled",
                "citation_count": len(runtime_ctx.citations),
            },
            memory_config=self._app_config.context_memory_config,
        )

    def _finalize_trace(
        self,
        runtime_ctx: RuntimeTurnContext,
        stream: bool,
    ) -> None:
        del stream
        error_type = runtime_ctx.error_code if runtime_ctx.status == "failed" else None
        runtime_ctx.trace.complete(
            provider=runtime_ctx.selected_provider_name,
            model=runtime_ctx.selected_model,
            finish_reason=runtime_ctx.finish_reason,
            error_type=error_type,
        )
        if runtime_ctx.status == "completed" and runtime_ctx.finish_reason is None:
            runtime_ctx.finish_reason = "stop"
        log_report("chat_runtime.trace", runtime_ctx.trace.to_dict())

    def _build_completed_event(self, runtime_ctx: RuntimeTurnContext) -> dict[str, Any]:
        options = runtime_ctx.request.stream_options
        if options is None:
            raise RuntimeError("stream_options 未初始化。")
        return {
            "event": "response.completed",
            "data": {
                "request_id": runtime_ctx.request.request_id,
                "assistant_message_id": runtime_ctx.assistant_message_id,
                "status": "completed",
                "finish_reason": runtime_ctx.finish_reason or "stop",
                "usage": asdict(runtime_ctx.usage) if options.stream_emit_usage and runtime_ctx.usage else None,
                "latency_ms": runtime_ctx.trace.latency_ms,
                "citations": [citation.to_dict() for citation in runtime_ctx.citations],
                "trace": self._build_stream_trace_payload(runtime_ctx) if options.stream_emit_trace else None,
            },
        }

    def _build_error_event(self, runtime_ctx: RuntimeTurnContext) -> dict[str, Any]:
        options = runtime_ctx.request.stream_options
        if options is None:
            raise RuntimeError("stream_options 未初始化。")
        return {
            "event": "response.error",
            "data": {
                "request_id": runtime_ctx.request.request_id,
                "assistant_message_id": runtime_ctx.assistant_message_id,
                "status": "failed",
                "error_code": runtime_ctx.error_code or "stream_failed",
                "message": runtime_ctx.error_message or "流式响应失败。",
                "trace": self._build_stream_trace_payload(runtime_ctx) if options.stream_emit_trace else None,
            },
        }

    def _build_cancelled_event(self, runtime_ctx: RuntimeTurnContext) -> dict[str, Any]:
        options = runtime_ctx.request.stream_options
        if options is None:
            raise RuntimeError("stream_options 未初始化。")
        return {
            "event": "response.cancelled",
            "data": {
                "request_id": runtime_ctx.request.request_id,
                "assistant_message_id": runtime_ctx.assistant_message_id,
                "status": "cancelled",
                "partial_output_chars": len(runtime_ctx.response_text),
                "trace": self._build_stream_trace_payload(runtime_ctx) if options.stream_emit_trace else None,
            },
        }

    def _build_stream_trace_payload(self, runtime_ctx: RuntimeTurnContext) -> dict[str, Any]:
        retrieval_trace = runtime_ctx.retrieval_trace
        return {
            **runtime_ctx.trace.to_dict(),
            "request_id": runtime_ctx.request.request_id,
            "session_id": runtime_ctx.normalized_session_id,
            "conversation_id": runtime_ctx.normalized_conversation_id,
            "assistant_message_id": runtime_ctx.assistant_message_id,
            "streaming": True,
            "stream_event_count": runtime_ctx.stream_event_count,
            "status": runtime_ctx.status,
            "error_code": runtime_ctx.error_code,
            "retrieval": retrieval_trace.to_dict() if retrieval_trace else None,
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


def resolve_stream_options(
    *,
    app_config: AppConfig,
    request_stream_options: RuntimeStreamOptions | None,
) -> RuntimeStreamOptions:
    if request_stream_options is not None:
        return request_stream_options
    default_config = app_config.streaming_config
    return RuntimeStreamOptions(
        stream_heartbeat_interval_seconds=default_config.stream_heartbeat_interval_seconds,
        stream_request_timeout_seconds=default_config.stream_request_timeout_seconds,
        stream_emit_usage=default_config.stream_emit_usage,
        stream_emit_trace=default_config.stream_emit_trace,
    )


def _extract_retrieval_filter(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None
    retrieval_filter = metadata.get("retrieval_filter")
    if not isinstance(retrieval_filter, dict):
        return None
    return dict(retrieval_filter)
