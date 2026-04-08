"""OpenAI 兼容聊天 Provider 的共享基类。"""

from __future__ import annotations

from time import perf_counter
import traceback
from typing import Any

from app.config import ProviderConfig
from app.observability.log_until import log_report
from app.providers.base import (
    BaseLLMProvider,
    ProviderConfigurationError,
    ProviderInvocationError,
)
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse, LLMUsage

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime if dependency is missing
    OpenAI = None


class OpenAICompatibleBaseProvider(BaseLLMProvider):
    """面向 OpenAI 兼容 API 的 Provider 基础实现。"""

    provider_name = "openai_compatible"

    def __init__(
        self,
        provider_config: ProviderConfig,
        client: Any | None = None,
    ) -> None:
        super().__init__(provider_config)
        self._client = client or self._build_client()

    def chat(self, llm_request: LLMRequest) -> LLMResponse:
        self.ensure_non_streaming(llm_request)

        if not llm_request.model:
            raise ProviderConfigurationError(
                f"Provider '{self.provider_name}' 需要模型。"
            )

        llm_payload = {
            "model": llm_request.model,
            "messages": self._to_vendor_messages(llm_request),
            "stream": False,
            "temperature": 0.6,
            "max_tokens": 1000,
        }
        if llm_request.temperature is not None:
            llm_payload["temperature"] = llm_request.temperature
        if llm_request.max_tokens is not None:
            llm_payload["max_tokens"] = llm_request.max_tokens

        log_report("OpenAICompatibleBaseProvider.chat.llm_payload", llm_payload)

        started_at = perf_counter()
        try:
            llm_vendor_response = self._client.chat.completions.create(**llm_payload)
            log_report("OpenAICompatibleBaseProvider.chat.llm_vendor_response", llm_vendor_response)
        except Exception as exc:  # pragma: no cover - depends on vendor runtime
            log_report(
                "provider.request.error",
                {
                    "provider": self.provider_name,
                    "model": llm_request.model,
                    "endpoint": self.provider_config.base_url,
                    "latency_ms": round((perf_counter() - started_at) * 1000, 2),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": "".join(
                        traceback.format_exception(type(exc), exc, exc.__traceback__)
                    ),
                },
            )
            raise ProviderInvocationError(
                f"Provider '{self.provider_name}' 请求失败：{exc}"
            ) from exc

        response = self._to_response(llm_vendor_response)
        return response

    def _build_client(self):
        if OpenAI is None:
            raise ProviderConfigurationError(
                "缺少依赖 'openai'。请先执行 'pip install openai'。"
            )

        client_kwargs = {
            "api_key": self.ensure_api_key(),
            "timeout": self.provider_config.timeout_seconds,
        }
        if self.provider_config.base_url:
            client_kwargs["base_url"] = self.provider_config.base_url

        return OpenAI(**client_kwargs)

    def _to_vendor_messages(self, request: LLMRequest) -> list[dict[str, str]]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in request.messages
        ]

    def _to_response(self, vendor_response: Any) -> LLMResponse:
        choice = vendor_response.choices[0]
        usage = getattr(vendor_response, "usage", None)
        response_usage = None
        if usage is not None:
            response_usage = LLMUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", None),
                completion_tokens=getattr(usage, "completion_tokens", None),
                total_tokens=getattr(usage, "total_tokens", None),
            )

        raw_response = {
            key: getattr(vendor_response, key)
            for key in ("id", "object", "created")
            if getattr(vendor_response, key, None) is not None
        } or None

        return LLMResponse(
            content=choice.message.content or "",
            provider=self.provider_name,
            model=getattr(vendor_response, "model", None),
            usage=response_usage,
            finish_reason=getattr(choice, "finish_reason", None),
            metadata={},
            raw_response=raw_response,
        )
