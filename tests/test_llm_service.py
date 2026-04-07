from __future__ import annotations

import unittest

from app.api.schemas import ChatRequest
from app.config import AppConfig, ProviderConfig
from app.context.models import ContextMessage, ContextWindow
from app.providers.base import BaseLLMProvider, ProviderNotImplementedError
from app.providers.registry import ProviderRegistry
from app.schemas.llm_request import LLMMessage, LLMRequest
from app.schemas.llm_response import LLMResponse
from app.services.errors import (
    ServiceConfigurationError,
    ServiceNotImplementedError,
    ServiceValidationError,
)
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService


class FakeProvider(BaseLLMProvider):
    def __init__(self, provider_config: ProviderConfig) -> None:
        super().__init__(provider_config)
        self.last_request: LLMRequest | None = None

    def chat(self, request: LLMRequest) -> LLMResponse:
        self.last_request = request
        return LLMResponse(
            content=f"handled-by-{self.provider_name}",
            provider=self.provider_name,
            model=request.model,
        )


class FakeOpenAIProvider(FakeProvider):
    provider_name = "openai"


class FakeDeepSeekProvider(FakeProvider):
    provider_name = "deepseek"


class FakeGeminiProvider(FakeProvider):
    provider_name = "gemini"

    def chat(self, request: LLMRequest) -> LLMResponse:
        raise ProviderNotImplementedError("Gemini scaffold")


class FakeContextManager:
    def __init__(self) -> None:
        self.last_get_session_id: str | None = None
        self.user_appends: list[tuple[str, str]] = []
        self.assistant_appends: list[tuple[str, str]] = []
        self._window = ContextWindow(
            session_id="session-1",
            messages=[ContextMessage(role="assistant", content="history")],
        )

    def get_context(self, session_id: str) -> ContextWindow:
        self.last_get_session_id = session_id
        return self._window

    def append_user_message(
        self,
        session_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> ContextWindow:
        del metadata
        self.user_appends.append((session_id, content))
        return self._window

    def append_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> ContextWindow:
        del metadata
        self.assistant_appends.append((session_id, content))
        return self._window

    def reset_session(self, session_id: str) -> ContextWindow:
        self._window = ContextWindow(session_id=session_id, messages=[])
        return self._window

    def reset_conversation(
        self,
        session_id: str,
        conversation_id: str | None = None,
    ) -> ContextWindow:
        del conversation_id
        self._window = ContextWindow(session_id=session_id, messages=[])
        return self._window


class LLMServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        providers = {
            "openai": ProviderConfig(name="openai", api_key="k1", default_model="gpt-test"),
            "deepseek": ProviderConfig(
                name="deepseek",
                api_key="k2",
                default_model="deepseek-chat",
                base_url="https://api.deepseek.com",
            ),
            "gemini": ProviderConfig(name="gemini"),
            "doubao": ProviderConfig(name="doubao"),
            "tongyi": ProviderConfig(name="tongyi"),
        }
        self.config = AppConfig(
            default_provider="openai",
            timeout_seconds=60.0,
            providers=providers,
        )
        self.providers = {
            "openai": FakeOpenAIProvider(providers["openai"]),
            "deepseek": FakeDeepSeekProvider(providers["deepseek"]),
            "gemini": FakeGeminiProvider(providers["gemini"]),
        }
        self.registry = ProviderRegistry(
            config=self.config,
            provider_overrides=self.providers,
        )
        self.service = LLMService(config=self.config, registry=self.registry)

    def test_chat_uses_default_provider_and_default_model(self) -> None:
        response = self.service.chat(
            LLMRequest(messages=[LLMMessage(role="user", content="hello")])
        )

        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.model, "gpt-test")
        self.assertEqual(self.providers["openai"].last_request.model, "gpt-test")

    def test_chat_routes_to_requested_provider(self) -> None:
        response = self.service.chat(
            LLMRequest(
                provider="deepseek",
                messages=[LLMMessage(role="user", content="hello")],
            )
        )

        self.assertEqual(response.provider, "deepseek")
        self.assertEqual(response.model, "deepseek-chat")
        self.assertEqual(self.providers["deepseek"].last_request.provider, "deepseek")

    def test_chat_injects_system_prompt_via_prompt_service(self) -> None:
        self.service.chat(
            LLMRequest(
                messages=[LLMMessage(role="user", content="hello")],
                system_prompt="be concise",
            )
        )

        roles = [message.role for message in self.providers["openai"].last_request.messages]
        self.assertEqual(roles, ["system", "user"])

    def test_chat_rejects_missing_messages(self) -> None:
        with self.assertRaises(ServiceValidationError):
            self.service.chat(LLMRequest())

    def test_chat_rejects_stream_requests(self) -> None:
        with self.assertRaises(ServiceNotImplementedError):
            self.service.chat(
                LLMRequest(
                    messages=[LLMMessage(role="user", content="hello")],
                    stream=True,
                )
            )

    def test_chat_rejects_unsupported_provider(self) -> None:
        with self.assertRaises(ServiceConfigurationError):
            self.service.chat(
                LLMRequest(
                    provider="unknown-provider",
                    messages=[LLMMessage(role="user", content="hello")],
                )
            )

    def test_scaffold_provider_surfaces_not_implemented(self) -> None:
        with self.assertRaises(ServiceNotImplementedError) as context:
            self.service.chat(
                LLMRequest(
                    provider="gemini",
                    model="gemini-test",
                    messages=[LLMMessage(role="user", content="hello")],
                )
            )
        self.assertIsInstance(context.exception.__cause__, ProviderNotImplementedError)

    def test_unused_provider_missing_key_does_not_break_default_provider(self) -> None:
        providers = {
            "openai": ProviderConfig(name="openai", api_key="k1", default_model="gpt-test"),
            "deepseek": ProviderConfig(
                name="deepseek",
                api_key=None,
                default_model="deepseek-chat",
                base_url="https://api.deepseek.com",
            ),
            "gemini": ProviderConfig(name="gemini"),
            "doubao": ProviderConfig(name="doubao"),
            "tongyi": ProviderConfig(name="tongyi"),
        }
        config = AppConfig(
            default_provider="openai",
            timeout_seconds=60.0,
            providers=providers,
        )
        registry = ProviderRegistry(
            config=config,
            provider_overrides={"openai": FakeOpenAIProvider(providers["openai"])},
        )
        service = LLMService(config=config, registry=registry)

        response = service.chat(
            LLMRequest(messages=[LLMMessage(role="user", content="hello")])
        )

        self.assertEqual(response.provider, "openai")

    def test_chat_from_user_prompt_uses_context_and_persists_turns(self) -> None:
        fake_context_manager = FakeContextManager()
        service = LLMService(
            config=self.config,
            registry=self.registry,
            prompt_service=PromptService(),
            context_manager=fake_context_manager,
        )

        response = service.chat_from_user_prompt(
            ChatRequest(
                user_prompt="new question",
                session_id="session-1",
                provider="openai",
                temperature=0.2,
                max_tokens=128,
                stream=False,
            )
        )

        self.assertEqual(response.provider, "openai")
        self.assertEqual(fake_context_manager.last_get_session_id, "session-1")
        self.assertEqual(fake_context_manager.user_appends, [("session-1", "new question")])
        self.assertEqual(len(fake_context_manager.assistant_appends), 1)

        sent_messages = self.providers["openai"].last_request.messages
        sent_roles = [message.role for message in sent_messages]
        self.assertEqual(sent_roles, ["system", "assistant", "user"])
        self.assertEqual(self.providers["openai"].last_request.temperature, 0.2)
        self.assertEqual(self.providers["openai"].last_request.max_tokens, 128)
        used_context_history = self.providers["openai"].last_request.metadata["used_context_history"]
        self.assertTrue(used_context_history["enabled"])
        self.assertEqual(used_context_history["raw_message_count"], 1)
        self.assertEqual(used_context_history["selected_message_count"], 1)
        self.assertEqual(used_context_history["dropped_message_count"], 0)
        self.assertEqual(used_context_history["serialized_message_count"], 1)
        self.assertNotIn("messages", used_context_history)

    def test_chat_from_user_prompt_without_session_does_not_access_context(self) -> None:
        fake_context_manager = FakeContextManager()
        service = LLMService(
            config=self.config,
            registry=self.registry,
            prompt_service=PromptService(),
            context_manager=fake_context_manager,
        )

        response = service.chat_from_user_prompt(
            ChatRequest(
                user_prompt="stateless question",
                provider="openai",
                stream=False,
            )
        )

        self.assertEqual(response.provider, "openai")
        self.assertIsNone(fake_context_manager.last_get_session_id)
        self.assertEqual(fake_context_manager.user_appends, [])
        self.assertEqual(fake_context_manager.assistant_appends, [])

    def test_reset_context_clears_session_window(self) -> None:
        fake_context_manager = FakeContextManager()
        service = LLMService(
            config=self.config,
            registry=self.registry,
            prompt_service=PromptService(),
            context_manager=fake_context_manager,
        )

        result = service.reset_context(session_id="session-1")

        self.assertEqual(result["session_id"], "session-1")
        self.assertEqual(result["scope"], "session")
        self.assertEqual(result["remaining_message_count"], 0)
