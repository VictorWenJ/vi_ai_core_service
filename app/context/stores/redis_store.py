"""Redis 持久化短期记忆存储实现。"""

from __future__ import annotations

import json
from typing import Any

from app.context.models import (
    ContextMessage,
    ContextWindow,
    RollingSummaryState,
    WorkingMemoryState,
    now_utc_iso,
    normalize_conversation_scope,
)
from app.context.stores.base import BaseContextStore
from app.observability.log_until import log_report


class RedisContextStore(BaseContextStore):
    """基于 Redis 的上下文存储实现。"""

    backend_name = "redis"

    def __init__(
        self,
        *,
        redis_url: str,
        key_prefix: str,
        session_ttl_seconds: int,
        redis_client: Any | None = None,
    ) -> None:
        if not redis_url.strip():
            raise ValueError("redis_url 不能为空。")
        if not key_prefix.strip():
            raise ValueError("key_prefix 不能为空。")
        if session_ttl_seconds <= 0:
            raise ValueError("session_ttl_seconds 必须大于 0。")

        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._session_ttl_seconds = session_ttl_seconds
        self._redis = redis_client or self._build_redis_client(redis_url)

    def ping(self) -> bool:
        return bool(self._redis.ping())

    def get_window(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        scope = normalize_conversation_scope(conversation_id)
        key = self._build_conversation_key(session_id, scope)
        raw_payload = self._redis.get(key)
        if raw_payload is None:
            window = ContextWindow(session_id=session_id, conversation_id=scope)
            log_report(
                "context.store.redis.get_window",
                {
                    "backend": self.backend_name,
                    "session_id": session_id,
                    "conversation_id": scope,
                    "hit": False,
                    "message_count": 0,
                    "ttl_seconds": None,
                },
            )
            return window

        window = self._decode_window(session_id, scope, raw_payload)
        log_report(
            "context.store.redis.get_window",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "conversation_id": scope,
                "hit": True,
                "message_count": window.message_count,
                "ttl_seconds": self._read_ttl_seconds(key),
            },
        )
        return window

    def append_message(
        self,
        session_id: str,
        conversation_id: str | None,
        message: ContextMessage,
    ) -> ContextWindow:
        scope = normalize_conversation_scope(conversation_id)
        window = self.get_window(session_id, scope)
        window.messages.append(message)
        self._save_window(window, scope=scope)
        log_report(
            "context.store.redis.append_message",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "conversation_id": scope,
                "message_count": window.message_count,
                "ttl_seconds": self._session_ttl_seconds,
            },
        )
        return window

    def clear_window(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        scope = normalize_conversation_scope(conversation_id)
        key = self._build_conversation_key(session_id, scope)
        self._redis.delete(key)
        self._redis.srem(self._build_session_index_key(session_id), scope)
        window = ContextWindow(session_id=session_id, conversation_id=scope)
        log_report(
            "context.store.redis.clear_window",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "conversation_id": scope,
                "message_count": 0,
            },
        )
        return window

    def reset_session(self, session_id: str) -> ContextWindow:
        index_key = self._build_session_index_key(session_id)
        scopes = list(self._redis.smembers(index_key) or [])
        delete_keys = [self._build_conversation_key(session_id, scope) for scope in scopes]
        if delete_keys:
            self._redis.delete(*delete_keys)
        self._redis.delete(index_key)
        log_report(
            "context.store.redis.reset_session",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "conversation_count": len(scopes),
            },
        )
        return ContextWindow(session_id=session_id)

    def reset_conversation(
        self,
        session_id: str,
        conversation_id: str | None,
    ) -> ContextWindow:
        scope = normalize_conversation_scope(conversation_id)
        self.clear_window(session_id, scope)
        log_report(
            "context.store.redis.reset_conversation",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "conversation_id": scope,
                "remaining_message_count": 0,
                "ttl_seconds": None,
            },
        )
        return ContextWindow(session_id=session_id, conversation_id=scope)

    def replace_messages(
        self,
        session_id: str,
        conversation_id: str | None,
        messages: list[ContextMessage],
    ) -> ContextWindow:
        scope = normalize_conversation_scope(conversation_id)
        window = self.get_window(session_id, scope)
        window.messages = list(messages)
        if window.messages:
            self._save_window(window, scope=scope)
        else:
            self.clear_window(session_id, scope)
        log_report(
            "context.store.redis.replace_messages",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "conversation_id": scope,
                "message_count": window.message_count,
                "ttl_seconds": self._read_ttl_seconds(
                    self._build_conversation_key(session_id, scope)
                ),
            },
        )
        return window

    def upsert_window(self, window: ContextWindow) -> ContextWindow:
        scope = normalize_conversation_scope(window.conversation_id)
        normalized_window = ContextWindow(
            session_id=window.session_id,
            conversation_id=scope,
            messages=list(window.messages),
            rolling_summary=window.rolling_summary,
            working_memory=window.working_memory,
            runtime_meta=dict(window.runtime_meta),
        )
        if (
            not normalized_window.messages
            and not normalized_window.rolling_summary.has_content
            and not normalized_window.working_memory.non_empty_fields()
        ):
            return self.clear_window(normalized_window.session_id, scope)

        self._save_window(normalized_window, scope=scope)
        return normalized_window

    def _save_window(self, window: ContextWindow, *, scope: str) -> None:
        key = self._build_conversation_key(window.session_id, scope)
        payload = self._encode_window(window)
        self._redis.set(key, payload, ex=self._session_ttl_seconds)
        self._touch_session_index(window.session_id, scope)

    def _touch_session_index(self, session_id: str, scope: str) -> None:
        index_key = self._build_session_index_key(session_id)
        self._redis.sadd(index_key, scope)
        self._redis.expire(index_key, self._session_ttl_seconds)

    def _build_conversation_key(self, session_id: str, scope: str) -> str:
        return f"{self._key_prefix}:session:{session_id}:conversation:{scope}"

    def _build_session_index_key(self, session_id: str) -> str:
        return f"{self._key_prefix}:session:{session_id}:conversations"

    def _encode_window(self, window: ContextWindow) -> str:
        payload = {
            "session_id": window.session_id,
            "conversation_id": window.conversation_id,
            "messages": [self._encode_message(message) for message in window.messages],
            "rolling_summary": {
                "text": window.rolling_summary.text,
                "updated_at": window.rolling_summary.updated_at,
                "source_message_count": window.rolling_summary.source_message_count,
            },
            "working_memory": {
                "active_goal": window.working_memory.active_goal,
                "constraints": list(window.working_memory.constraints),
                "decisions": list(window.working_memory.decisions),
                "open_questions": list(window.working_memory.open_questions),
                "next_step": window.working_memory.next_step,
                "updated_at": window.working_memory.updated_at,
            },
            "runtime_meta": dict(window.runtime_meta),
        }
        return json.dumps(payload, ensure_ascii=False)

    def _decode_window(self, session_id: str, scope: str, raw_payload: str) -> ContextWindow:
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return ContextWindow(session_id=session_id, conversation_id=scope, messages=[])

        raw_messages = payload.get("messages", [])
        messages = [
            self._decode_message(raw_message)
            for raw_message in raw_messages
            if isinstance(raw_message, dict)
        ]
        raw_summary = payload.get("rolling_summary", {})
        rolling_summary = RollingSummaryState(
            text=str(raw_summary.get("text", "")),
            updated_at=raw_summary.get("updated_at"),
            source_message_count=int(raw_summary.get("source_message_count", 0)),
        )
        raw_working_memory = payload.get("working_memory", {})
        working_memory = WorkingMemoryState(
            active_goal=_to_optional_text(raw_working_memory.get("active_goal")),
            constraints=_to_str_list(raw_working_memory.get("constraints")),
            decisions=_to_str_list(raw_working_memory.get("decisions")),
            open_questions=_to_str_list(raw_working_memory.get("open_questions")),
            next_step=_to_optional_text(raw_working_memory.get("next_step")),
            updated_at=_to_optional_text(raw_working_memory.get("updated_at")),
        )
        runtime_meta = payload.get("runtime_meta")
        if not isinstance(runtime_meta, dict):
            runtime_meta = {}
        return ContextWindow(
            session_id=session_id,
            conversation_id=str(payload.get("conversation_id", scope)),
            messages=messages,
            rolling_summary=rolling_summary,
            working_memory=working_memory,
            runtime_meta=runtime_meta,
        )

    @staticmethod
    def _encode_message(message: ContextMessage) -> dict[str, Any]:
        return {
            "role": message.role,
            "content": message.content,
            "metadata": dict(message.metadata),
            "created_at": message.created_at,
        }

    @staticmethod
    def _decode_message(raw_message: dict[str, Any]) -> ContextMessage:
        created_at = raw_message.get("created_at")
        normalized_created_at = (
            str(created_at)
            if isinstance(created_at, str) and created_at
            else now_utc_iso()
        )
        metadata = raw_message.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        return ContextMessage(
            role=str(raw_message.get("role", "")),
            content=str(raw_message.get("content", "")),
            metadata=metadata,
            created_at=normalized_created_at,
        )

    def _read_ttl_seconds(self, key: str) -> int | None:
        try:
            ttl = int(self._redis.ttl(key))
        except Exception:
            return None
        if ttl < 0:
            return None
        return ttl

    @staticmethod
    def _build_redis_client(redis_url: str) -> Any:
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError(
                "缺少依赖 'redis'，请先安装 requirements.txt。"
            ) from exc
        return redis.Redis.from_url(redis_url, decode_responses=True)


def _to_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized_value = str(value).strip()
    return normalized_value or None


def _to_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return result
