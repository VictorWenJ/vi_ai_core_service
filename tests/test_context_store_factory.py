from __future__ import annotations

import unittest
from unittest.mock import patch

from app.config import AppConfig, ConfigError, ContextStorageConfig
from app.context.stores.factory import build_context_store
from app.context.stores.in_memory import InMemoryContextStore


class ContextStoreFactoryTests(unittest.TestCase):
    def test_memory_backend_builds_in_memory_store(self) -> None:
        config = AppConfig(
            context_storage_config=ContextStorageConfig(backend="memory"),
        )

        store = build_context_store(config)

        self.assertIsInstance(store, InMemoryContextStore)

    def test_redis_backend_can_fallback_to_memory_when_enabled(self) -> None:
        config = AppConfig(
            context_storage_config=ContextStorageConfig(
                backend="redis",
                allow_memory_fallback=True,
            ),
        )

        with patch("app.context.stores.factory.RedisContextStore", side_effect=RuntimeError("redis down")):
            store = build_context_store(config)

        self.assertIsInstance(store, InMemoryContextStore)

    def test_redis_backend_raises_when_fallback_disabled(self) -> None:
        config = AppConfig(
            context_storage_config=ContextStorageConfig(
                backend="redis",
                allow_memory_fallback=False,
            ),
        )

        with patch("app.context.stores.factory.RedisContextStore", side_effect=RuntimeError("redis down")):
            with self.assertRaises(ConfigError):
                build_context_store(config)
