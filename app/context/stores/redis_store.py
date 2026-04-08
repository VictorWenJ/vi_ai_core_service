"""Redis 持久化短期记忆存储实现。"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

from app.context.models import ContextMessage, ContextWindow
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

    def get_window(self, session_id: str) -> ContextWindow:
        key = self._build_session_key(session_id)
        raw_payload = self._redis.get(key)
        if raw_payload is None:
            window = ContextWindow(session_id=session_id)
            log_report(
                "context.store.redis.get_window",
                {
                    "backend": self.backend_name,
                    "session_id": session_id,
                    "hit": False,
                    "message_count": 0,
                    "ttl_seconds": None,
                },
            )
            return window

        window = self._decode_window(session_id, raw_payload)
        log_report(
            "context.store.redis.get_window",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "hit": True,
                "message_count": window.message_count,
                "ttl_seconds": self._read_ttl_seconds(key),
            },
        )
        return window

    def append_message(self, session_id: str, message: ContextMessage) -> ContextWindow:
        window = self.get_window(session_id)
        window.messages.append(message)
        self._save_window(window)
        log_report(
            "context.store.redis.append_message",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "message_count": window.message_count,
                "ttl_seconds": self._session_ttl_seconds,
            },
        )
        return window

    def clear_window(self, session_id: str) -> ContextWindow:
        key = self._build_session_key(session_id)
        self._redis.delete(key)
        window = ContextWindow(session_id=session_id)
        log_report(
            "context.store.redis.clear_window",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "message_count": 0,
            },
        )
        return window

    def reset_conversation(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        if conversation_id is None:
            return self.clear_window(session_id)

        window = self.get_window(session_id)
        filtered_messages = [
            message
            for message in window.messages
            if message.metadata.get("conversation_id") != conversation_id
        ]
        window.messages = filtered_messages
        if window.messages:
            self._save_window(window)
        else:
            self._redis.delete(self._build_session_key(session_id))
        log_report(
            "context.store.redis.reset_conversation",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "remaining_message_count": window.message_count,
                "ttl_seconds": self._read_ttl_seconds(self._build_session_key(session_id)),
            },
        )
        return window

    def replace_messages(
        self,
        session_id: str,
        messages: list[ContextMessage],
    ) -> ContextWindow:
        window = ContextWindow(session_id=session_id, messages=list(messages))
        if window.messages:
            self._save_window(window)
        else:
            self._redis.delete(self._build_session_key(session_id))
        log_report(
            "context.store.redis.replace_messages",
            {
                "backend": self.backend_name,
                "session_id": session_id,
                "message_count": window.message_count,
                "ttl_seconds": self._read_ttl_seconds(self._build_session_key(session_id)),
            },
        )
        return window

    def _save_window(self, window: ContextWindow) -> None:
        key = self._build_session_key(window.session_id)
        payload = self._encode_window(window)
        self._redis.set(key, payload, ex=self._session_ttl_seconds)

    def _build_session_key(self, session_id: str) -> str:
        return f"{self._key_prefix}:session:{session_id}"

    def _encode_window(self, window: ContextWindow) -> str:
        payload = {
            "session_id": window.session_id,
            "messages": [self._encode_message(message) for message in window.messages],
        }
        return json.dumps(payload, ensure_ascii=False)

    def _decode_window(self, session_id: str, raw_payload: str) -> ContextWindow:
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return ContextWindow(session_id=session_id, messages=[])

        raw_messages = payload.get("messages", [])
        messages = [
            self._decode_message(raw_message)
            for raw_message in raw_messages
            if isinstance(raw_message, dict)
        ]
        return ContextWindow(session_id=session_id, messages=messages)

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
            else datetime.now(timezone.utc).isoformat()
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
