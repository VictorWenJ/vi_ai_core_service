"""流式会话取消注册表。"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event, Lock
from time import perf_counter


@dataclass
class StreamTaskHandle:
    # 流式请求唯一 ID。
    request_id: str
    # 对应 assistant 消息 ID，用于消息维度取消。
    assistant_message_id: str
    # 会话 ID。
    session_id: str
    # 会话作用域 ID。
    conversation_id: str
    # 请求使用的 provider 名称；缺省时为空。
    provider: str | None
    # 请求使用的模型名称；缺省时为空。
    model: str | None
    # 任务启动时间戳，基于 perf_counter，单位为秒。
    started_at: float
    # 取消信号事件对象；被置位表示任务应中止。
    cancel_event: Event


class CancellationRegistry:
    """维护进行中流式任务，提供显式 cancel 能力。"""

    def __init__(self) -> None:
        self._lock = Lock()
        self._request_index: dict[str, StreamTaskHandle] = {}
        self._assistant_index: dict[str, StreamTaskHandle] = {}

    def register(
        self,
        *,
        request_id: str,
        assistant_message_id: str,
        session_id: str,
        conversation_id: str,
        provider: str | None,
        model: str | None,
    ) -> StreamTaskHandle:
        handle = StreamTaskHandle(
            request_id=request_id,
            assistant_message_id=assistant_message_id,
            session_id=session_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            started_at=perf_counter(),
            cancel_event=Event(),
        )
        # 上锁写入登记簿
        # 进入临界区：注册表是共享可变状态，写入时必须加锁，避免并发覆盖或索引不一致。
        with self._lock:
            # 主索引：按 request_id 建立映射，便于通过请求维度快速定位流式任务。
            self._request_index[request_id] = handle
            # 辅助索引：按 assistant_message_id 建立映射，便于通过消息维度执行取消。
            self._assistant_index[assistant_message_id] = handle
        return handle

    def unregister(self, handle: StreamTaskHandle) -> None:
        with self._lock:
            existing_by_request = self._request_index.get(handle.request_id)
            if existing_by_request is handle:
                self._request_index.pop(handle.request_id, None)

            existing_by_assistant = self._assistant_index.get(handle.assistant_message_id)
            if existing_by_assistant is handle:
                self._assistant_index.pop(handle.assistant_message_id, None)

    def cancel(
        self,
        *,
        request_id: str | None,
        assistant_message_id: str | None,
        session_id: str | None,
        conversation_id: str | None,
    ) -> dict[str, object]:
        with self._lock:
            handle = self._resolve_handle(
                request_id=request_id,
                assistant_message_id=assistant_message_id,
            )
            if handle is None:
                return {
                    "found": False,
                    "cancelled": False,
                    "request_id": request_id,
                    "assistant_message_id": assistant_message_id,
                }

            if session_id and session_id != handle.session_id:
                return {
                    "found": False,
                    "cancelled": False,
                    "request_id": request_id,
                    "assistant_message_id": assistant_message_id,
                }
            if conversation_id and conversation_id != handle.conversation_id:
                return {
                    "found": False,
                    "cancelled": False,
                    "request_id": request_id,
                    "assistant_message_id": assistant_message_id,
                }

            already_set = handle.cancel_event.is_set()
            handle.cancel_event.set()

            return {
                "found": True,
                "cancelled": not already_set,
                "already_cancelled": already_set,
                "request_id": handle.request_id,
                "assistant_message_id": handle.assistant_message_id,
                "session_id": handle.session_id,
                "conversation_id": handle.conversation_id,
            }

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._request_index)

    def _resolve_handle(
        self,
        *,
        request_id: str | None,
        assistant_message_id: str | None,
    ) -> StreamTaskHandle | None:
        if request_id:
            handle = self._request_index.get(request_id)
            if handle is not None:
                return handle
        if assistant_message_id:
            return self._assistant_index.get(assistant_message_id)
        return None
