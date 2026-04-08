"""上下文存储后端构建器。"""

from __future__ import annotations

from app.config import AppConfig, ConfigError
from app.context.stores.base import BaseContextStore
from app.context.stores.in_memory import InMemoryContextStore
from app.context.stores.redis_store import RedisContextStore
from app.observability.log_until import log_report


def build_context_store(app_config: AppConfig) -> BaseContextStore:
    storage_config = app_config.context_storage_config
    backend = storage_config.backend

    if backend == "memory":
        log_report(
            "context.store.factory.build",
            {
                "backend": "memory",
                "mode": "direct",
            },
        )
        return InMemoryContextStore()

    if backend != "redis":
        raise ConfigError(f"不支持的 context store backend: {backend}。")

    try:
        store = RedisContextStore(
            redis_url=storage_config.redis_url,
            key_prefix=storage_config.key_prefix,
            session_ttl_seconds=storage_config.session_ttl_seconds,
        )
        store.ping()
        log_report(
            "context.store.factory.build",
            {
                "backend": "redis",
                "mode": "direct",
                "key_prefix": storage_config.key_prefix,
                "session_ttl_seconds": storage_config.session_ttl_seconds,
            },
        )
        return store
    except Exception as exc:
        if not storage_config.allow_memory_fallback:
            raise ConfigError(
                "RedisContextStore 初始化失败，且已禁用回退到内存存储。"
            ) from exc

        log_report(
            "context.store.factory.build",
            {
                "backend": "memory",
                "mode": "fallback",
                "reason": str(exc),
            },
        )
        return InMemoryContextStore()
