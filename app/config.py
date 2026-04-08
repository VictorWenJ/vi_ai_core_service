"""集中式应用与 Provider 配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_PROVIDER_NAMES = ("openai", "deepseek", "gemini", "doubao", "tongyi")
SUPPORTED_LOG_FORMATS = ("json",)
SUPPORTED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
SUPPORTED_CONTEXT_FALLBACK_BEHAVIORS = (
    "summary_then_drop_oldest",
    "drop_oldest",
)
SUPPORTED_CONTEXT_STORE_BACKENDS = ("memory", "redis")

DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_LOG_ENABLED = True
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "json"
DEFAULT_LOG_API_PAYLOAD = True
DEFAULT_LOG_PROVIDER_PAYLOAD = True
DEFAULT_CONTEXT_MAX_TOKEN_BUDGET = 1200
DEFAULT_CONTEXT_TRUNCATION_TOKEN_BUDGET = 900
DEFAULT_CONTEXT_SUMMARY_ENABLED = True
DEFAULT_CONTEXT_SUMMARY_MAX_CHARS = 320
DEFAULT_CONTEXT_FALLBACK_BEHAVIOR = "summary_then_drop_oldest"
DEFAULT_CONTEXT_MESSAGE_OVERHEAD_TOKENS = 4
DEFAULT_CONTEXT_STORE_BACKEND = "memory"
DEFAULT_CONTEXT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_CONTEXT_STORE_KEY_PREFIX = "vi_ai_core_service:context"
DEFAULT_CONTEXT_SESSION_TTL_SECONDS = 86400
DEFAULT_CONTEXT_ALLOW_MEMORY_FALLBACK = True
DEFAULT_BASE_URLS: dict[str, str | None] = {
    "openai": None,
    "deepseek": "https://api.deepseek.com",
    "gemini": None,
    "doubao": None,
    "tongyi": None,
}


class ConfigError(ValueError):
    """当应用配置无效时抛出。"""


@dataclass(frozen=True)
class ProviderConfig:
    """单个 Provider 的配置。"""

    name: str
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ObservabilityConfig:
    """可观测性与日志行为配置。"""

    log_enabled: bool = DEFAULT_LOG_ENABLED
    log_level: str = DEFAULT_LOG_LEVEL
    log_format: str = DEFAULT_LOG_FORMAT
    log_api_payload: bool = DEFAULT_LOG_API_PAYLOAD
    log_provider_payload: bool = DEFAULT_LOG_PROVIDER_PAYLOAD


@dataclass(frozen=True)
class ContextPolicyConfig:
    """上下文策略管线行为配置。"""

    # 上下文选窗阶段的最大 token 预算。
    max_token_budget: int = DEFAULT_CONTEXT_MAX_TOKEN_BUDGET
    # 上下文截断阶段的 token 预算（需小于等于 max_token_budget）。
    truncation_token_budget: int = DEFAULT_CONTEXT_TRUNCATION_TOKEN_BUDGET
    # 是否启用确定性 summary/compaction 策略。
    summary_enabled: bool = DEFAULT_CONTEXT_SUMMARY_ENABLED
    # 摘要文本最大字符数，用于限制 summary 消息长度。
    summary_max_chars: int = DEFAULT_CONTEXT_SUMMARY_MAX_CHARS
    # 当摘要后仍超预算时的回退策略。
    fallback_behavior: str = DEFAULT_CONTEXT_FALLBACK_BEHAVIOR
    # 估算消息 token 时每条消息的固定开销（工程近似值，可配置）。
    message_overhead_tokens: int = DEFAULT_CONTEXT_MESSAGE_OVERHEAD_TOKENS


@dataclass(frozen=True)
class ContextStorageConfig:
    """上下文存储后端与生命周期治理配置。"""

    # 上下文存储后端：memory/redis。
    backend: str = DEFAULT_CONTEXT_STORE_BACKEND
    # Redis 连接地址；当 backend=redis 时生效。
    redis_url: str = DEFAULT_CONTEXT_REDIS_URL
    # 会话窗口 TTL（秒）；写入时刷新，用于短期记忆生命周期治理。
    session_ttl_seconds: int = DEFAULT_CONTEXT_SESSION_TTL_SECONDS
    # Redis key 前缀，用于隔离命名空间。
    key_prefix: str = DEFAULT_CONTEXT_STORE_KEY_PREFIX
    # 当 Redis 不可用时是否允许回退到内存存储（建议仅 dev/test 开启）。
    allow_memory_fallback: bool = DEFAULT_CONTEXT_ALLOW_MEMORY_FALLBACK


@dataclass(frozen=True)
class AppConfig:
    """应用顶层配置。"""

    # 默认 provider 名称；当请求未显式指定 provider 时使用。
    default_provider: str = "openai"
    # 全局超时时间（秒）；作为各 provider 的默认超时来源。
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    # provider 配置表，key 为 provider 名称（如 openai/deepseek）。
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    # 可观测性配置（日志开关、级别、格式等）。
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    # 上下文策略配置（token 预算、summary 开关、回退策略等）。
    context_policy_config: ContextPolicyConfig = field(default_factory=ContextPolicyConfig)
    # 上下文存储配置（backend、TTL、key 前缀与回退策略）。
    context_storage_config: ContextStorageConfig = field(default_factory=ContextStorageConfig)

    @classmethod
    def from_env(
        cls,
        load_dotenv_file: bool = True,
        dotenv_path: str | None = None,
    ) -> "AppConfig":
        if load_dotenv_file:
            _load_dotenv(dotenv_path)

        timeout_seconds = _read_float("LLM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
        default_provider = os.getenv("LLM_DEFAULT_PROVIDER", "openai").strip().lower()

        if default_provider not in SUPPORTED_PROVIDER_NAMES:
            raise ConfigError(
                f"不支持的默认 Provider '{default_provider}'。 "
                f"支持的 Provider：{', '.join(SUPPORTED_PROVIDER_NAMES)}。"
            )

        providers = {
            provider_name: ProviderConfig(
                name=provider_name,
                api_key=_read_optional(f"{provider_name.upper()}_API_KEY"),
                base_url=_read_optional(
                    f"{provider_name.upper()}_BASE_URL",
                    default=DEFAULT_BASE_URLS[provider_name],
                ),
                default_model=_read_optional(f"{provider_name.upper()}_DEFAULT_MODEL"),
                timeout_seconds=timeout_seconds,
            )
            for provider_name in SUPPORTED_PROVIDER_NAMES
        }

        observability = ObservabilityConfig(
            log_enabled=_read_bool("LOG_ENABLED", DEFAULT_LOG_ENABLED),
            log_level=_read_log_level("LOG_LEVEL", DEFAULT_LOG_LEVEL),
            log_format=_read_log_format("LOG_FORMAT", DEFAULT_LOG_FORMAT),
            log_api_payload=_read_bool("LOG_API_PAYLOAD", DEFAULT_LOG_API_PAYLOAD),
            log_provider_payload=_read_bool(
                "LOG_PROVIDER_PAYLOAD",
                DEFAULT_LOG_PROVIDER_PAYLOAD,
            ),
        )

        max_token_budget = _read_int(
            "CONTEXT_MAX_TOKEN_BUDGET",
            DEFAULT_CONTEXT_MAX_TOKEN_BUDGET,
        )
        truncation_token_budget = _read_int(
            "CONTEXT_TRUNCATION_TOKEN_BUDGET",
            DEFAULT_CONTEXT_TRUNCATION_TOKEN_BUDGET,
        )
        summary_max_chars = _read_int(
            "CONTEXT_SUMMARY_MAX_CHARS",
            DEFAULT_CONTEXT_SUMMARY_MAX_CHARS,
        )
        if truncation_token_budget > max_token_budget:
            raise ConfigError(
                "CONTEXT_TRUNCATION_TOKEN_BUDGET 必须小于或等于 "
                "CONTEXT_MAX_TOKEN_BUDGET。"
            )

        context = ContextPolicyConfig(
            max_token_budget=max_token_budget,
            truncation_token_budget=truncation_token_budget,
            summary_enabled=_read_bool(
                "CONTEXT_SUMMARY_ENABLED",
                DEFAULT_CONTEXT_SUMMARY_ENABLED,
            ),
            summary_max_chars=summary_max_chars,
            fallback_behavior=_read_context_fallback_behavior(
                "CONTEXT_FALLBACK_BEHAVIOR",
                DEFAULT_CONTEXT_FALLBACK_BEHAVIOR,
            ),
            message_overhead_tokens=_read_int(
                "CONTEXT_MESSAGE_OVERHEAD_TOKENS",
                DEFAULT_CONTEXT_MESSAGE_OVERHEAD_TOKENS,
            ),
        )

        context_store_key_prefix = _read_optional(
            "CONTEXT_STORE_KEY_PREFIX",
            default=DEFAULT_CONTEXT_STORE_KEY_PREFIX,
        )
        if not context_store_key_prefix:
            raise ConfigError("环境变量 'CONTEXT_STORE_KEY_PREFIX' 不能为空。")
        context_storage = ContextStorageConfig(
            backend=_read_context_store_backend(
                "CONTEXT_STORE_BACKEND",
                DEFAULT_CONTEXT_STORE_BACKEND,
            ),
            redis_url=_read_optional(
                "CONTEXT_REDIS_URL",
                default=DEFAULT_CONTEXT_REDIS_URL,
            ) or DEFAULT_CONTEXT_REDIS_URL,
            session_ttl_seconds=_read_int(
                "CONTEXT_SESSION_TTL_SECONDS",
                DEFAULT_CONTEXT_SESSION_TTL_SECONDS,
            ),
            key_prefix=context_store_key_prefix,
            allow_memory_fallback=_read_bool(
                "CONTEXT_ALLOW_MEMORY_FALLBACK",
                DEFAULT_CONTEXT_ALLOW_MEMORY_FALLBACK,
            ),
        )

        return cls(
            default_provider=default_provider,
            timeout_seconds=timeout_seconds,
            providers=providers,
            observability=observability,
            context_policy_config=context,
            context_storage_config=context_storage,
        )

    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        normalized_name = provider_name.strip().lower()
        try:
            return self.providers[normalized_name]
        except KeyError as exc:
            raise ConfigError(
                f"不支持的 Provider '{provider_name}'。 "
                f"支持的 Provider：{', '.join(self.providers.keys())}。"
            ) from exc


def _read_optional(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default

    stripped_value = value.strip()
    return stripped_value or default


def _read_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ConfigError(f"环境变量 '{name}' 必须是数字。") from exc


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"环境变量 '{name}' 必须是整数。") from exc

    if parsed <= 0:
        raise ConfigError(f"环境变量 '{name}' 必须大于 0。")
    return parsed


def _read_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized_value = raw_value.strip().lower()
    if normalized_value in {"1", "true", "yes", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(
        f"环境变量 '{name}' 必须是布尔值 "
        "（true/false/1/0/yes/no/on/off）。"
    )


def _read_log_level(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized_value = raw_value.strip().upper()
    if normalized_value not in SUPPORTED_LOG_LEVELS:
        raise ConfigError(
            f"环境变量 '{name}' 必须是以下之一："
            f"{', '.join(SUPPORTED_LOG_LEVELS)}。"
        )
    return normalized_value


def _read_log_format(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized_value = raw_value.strip().lower()
    if normalized_value not in SUPPORTED_LOG_FORMATS:
        raise ConfigError(
            f"环境变量 '{name}' 必须是以下之一："
            f"{', '.join(SUPPORTED_LOG_FORMATS)}。"
        )
    return normalized_value


def _read_context_fallback_behavior(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized_value = raw_value.strip().lower()
    if normalized_value not in SUPPORTED_CONTEXT_FALLBACK_BEHAVIORS:
        raise ConfigError(
            f"环境变量 '{name}' 必须是以下之一："
            f"{', '.join(SUPPORTED_CONTEXT_FALLBACK_BEHAVIORS)}。"
        )
    return normalized_value


def _read_context_store_backend(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized_value = raw_value.strip().lower()
    if normalized_value not in SUPPORTED_CONTEXT_STORE_BACKENDS:
        raise ConfigError(
            f"环境变量 '{name}' 必须是以下之一："
            f"{', '.join(SUPPORTED_CONTEXT_STORE_BACKENDS)}。"
        )
    return normalized_value


def _load_dotenv(dotenv_path: str | None) -> None:
    dotenv_file = Path(dotenv_path) if dotenv_path else Path(".env.example")
    if not dotenv_file.exists():
        return

    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise ConfigError(
            "缺少依赖 'python-dotenv'。请先安装："
            "'pip install -r requirements.txt'。"
        ) from exc

    # 当前阶段统一从 .env.example 加载运行配置，不再使用 .env 双轨模式。
    load_dotenv(dotenv_path=dotenv_file, override=True)
