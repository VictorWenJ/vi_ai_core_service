from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.config import AppConfig
from app.providers.embeddings.deterministic_provider import DeterministicEmbeddingProvider
from app.providers.embeddings.registry import build_embedding_provider
from app.providers.embeddings.tei_provider import TEIEmbeddingProvider


class EmbeddingProviderRegistryTests(unittest.TestCase):
    def test_build_embedding_provider_returns_tei_provider(self) -> None:
        env = {
            "RAG_EMBEDDING_PROVIDER": "tei",
            "TEI_BASE_URL": "http://localhost:8080",
            "TEI_TIMEOUT_SECONDS": "9",
        }
        with patch.dict(os.environ, env, clear=True):
            app_config = AppConfig.from_env(load_dotenv_file=False)

        provider = build_embedding_provider(app_config)

        self.assertIsInstance(provider, TEIEmbeddingProvider)

    def test_build_embedding_provider_keeps_deterministic_provider(self) -> None:
        env = {
            "RAG_EMBEDDING_PROVIDER": "deterministic",
            "RAG_EMBEDDING_DIMENSION": "128",
        }
        with patch.dict(os.environ, env, clear=True):
            app_config = AppConfig.from_env(load_dotenv_file=False)

        provider = build_embedding_provider(app_config)

        self.assertIsInstance(provider, DeterministicEmbeddingProvider)
        result = provider.embed_texts(["hello"])
        self.assertEqual(result.dimensions, 128)

    def test_build_embedding_provider_keeps_openai_provider_path(self) -> None:
        env = {
            "RAG_EMBEDDING_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env, clear=True):
            app_config = AppConfig.from_env(load_dotenv_file=False)

        with patch("app.providers.embeddings.registry.OpenAIEmbeddingProvider") as mocked_cls:
            mocked_instance = object()
            mocked_cls.return_value = mocked_instance

            provider = build_embedding_provider(app_config)

        self.assertIs(provider, mocked_instance)
        mocked_cls.assert_called_once()
