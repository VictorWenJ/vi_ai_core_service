"""Application and provider configuration."""

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
SUPPORTED_RAG_EMBEDDING_PROVIDERS = ("deterministic", "openai")

# 全局 LLM 调用的默认超时时间，单位为秒。
DEFAULT_TIMEOUT_SECONDS = 60.0
# 可观测性子域默认是否开启结构化日志。
DEFAULT_LOG_ENABLED = True
# 可观测性日志默认级别，用于控制日志输出粒度。
DEFAULT_LOG_LEVEL = "INFO"
# 可观测性日志默认格式；当前仅支持 json。
DEFAULT_LOG_FORMAT = "json"
# API 层请求/响应负载默认是否允许写入日志。
DEFAULT_LOG_API_PAYLOAD = True
# Provider 层请求/响应负载默认是否允许写入日志。
DEFAULT_LOG_PROVIDER_PAYLOAD = True
# 上下文窗口选择阶段默认 token 预算上限，单位为 token。
DEFAULT_CONTEXT_MAX_TOKEN_BUDGET = 1200
# 上下文截断阶段默认 token 预算上限，单位为 token。
DEFAULT_CONTEXT_TRUNCATION_TOKEN_BUDGET = 900
# 上下文摘要/压缩策略默认是否启用。
DEFAULT_CONTEXT_SUMMARY_ENABLED = True
# 摘要文本默认最大长度，单位为字符数（chars）。
DEFAULT_CONTEXT_SUMMARY_MAX_CHARS = 320
# 超预算回退策略默认行为标识。
DEFAULT_CONTEXT_FALLBACK_BEHAVIOR = "summary_then_drop_oldest"
# 单条消息 token 估算默认固定开销，单位为 token。
DEFAULT_CONTEXT_MESSAGE_OVERHEAD_TOKENS = 4
# 分层短期记忆能力默认是否启用。
DEFAULT_CONTEXT_LAYERED_MEMORY_ENABLED = True
# recent raw 层默认 token 预算上限，单位为 token。
DEFAULT_CONTEXT_RECENT_RAW_MAX_TOKEN_BUDGET = 900
# recent raw 层默认最少保留消息条数，单位为条（count）。
DEFAULT_CONTEXT_RECENT_RAW_MIN_KEEP_MESSAGES = 2
# rolling summary 层默认是否启用。
DEFAULT_CONTEXT_ROLLING_SUMMARY_ENABLED = True
# rolling summary 文本默认最大长度，单位为字符数（chars）。
DEFAULT_CONTEXT_ROLLING_SUMMARY_MAX_CHARS = 1200
# working memory 层默认是否启用。
DEFAULT_CONTEXT_WORKING_MEMORY_ENABLED = True
# working memory 每个 section 默认最大条目数，单位为条（count）。
DEFAULT_CONTEXT_WORKING_MEMORY_MAX_ITEMS_PER_SECTION = 5
# working memory 单条值默认最大长度，单位为字符数（chars）。
DEFAULT_CONTEXT_WORKING_MEMORY_MAX_VALUE_CHARS = 160
# 上下文存储默认后端类型。
DEFAULT_CONTEXT_STORE_BACKEND = "memory"
# Redis 上下文存储默认连接地址。
DEFAULT_CONTEXT_REDIS_URL = "redis://localhost:6379/0"
# 上下文存储默认键前缀，用于隔离命名空间。
DEFAULT_CONTEXT_STORE_KEY_PREFIX = "vi_ai_core_service:context"
# 会话上下文默认 TTL，单位为秒（seconds）。
DEFAULT_CONTEXT_SESSION_TTL_SECONDS = 3600
# Redis 不可用时默认是否允许降级到内存存储。
DEFAULT_CONTEXT_ALLOW_MEMORY_FALLBACK = True
# 流式会话能力默认是否开启。
DEFAULT_STREAMING_ENABLED = True
# 流式心跳事件默认间隔，单位为秒（seconds）。
DEFAULT_STREAM_HEARTBEAT_INTERVAL_SECONDS = 15.0
# 流式请求默认超时时间，单位为秒（seconds）。
DEFAULT_STREAM_REQUEST_TIMEOUT_SECONDS = 120.0
# 流式 completed 事件默认是否附带 usage。
DEFAULT_STREAM_EMIT_USAGE = True
# 流式事件默认是否附带 trace。
DEFAULT_STREAM_EMIT_TRACE = True
# 流式请求默认是否允许显式 cancel。
DEFAULT_STREAM_CANCEL_ENABLED = True

# RAG 子域默认是否启用。
DEFAULT_RAG_ENABLED = False
# Qdrant 默认连接地址。
DEFAULT_RAG_QDRANT_URL = "http://localhost:6333"
# Qdrant 默认集合名称。
DEFAULT_RAG_QDRANT_COLLECTION = "vi_ai_knowledge_chunks"
# 检索默认返回条数上限，单位为条（top-k count）。
DEFAULT_RAG_RETRIEVAL_TOP_K = 4
# 检索默认相似度阈值，单位为余弦分值（0~1）；None 表示不启用阈值过滤。
DEFAULT_RAG_SCORE_THRESHOLD: float | None = None
# chunk 默认目标长度，单位为 token。
DEFAULT_RAG_CHUNK_TOKEN_SIZE = 300
# 相邻 chunk 默认重叠长度，单位为 token。
DEFAULT_RAG_CHUNK_OVERLAP_TOKEN_SIZE = 50
# embedding 默认 provider 名称。
DEFAULT_RAG_EMBEDDING_PROVIDER = "deterministic"
# embedding 默认模型标识。
DEFAULT_RAG_EMBEDDING_MODEL = "deterministic-text-v1"
# embedding 向量默认维度大小，单位为维（dimension）。
DEFAULT_RAG_EMBEDDING_DIMENSION = 64

DEFAULT_BASE_URLS: dict[str, str | None] = {
    "openai": None,
    "deepseek": "https://api.deepseek.com",
    "gemini": None,
    "doubao": None,
    "tongyi": None,
}


class ConfigError(ValueError):
    """Raised when app configuration is invalid."""


@dataclass(frozen=True)
class ProviderConfig:
    # Provider 标识名，需与注册表中的 provider key 一致。
    name: str
    # Provider API 密钥；为空时表示未配置鉴权。
    api_key: str | None = None
    # Provider API 基础地址；为空时使用 SDK/厂商默认地址。
    base_url: str | None = None
    # Provider 默认模型名；为空时由上游调用方显式指定。
    default_model: str | None = None
    # Provider 请求默认超时，单位为秒。
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ObservabilityConfig:
    # 是否启用结构化日志输出。
    log_enabled: bool = DEFAULT_LOG_ENABLED
    # 日志级别阈值。
    log_level: str = DEFAULT_LOG_LEVEL
    # 日志输出格式。
    log_format: str = DEFAULT_LOG_FORMAT
    # 是否记录 API 负载日志。
    log_api_payload: bool = DEFAULT_LOG_API_PAYLOAD
    # 是否记录 Provider 负载日志。
    log_provider_payload: bool = DEFAULT_LOG_PROVIDER_PAYLOAD


@dataclass(frozen=True)
class ContextPolicyConfig:
    # 窗口选择阶段 token 预算上限，单位为 token。
    windows_token_budget: int = DEFAULT_CONTEXT_MAX_TOKEN_BUDGET
    # 截断阶段 token 预算上限，单位为 token。
    truncation_token_budget: int = DEFAULT_CONTEXT_TRUNCATION_TOKEN_BUDGET
    # 是否启用摘要/压缩策略。
    summary_enabled: bool = DEFAULT_CONTEXT_SUMMARY_ENABLED
    # 摘要文本最大长度，单位为字符数（chars）。
    summary_max_chars: int = DEFAULT_CONTEXT_SUMMARY_MAX_CHARS
    # 超预算时的回退行为策略标识。
    fallback_behavior: str = DEFAULT_CONTEXT_FALLBACK_BEHAVIOR
    # 单条消息 token 估算固定开销，单位为 token。
    message_overhead_tokens: int = DEFAULT_CONTEXT_MESSAGE_OVERHEAD_TOKENS


@dataclass(frozen=True)
class ContextStorageConfig:
    # 上下文存储后端类型（memory / redis）。
    backend: str = DEFAULT_CONTEXT_STORE_BACKEND
    # Redis 连接地址；仅在 backend=redis 时生效。
    redis_url: str = DEFAULT_CONTEXT_REDIS_URL
    # 会话存储 TTL，单位为秒（seconds）。
    session_ttl_seconds: int = DEFAULT_CONTEXT_SESSION_TTL_SECONDS
    # 存储键名前缀，用于多服务隔离。
    key_prefix: str = DEFAULT_CONTEXT_STORE_KEY_PREFIX
    # Redis 不可用时是否允许降级至内存后端。
    allow_memory_fallback: bool = DEFAULT_CONTEXT_ALLOW_MEMORY_FALLBACK


@dataclass(frozen=True)
class ContextMemoryConfig:
    # 是否开启 layered short-term memory 管道。
    layered_memory_enabled: bool = DEFAULT_CONTEXT_LAYERED_MEMORY_ENABLED
    # recent raw 层 token 预算上限，单位为 token。
    recent_raw_max_token_budget: int = DEFAULT_CONTEXT_RECENT_RAW_MAX_TOKEN_BUDGET
    # recent raw 层最少保留消息条数，单位为条（count）。
    recent_raw_min_keep_messages: int = DEFAULT_CONTEXT_RECENT_RAW_MIN_KEEP_MESSAGES
    # 是否启用 rolling summary 层。
    rolling_summary_enabled: bool = DEFAULT_CONTEXT_ROLLING_SUMMARY_ENABLED
    # rolling summary 最大长度，单位为字符数（chars）。
    rolling_summary_max_chars: int = DEFAULT_CONTEXT_ROLLING_SUMMARY_MAX_CHARS
    # 是否启用 working memory 层。
    working_memory_enabled: bool = DEFAULT_CONTEXT_WORKING_MEMORY_ENABLED
    # working memory 每个 section 的最大条目数，单位为条（count）。
    working_memory_max_items_per_section: int = (
        DEFAULT_CONTEXT_WORKING_MEMORY_MAX_ITEMS_PER_SECTION
    )
    # working memory 单项文本最大长度，单位为字符数（chars）。
    working_memory_max_value_chars: int = DEFAULT_CONTEXT_WORKING_MEMORY_MAX_VALUE_CHARS


@dataclass(frozen=True)
class StreamingConfig:
    # 是否启用流式聊天输出。
    streaming_enabled: bool = DEFAULT_STREAMING_ENABLED
    # 心跳事件发送间隔，单位为秒（seconds）。
    stream_heartbeat_interval_seconds: float = DEFAULT_STREAM_HEARTBEAT_INTERVAL_SECONDS
    # 流式请求超时阈值，单位为秒（seconds）。
    stream_request_timeout_seconds: float = DEFAULT_STREAM_REQUEST_TIMEOUT_SECONDS
    # 是否在 completed 事件输出 usage。
    stream_emit_usage: bool = DEFAULT_STREAM_EMIT_USAGE
    # 是否在流式事件输出 trace 信息。
    stream_emit_trace: bool = DEFAULT_STREAM_EMIT_TRACE
    # 是否允许通过 cancel 接口中断流式任务。
    stream_cancel_enabled: bool = DEFAULT_STREAM_CANCEL_ENABLED


@dataclass(frozen=True)
class RAGConfig:
    # 是否启用 RAG 检索与引用能力。
    enabled: bool = DEFAULT_RAG_ENABLED
    # Qdrant 连接地址。
    qdrant_url: str = DEFAULT_RAG_QDRANT_URL
    # Qdrant API 密钥；为空表示无鉴权。
    qdrant_api_key: str | None = None
    # Qdrant 集合名称。
    qdrant_collection: str = DEFAULT_RAG_QDRANT_COLLECTION
    # 检索返回条数上限，单位为条（top-k count）。
    retrieval_top_k: int = DEFAULT_RAG_RETRIEVAL_TOP_K
    # 相似度阈值；None 表示不按阈值过滤。
    score_threshold: float | None = DEFAULT_RAG_SCORE_THRESHOLD
    # chunk 目标长度，单位为 token。
    chunk_token_size: int = DEFAULT_RAG_CHUNK_TOKEN_SIZE
    # chunk 间重叠长度，单位为 token。
    chunk_overlap_token_size: int = DEFAULT_RAG_CHUNK_OVERLAP_TOKEN_SIZE
    # embedding provider 标识。
    embedding_provider: str = DEFAULT_RAG_EMBEDDING_PROVIDER
    # embedding 模型标识。
    embedding_model: str = DEFAULT_RAG_EMBEDDING_MODEL
    # embedding 向量维度，单位为维（dimension）。
    embedding_dimension: int = DEFAULT_RAG_EMBEDDING_DIMENSION


@dataclass(frozen=True)
class AppConfig:
    # 服务默认使用的 provider 名称。
    default_provider: str = "openai"
    # 全局默认请求超时，单位为秒（seconds）。
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    # 已解析的 provider 配置映射表。
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    # 可观测性配置。
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    # 上下文策略配置。
    context_policy_config: ContextPolicyConfig = field(default_factory=ContextPolicyConfig)
    # 上下文存储配置。
    context_storage_config: ContextStorageConfig = field(default_factory=ContextStorageConfig)
    # 分层短期记忆配置。
    context_memory_config: ContextMemoryConfig = field(default_factory=ContextMemoryConfig)
    # 流式会话配置。
    streaming_config: StreamingConfig = field(default_factory=StreamingConfig)
    # RAG 子域配置。
    rag_config: RAGConfig = field(default_factory=RAGConfig)

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
                f"Unsupported default provider '{default_provider}'. "
                f"Supported: {', '.join(SUPPORTED_PROVIDER_NAMES)}."
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
        if truncation_token_budget > max_token_budget:
            raise ConfigError(
                "CONTEXT_TRUNCATION_TOKEN_BUDGET must be <= CONTEXT_MAX_TOKEN_BUDGET."
            )

        context = ContextPolicyConfig(
            windows_token_budget=max_token_budget,
            truncation_token_budget=truncation_token_budget,
            summary_enabled=_read_bool(
                "CONTEXT_SUMMARY_ENABLED",
                DEFAULT_CONTEXT_SUMMARY_ENABLED,
            ),
            summary_max_chars=_read_int(
                "CONTEXT_SUMMARY_MAX_CHARS",
                DEFAULT_CONTEXT_SUMMARY_MAX_CHARS,
            ),
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
            raise ConfigError("CONTEXT_STORE_KEY_PREFIX cannot be empty.")
        context_storage = ContextStorageConfig(
            backend=_read_context_store_backend(
                "CONTEXT_STORE_BACKEND",
                DEFAULT_CONTEXT_STORE_BACKEND,
            ),
            redis_url=_read_optional(
                "CONTEXT_REDIS_URL",
                default=DEFAULT_CONTEXT_REDIS_URL,
            )
            or DEFAULT_CONTEXT_REDIS_URL,
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

        context_memory = ContextMemoryConfig(
            layered_memory_enabled=_read_bool(
                "CONTEXT_LAYERED_MEMORY_ENABLED",
                DEFAULT_CONTEXT_LAYERED_MEMORY_ENABLED,
            ),
            recent_raw_max_token_budget=_read_int(
                "CONTEXT_RECENT_RAW_MAX_TOKEN_BUDGET",
                DEFAULT_CONTEXT_RECENT_RAW_MAX_TOKEN_BUDGET,
            ),
            recent_raw_min_keep_messages=_read_int(
                "CONTEXT_RECENT_RAW_MIN_KEEP_MESSAGES",
                DEFAULT_CONTEXT_RECENT_RAW_MIN_KEEP_MESSAGES,
            ),
            rolling_summary_enabled=_read_bool(
                "CONTEXT_ROLLING_SUMMARY_ENABLED",
                DEFAULT_CONTEXT_ROLLING_SUMMARY_ENABLED,
            ),
            rolling_summary_max_chars=_read_int(
                "CONTEXT_ROLLING_SUMMARY_MAX_CHARS",
                DEFAULT_CONTEXT_ROLLING_SUMMARY_MAX_CHARS,
            ),
            working_memory_enabled=_read_bool(
                "CONTEXT_WORKING_MEMORY_ENABLED",
                DEFAULT_CONTEXT_WORKING_MEMORY_ENABLED,
            ),
            working_memory_max_items_per_section=_read_int(
                "CONTEXT_WORKING_MEMORY_MAX_ITEMS_PER_SECTION",
                DEFAULT_CONTEXT_WORKING_MEMORY_MAX_ITEMS_PER_SECTION,
            ),
            working_memory_max_value_chars=_read_int(
                "CONTEXT_WORKING_MEMORY_MAX_VALUE_CHARS",
                DEFAULT_CONTEXT_WORKING_MEMORY_MAX_VALUE_CHARS,
            ),
        )

        streaming = StreamingConfig(
            streaming_enabled=_read_bool("STREAMING_ENABLED", DEFAULT_STREAMING_ENABLED),
            stream_heartbeat_interval_seconds=_read_float(
                "STREAM_HEARTBEAT_INTERVAL_SECONDS",
                DEFAULT_STREAM_HEARTBEAT_INTERVAL_SECONDS,
            ),
            stream_request_timeout_seconds=_read_float(
                "STREAM_REQUEST_TIMEOUT_SECONDS",
                DEFAULT_STREAM_REQUEST_TIMEOUT_SECONDS,
            ),
            stream_emit_usage=_read_bool("STREAM_EMIT_USAGE", DEFAULT_STREAM_EMIT_USAGE),
            stream_emit_trace=_read_bool("STREAM_EMIT_TRACE", DEFAULT_STREAM_EMIT_TRACE),
            stream_cancel_enabled=_read_bool(
                "STREAM_CANCEL_ENABLED",
                DEFAULT_STREAM_CANCEL_ENABLED,
            ),
        )
        if streaming.stream_heartbeat_interval_seconds <= 0:
            raise ConfigError("STREAM_HEARTBEAT_INTERVAL_SECONDS must be greater than 0.")
        if streaming.stream_request_timeout_seconds <= 0:
            raise ConfigError("STREAM_REQUEST_TIMEOUT_SECONDS must be greater than 0.")

        rag_config = RAGConfig(
            enabled=_read_bool("RAG_ENABLED", DEFAULT_RAG_ENABLED),
            qdrant_url=_read_optional("RAG_QDRANT_URL", DEFAULT_RAG_QDRANT_URL)
            or DEFAULT_RAG_QDRANT_URL,
            qdrant_api_key=_read_optional("RAG_QDRANT_API_KEY"),
            qdrant_collection=_read_optional(
                "RAG_QDRANT_COLLECTION",
                DEFAULT_RAG_QDRANT_COLLECTION,
            )
            or DEFAULT_RAG_QDRANT_COLLECTION,
            retrieval_top_k=_read_int("RAG_RETRIEVAL_TOP_K", DEFAULT_RAG_RETRIEVAL_TOP_K),
            score_threshold=_read_optional_float(
                "RAG_SCORE_THRESHOLD",
                DEFAULT_RAG_SCORE_THRESHOLD,
            ),
            chunk_token_size=_read_int("RAG_CHUNK_TOKEN_SIZE", DEFAULT_RAG_CHUNK_TOKEN_SIZE),
            chunk_overlap_token_size=_read_int(
                "RAG_CHUNK_OVERLAP_TOKEN_SIZE",
                DEFAULT_RAG_CHUNK_OVERLAP_TOKEN_SIZE,
            ),
            embedding_provider=_read_rag_embedding_provider(
                "RAG_EMBEDDING_PROVIDER",
                DEFAULT_RAG_EMBEDDING_PROVIDER,
            ),
            embedding_model=_read_optional(
                "RAG_EMBEDDING_MODEL",
                DEFAULT_RAG_EMBEDDING_MODEL,
            )
            or DEFAULT_RAG_EMBEDDING_MODEL,
            embedding_dimension=_read_int(
                "RAG_EMBEDDING_DIMENSION",
                DEFAULT_RAG_EMBEDDING_DIMENSION,
            ),
        )
        if rag_config.chunk_overlap_token_size >= rag_config.chunk_token_size:
            raise ConfigError("RAG_CHUNK_OVERLAP_TOKEN_SIZE must be < RAG_CHUNK_TOKEN_SIZE.")

        return cls(
            default_provider=default_provider,
            timeout_seconds=timeout_seconds,
            providers=providers,
            observability=observability,
            context_policy_config=context,
            context_storage_config=context_storage,
            context_memory_config=context_memory,
            streaming_config=streaming,
            rag_config=rag_config,
        )

    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        normalized_name = provider_name.strip().lower()
        try:
            return self.providers[normalized_name]
        except KeyError as exc:
            raise ConfigError(
                f"Unsupported provider '{provider_name}'. "
                f"Supported: {', '.join(self.providers.keys())}."
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
        raise ConfigError(f"Environment variable '{name}' must be numeric.") from exc


def _read_optional_float(name: str, default: float | None = None) -> float | None:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    stripped_value = raw_value.strip()
    if not stripped_value:
        return default
    try:
        return float(stripped_value)
    except ValueError as exc:
        raise ConfigError(f"Environment variable '{name}' must be numeric.") from exc


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        parsed = int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"Environment variable '{name}' must be integer.") from exc
    if parsed <= 0:
        raise ConfigError(f"Environment variable '{name}' must be greater than 0.")
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
        f"Environment variable '{name}' must be boolean "
        "(true/false/1/0/yes/no/on/off)."
    )


def _read_log_level(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized_value = raw_value.strip().upper()
    if normalized_value not in SUPPORTED_LOG_LEVELS:
        raise ConfigError(
            f"Environment variable '{name}' must be one of: "
            f"{', '.join(SUPPORTED_LOG_LEVELS)}."
        )
    return normalized_value


def _read_log_format(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized_value = raw_value.strip().lower()
    if normalized_value not in SUPPORTED_LOG_FORMATS:
        raise ConfigError(
            f"Environment variable '{name}' must be one of: "
            f"{', '.join(SUPPORTED_LOG_FORMATS)}."
        )
    return normalized_value


def _read_context_fallback_behavior(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized_value = raw_value.strip().lower()
    if normalized_value not in SUPPORTED_CONTEXT_FALLBACK_BEHAVIORS:
        raise ConfigError(
            f"Environment variable '{name}' must be one of: "
            f"{', '.join(SUPPORTED_CONTEXT_FALLBACK_BEHAVIORS)}."
        )
    return normalized_value


def _read_context_store_backend(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized_value = raw_value.strip().lower()
    if normalized_value not in SUPPORTED_CONTEXT_STORE_BACKENDS:
        raise ConfigError(
            f"Environment variable '{name}' must be one of: "
            f"{', '.join(SUPPORTED_CONTEXT_STORE_BACKENDS)}."
        )
    return normalized_value


def _read_rag_embedding_provider(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized_value = raw_value.strip().lower()
    if normalized_value not in SUPPORTED_RAG_EMBEDDING_PROVIDERS:
        raise ConfigError(
            f"Environment variable '{name}' must be one of: "
            f"{', '.join(SUPPORTED_RAG_EMBEDDING_PROVIDERS)}."
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
            "Missing dependency 'python-dotenv'. Run 'pip install -r requirements.txt'."
        ) from exc
    load_dotenv(dotenv_path=dotenv_file, override=True)
