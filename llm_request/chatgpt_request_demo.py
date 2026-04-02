#!/usr/bin/env python3
"""Minimal local demo for calling OpenAI GPT-5.4 via the Responses API.

Usage:
  export OPENAI_API_KEY="OPENAI_API_KEY"
  python chatgpt_request_demo.py --prompt "用中文解释什么是 RAG"

Interactive mode:
  python chatgpt_request_demo.py --interactive
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

try:
    from openai import OpenAI
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: openai\n"
        "Install it with: pip install --upgrade openai"
    ) from exc


DEFAULT_MODEL = "gpt-5.4"


def build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is not set.\n"
            "macOS/Linux: export OPENAI_API_KEY='your_api_key'\n"
            "Windows PowerShell: $env:OPENAI_API_KEY='your_api_key'"
        )
    return OpenAI(api_key=api_key)


def ask_once(
    client: OpenAI,
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
) -> str:
    input_payload = []

    if system_prompt:
        input_payload.append(
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            }
        )

    input_payload.append(
        {
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}],
        }
    )

    response = client.responses.create(
        model=model,
        input=input_payload,
    )

    return response.output_text


def run_interactive(client: OpenAI, model: str, system_prompt: Optional[str]) -> None:
    print(f"Interactive mode started. model={model}")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            prompt = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return

        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            print("Bye.")
            return

        try:
            answer = ask_once(client, prompt, model=model, system_prompt=system_prompt)
            print(f"\nAssistant> {answer}\n")
        except Exception as exc:  # broad on purpose for simple demo UX
            print(f"Request failed: {exc}\n", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call OpenAI GPT-5.4 locally with a simple Python script."
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Single prompt to send. If omitted, use --interactive.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Model ID to use. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--system",
        type=str,
        default=None,
        help="Optional system prompt.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive chat mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = build_client()

    if args.prompt:
        answer = ask_once(
            client=client,
            prompt=args.prompt,
            model=args.model,
            system_prompt=args.system,
        )
        print(answer)
        return

    if args.interactive:
        run_interactive(client, model=args.model, system_prompt=args.system)
        return

    raise SystemExit("Provide --prompt \"...\" or use --interactive")


if __name__ == "__main__":
    main()
