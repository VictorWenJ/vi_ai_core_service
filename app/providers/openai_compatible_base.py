"""Shared base for OpenAI-compatible chat providers."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.config import ProviderConfig
from app.observability.events import log_provider_request, log_provider_response
from app.observability.exception_logging import log_exception
from app.observability.logging_setup import get_logger, get_logging_settings
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

_provider_logger = get_logger("providers.openai_compatible")


class OpenAICompatibleBaseProvider(BaseLLMProvider):
    """Base implementation for providers that expose an OpenAI-compatible API."""

    provider_name = "openai_compatible"

    def __init__(
        self,
        provider_config: ProviderConfig,
        client: Any | None = None,
    ) -> None:
        super().__init__(provider_config)
        self._client = client or self._build_client()

    def chat(self, request: LLMRequest) -> LLMResponse:
        self.ensure_non_streaming(request)

        if not request.model:
            raise ProviderConfigurationError(
                f"Provider '{self.provider_name}' requires a model."
            )

        payload = {
            "model": request.model,
            "messages": self._to_vendor_messages(request),
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        payload_preview = None
        if get_logging_settings().log_provider_payload:
            payload_preview = self._build_payload_preview(request)

        log_provider_request(
            provider=self.provider_name,
            model=request.model,
            endpoint=self.provider_config.base_url,
            stream=False,
            message_count=len(request.messages),
            has_attachments=bool(request.attachments),
            has_tools=bool(request.tools),
            has_response_format=bool(request.response_format),
            timeout_seconds=self.provider_config.timeout_seconds,
            payload_preview=payload_preview,
        )

        started_at = perf_counter()
        try:
            vendor_response = self._client.chat.completions.create(**payload)
        except Exception as exc:  # pragma: no cover - depends on vendor runtime
            log_exception(
                exc,
                event="provider.request.error",
                message=f"Provider '{self.provider_name}' request failed.",
                logger=_provider_logger,
                provider=self.provider_name,
                model=request.model,
                endpoint=self.provider_config.base_url,
                latency_ms=round((perf_counter() - started_at) * 1000, 2),
                error_type=type(exc).__name__,
            )
            raise ProviderInvocationError(
                f"Provider '{self.provider_name}' request failed: {exc}"
            ) from exc

        response = self._to_response(vendor_response)
        log_provider_response(
            provider=self.provider_name,
            model=response.model,
            finish_reason=response.finish_reason,
            usage=response.usage,
            latency_ms=(perf_counter() - started_at) * 1000,
            success=True,
        )
        return response

    def _build_client(self):
        if OpenAI is None:
            raise ProviderConfigurationError(
                "Missing dependency 'openai'. Install it with 'pip install openai'."
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

    def _build_payload_preview(self, request: LLMRequest) -> dict[str, Any]:
        message_preview = [
            {
                "role": message.role,
                "content_preview": _truncate(message.content, 160),
            }
            for message in request.messages[:3]
        ]
        return {
            "message_preview": message_preview,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "message_count": len(request.messages),
        }


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."
