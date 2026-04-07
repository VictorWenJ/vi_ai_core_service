from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from app.config import AppConfig, ConfigError


class ConfigTests(unittest.TestCase):
    def test_from_env_loads_provider_configs(self) -> None:
        env = {
            "LLM_DEFAULT_PROVIDER": "deepseek",
            "LLM_TIMEOUT_SECONDS": "45",
            "OPENAI_API_KEY": "openai-key",
            "DEEPSEEK_API_KEY": "deepseek-key",
            "DEEPSEEK_DEFAULT_MODEL": "deepseek-chat",
            "CONTEXT_MAX_TOKEN_BUDGET": "1500",
            "CONTEXT_TRUNCATION_TOKEN_BUDGET": "1200",
            "CONTEXT_SUMMARY_ENABLED": "true",
            "CONTEXT_SUMMARY_MAX_CHARS": "280",
            "CONTEXT_FALLBACK_BEHAVIOR": "summary_then_drop_oldest",
        }

        with patch.dict(os.environ, env, clear=True):
            config = AppConfig.from_env(load_dotenv_file=False)

        self.assertEqual(config.default_provider, "deepseek")
        self.assertEqual(config.timeout_seconds, 45.0)
        self.assertEqual(config.get_provider_config("openai").api_key, "openai-key")
        self.assertEqual(
            config.get_provider_config("deepseek").base_url,
            "https://api.deepseek.com",
        )
        self.assertEqual(
            config.get_provider_config("deepseek").default_model,
            "deepseek-chat",
        )
        self.assertEqual(config.context.max_token_budget, 1500)
        self.assertEqual(config.context.truncation_token_budget, 1200)
        self.assertTrue(config.context.summary_enabled)
        self.assertEqual(config.context.summary_max_chars, 280)

    def test_invalid_default_provider_raises(self) -> None:
        with patch.dict(os.environ, {"LLM_DEFAULT_PROVIDER": "unknown"}, clear=True):
            with self.assertRaises(ConfigError):
                AppConfig.from_env(load_dotenv_file=False)

    def test_invalid_timeout_raises(self) -> None:
        with patch.dict(os.environ, {"LLM_TIMEOUT_SECONDS": "abc"}, clear=True):
            with self.assertRaises(ConfigError):
                AppConfig.from_env(load_dotenv_file=False)

    def test_invalid_context_budgets_raise(self) -> None:
        env = {
            "CONTEXT_MAX_TOKEN_BUDGET": "100",
            "CONTEXT_TRUNCATION_TOKEN_BUDGET": "200",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ConfigError):
                AppConfig.from_env(load_dotenv_file=False)

    def test_from_env_can_load_values_from_dotenv_file(self) -> None:
        dotenv_content = "\n".join(
            [
                "LLM_DEFAULT_PROVIDER=deepseek",
                "LLM_TIMEOUT_SECONDS=30",
                "DEEPSEEK_API_KEY=dotenv-key",
                "DEEPSEEK_DEFAULT_MODEL=deepseek-chat",
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = os.path.join(temp_dir, ".env")
            with open(dotenv_path, "w", encoding="utf-8") as file:
                file.write(dotenv_content)

            with patch.dict(os.environ, {}, clear=True):
                config = AppConfig.from_env(dotenv_path=dotenv_path)

        self.assertEqual(config.default_provider, "deepseek")
        self.assertEqual(config.timeout_seconds, 30.0)
        self.assertEqual(config.get_provider_config("deepseek").api_key, "dotenv-key")
        self.assertEqual(
            config.get_provider_config("deepseek").default_model,
            "deepseek-chat",
        )

    def test_environment_variables_override_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = os.path.join(temp_dir, ".env")
            with open(dotenv_path, "w", encoding="utf-8") as file:
                file.write("DEEPSEEK_DEFAULT_MODEL=dotenv-model\n")

            with patch.dict(os.environ, {"DEEPSEEK_DEFAULT_MODEL": "env-model"}, clear=True):
                config = AppConfig.from_env(dotenv_path=dotenv_path)

        self.assertEqual(
            config.get_provider_config("deepseek").default_model,
            "env-model",
        )
