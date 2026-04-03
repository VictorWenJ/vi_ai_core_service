"""Minimal CLI entrypoint for the LLM service."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from app.config import AppConfig
from app.schemas.llm_request import LLMRequest
from app.schemas.llm_response import LLMResponse
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single chat request.")
    parser.add_argument("--provider", type=str, default=None, help="Provider name.")
    parser.add_argument("--model", type=str, default=None, help="Model name.")
    parser.add_argument("--prompt", type=str, required=True, help="User prompt.")
    parser.add_argument("--system", type=str, default=None, help="System prompt.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the normalized response as JSON.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug summaries to stderr.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = AppConfig.from_env()
    if args.debug:
        _debug_print("Config Summary", _build_config_summary(config))

    prompt_service = PromptService()
    llm_service = LLMService(config=config, prompt_service=prompt_service)

    messages = prompt_service.build_messages(
        system_prompt=args.system,
        user_prompt=args.prompt,
    )
    request = LLMRequest(
        provider=args.provider,
        model=args.model,
        messages=messages,
    )

    if args.debug:
        _debug_print("Request Summary", _build_request_summary(request, config))

    response = llm_service.chat(request)

    if args.debug:
        _debug_print("Response Summary", _build_response_summary(response))

    if args.json:
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
        return

    print(response.content)


# python -m app.main --provider deepseek --prompt "hello"
# python -m app.main --provider deepseek --prompt "hello" --json
# python -m app.main --provider deepseek --prompt "hello" --debug
# python -m app.main --provider deepseek --prompt "hello" --json --debug



def _build_config_summary(config: AppConfig) -> dict[str, Any]:
    providers_summary: dict[str, dict[str, Any]] = {}
    for provider_name in sorted(config.providers.keys()):
        provider_config = config.providers[provider_name]
        providers_summary[provider_name] = {
            "has_api_key": bool(provider_config.api_key),
            "default_model": provider_config.default_model,
        }

    return {
        "default_provider": config.default_provider,
        "timeout_seconds": config.timeout_seconds,
        "providers": providers_summary,
    }


def _build_request_summary(request: LLMRequest, config: AppConfig) -> dict[str, Any]:
    provider_name = request.provider or config.default_provider
    provider_config = config.get_provider_config(provider_name)
    model_name = request.model or provider_config.default_model
    last_message = request.messages[-1].content if request.messages else ""

    return {
        "provider": provider_name,
        "model": model_name,
        "message_count": len(request.messages),
        "last_message_preview": _truncate_preview(last_message, 120),
    }


def _build_response_summary(response: LLMResponse) -> dict[str, Any]:
    usage = None
    if response.usage is not None:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    return {
        "provider": response.provider,
        "model": response.model,
        "content_length": len(response.content),
        "finish_reason": response.finish_reason,
        "usage": usage,
    }


def _truncate_preview(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _debug_print(title: str, payload: dict[str, Any]) -> None:
    print(f"[DEBUG] {title}", file=sys.stderr)
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
