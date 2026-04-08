"""面向上下文 token 策略的分词器适配器。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.context.models import ContextMessage

DEFAULT_MESSAGE_OVERHEAD_TOKENS = 4


class BaseTokenCounter(ABC):
    """与 Provider 无关的 token 计数契约。"""

    name: str = "tokenizer.base"

    def __init__(
        self,
        *,
        message_overhead_tokens: int = DEFAULT_MESSAGE_OVERHEAD_TOKENS,
    ) -> None:
        if message_overhead_tokens <= 0:
            raise ValueError("message_overhead_tokens 必须大于 0。")
        self._message_overhead_tokens = message_overhead_tokens

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

    # 每条消息的固定 token 额外开销（不含正文内容）。
    # 当前为工程近似值，可通过配置或子类覆写调整。
    def message_overhead_tokens(self, role: str) -> int:
        del role
        return self._message_overhead_tokens

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
    """基于 Unicode 字符计数的回退型确定性分词器。"""

    name = "tokenizer.character_fallback"

    def __init__(
        self,
        *,
        message_overhead_tokens: int = DEFAULT_MESSAGE_OVERHEAD_TOKENS,
    ) -> None:
        super().__init__(message_overhead_tokens=message_overhead_tokens)

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
    """依赖可用时基于 tiktoken 的 token 计数器。"""

    name = "tokenizer.tiktoken_cl100k_base"

    def __init__(
        self,
        encoding_name: str = "cl100k_base",
        *,
        message_overhead_tokens: int = DEFAULT_MESSAGE_OVERHEAD_TOKENS,
    ) -> None:
        super().__init__(message_overhead_tokens=message_overhead_tokens)
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


def build_default_token_counter(
    *,
    message_overhead_tokens: int = DEFAULT_MESSAGE_OVERHEAD_TOKENS,
) -> BaseTokenCounter:
    try:
        return TiktokenTokenCounter(message_overhead_tokens=message_overhead_tokens)
    except Exception:
        return CharacterTokenCounter(message_overhead_tokens=message_overhead_tokens)
