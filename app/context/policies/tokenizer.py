"""Tokenizer adapters for context token-aware policies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.context.models import ContextMessage


class BaseTokenCounter(ABC):
    """Provider-agnostic token counter contract."""

    name: str = "tokenizer.base"

    @abstractmethod
    def count_text_tokens(self, text: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def truncate_text_to_tokens(
        self,
        text: str,
        max_tokens: int,
        *,
        keep_tail: bool = True,
    ) -> str:
        raise NotImplementedError

    # 每条消息的固定 token 额外开销（不含正文内容）
    def message_overhead_tokens(self, role: str) -> int:
        # 参数当前实现里没用到，只是为了接口统一、避免未使用变量告警。
        del role
        return 4

    def count_message_tokens(self, message: ContextMessage) -> int:
        return self.message_overhead_tokens(message.role) + self.count_text_tokens(
            message.content
        )

    def count_messages_tokens(self, messages: list[ContextMessage]) -> int:
        return sum(self.count_message_tokens(message) for message in messages)

    def truncate_message_content_to_fit(
        self,
        message: ContextMessage,
        max_message_tokens: int,
        *,
        keep_tail: bool = True,
    ) -> str:
        content_budget = max(
            max_message_tokens - self.message_overhead_tokens(message.role),
            0,
        )
        return self.truncate_text_to_tokens(
            message.content,
            content_budget,
            keep_tail=keep_tail,
        )


class CharacterTokenCounter(BaseTokenCounter):
    """Fallback deterministic tokenizer based on unicode character count."""

    name = "tokenizer.character_fallback"

    def count_text_tokens(self, text: str) -> int:
        stripped = text.strip()
        if not stripped:
            return 0
        return len(stripped)

    def truncate_text_to_tokens(
        self,
        text: str,
        max_tokens: int,
        *,
        keep_tail: bool = True,
    ) -> str:
        if max_tokens <= 0:
            return ""
        stripped = text.strip()
        if len(stripped) <= max_tokens:
            return stripped
        if keep_tail:
            return stripped[-max_tokens:]
        return stripped[:max_tokens]


class TiktokenTokenCounter(BaseTokenCounter):
    """Token counter backed by tiktoken when dependency is available."""

    name = "tokenizer.tiktoken_cl100k_base"

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        import tiktoken

        self._encoding = tiktoken.get_encoding(encoding_name)

    def count_text_tokens(self, text: str) -> int:
        stripped = text.strip()
        if not stripped:
            return 0
        return len(self._encoding.encode(stripped))

    def truncate_text_to_tokens(
        self,
        text: str,
        max_tokens: int,
        *,
        keep_tail: bool = True,
    ) -> str:
        if max_tokens <= 0:
            return ""
        stripped = text.strip()
        encoded = self._encoding.encode(stripped)
        if len(encoded) <= max_tokens:
            return stripped
        if keep_tail:
            truncated = encoded[-max_tokens:]
        else:
            truncated = encoded[:max_tokens]
        return self._encoding.decode(truncated).strip()


def build_default_token_counter() -> BaseTokenCounter:
    try:
        return TiktokenTokenCounter()
    except Exception:
        return CharacterTokenCounter()
