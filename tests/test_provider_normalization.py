from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.config import ProviderConfig
from app.providers.chat.deepseek_provider import DeepSeekProvider
from app.providers.chat.openai_provider import OpenAIProvider
from app.schemas.llm_request import LLMMessage, LLMRequest


class FakeCompletionsClient:
    def __init__(self, response) -> None:
        self.response = response
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self.response


class FakeChatClient:
    def __init__(self, response) -> None:
        self.completions = FakeCompletionsClient(response)


class FakeOpenAIClient:
    def __init__(self, response) -> None:
        self.chat = FakeChatClient(response)


def build_vendor_response(model: str, content: str):
    return SimpleNamespace(
        id="resp_123",
        object="chat.completion",
        created=1234567890,
        model=model,
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason="stop",
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=11,
            completion_tokens=7,
            total_tokens=18,
        ),
    )


def build_vendor_stream_chunks():
    return [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="你"),
                    finish_reason=None,
                )
            ],
            usage=None,
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="好"),
                    finish_reason=None,
                )
            ],
            usage=None,
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=""),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2, total_tokens=5),
        ),
    ]


class ProviderNormalizationTests(unittest.TestCase):
    def test_openai_provider_normalizes_request_and_response(self) -> None:
        fake_client = FakeOpenAIClient(build_vendor_response("gpt-test", "hello"))
        provider = OpenAIProvider(
            provider_config=ProviderConfig(name="openai", api_key="key"),
            client=fake_client,
        )
        request = LLMRequest(
            provider="openai",
            model="gpt-test",
            messages=[
                LLMMessage(role="system", content="be concise"),
                LLMMessage(role="user", content="hello"),
            ],
            temperature=0.2,
            max_tokens=128,
        )

        response = provider.chat(request)
        vendor_kwargs = fake_client.chat.completions.last_kwargs

        self.assertEqual(vendor_kwargs["model"], "gpt-test")
        self.assertEqual(vendor_kwargs["stream"], False)
        self.assertEqual(vendor_kwargs["temperature"], 0.2)
        self.assertEqual(vendor_kwargs["max_tokens"], 128)
        self.assertEqual(
            vendor_kwargs["messages"],
            [
                {"role": "system", "content": "be concise"},
                {"role": "user", "content": "hello"},
            ],
        )
        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.content, "hello")
        self.assertEqual(response.usage.total_tokens, 18)
        self.assertEqual(response.raw_response["id"], "resp_123")

    def test_deepseek_provider_normalizes_to_deepseek_provider_name(self) -> None:
        fake_client = FakeOpenAIClient(
            build_vendor_response("deepseek-chat", "deepseek response")
        )
        provider = DeepSeekProvider(
            provider_config=ProviderConfig(
                name="deepseek",
                api_key="key",
                base_url="https://api.deepseek.com",
            ),
            client=fake_client,
        )
        request = LLMRequest(
            provider="deepseek",
            model="deepseek-chat",
            messages=[LLMMessage(role="user", content="hello")],
        )

        response = provider.chat(request)

        self.assertEqual(fake_client.chat.completions.last_kwargs["model"], "deepseek-chat")
        self.assertEqual(response.provider, "deepseek")
        self.assertEqual(response.model, "deepseek-chat")
        self.assertEqual(response.content, "deepseek response")

    def test_openai_provider_stream_chat_emits_normalized_chunks(self) -> None:
        fake_client = FakeOpenAIClient(build_vendor_stream_chunks())
        provider = OpenAIProvider(
            provider_config=ProviderConfig(name="openai", api_key="key"),
            client=fake_client,
        )
        request = LLMRequest(
            provider="openai",
            model="gpt-test",
            messages=[LLMMessage(role="user", content="hello")],
            stream=True,
        )

        chunks = list(provider.stream_chat(request))

        self.assertEqual(fake_client.chat.completions.last_kwargs["stream"], True)
        self.assertEqual("".join(chunk.delta for chunk in chunks), "你好")
        self.assertTrue(chunks[-1].done)
        self.assertEqual(chunks[-1].finish_reason, "stop")
