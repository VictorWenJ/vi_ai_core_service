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
DEFAULT_CONTEXT_LAYERED_MEMORY_ENABLED = True
DEFAULT_CONTEXT_RECENT_RAW_MAX_TOKEN_BUDGET = 900
DEFAULT_CONTEXT_RECENT_RAW_MIN_KEEP_MESSAGES = 2
DEFAULT_CONTEXT_ROLLING_SUMMARY_ENABLED = True
DEFAULT_CONTEXT_ROLLING_SUMMARY_MAX_CHARS = 1200
DEFAULT_CONTEXT_WORKING_MEMORY_ENABLED = True
DEFAULT_CONTEXT_WORKING_MEMORY_MAX_ITEMS_PER_SECTION = 5
DEFAULT_CONTEXT_WORKING_MEMORY_MAX_VALUE_CHARS = 160
DEFAULT_CONTEXT_STORE_BACKEND = "memory"
DEFAULT_CONTEXT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_CONTEXT_STORE_KEY_PREFIX = "vi_ai_core_service:context"
DEFAULT_CONTEXT_SESSION_TTL_SECONDS = 3600
DEFAULT_CONTEXT_ALLOW_MEMORY_FALLBACK = True
DEFAULT_STREAMING_ENABLED = True
DEFAULT_STREAM_HEARTBEAT_INTERVAL_SECONDS = 15.0
DEFAULT_STREAM_REQUEST_TIMEOUT_SECONDS = 120.0
DEFAULT_STREAM_EMIT_USAGE = True
DEFAULT_STREAM_EMIT_TRACE = True
DEFAULT_STREAM_CANCEL_ENABLED = True

DEFAULT_RAG_ENABLED = False
DEFAULT_RAG_QDRANT_URL = "http://localhost:6333"
DEFAULT_RAG_QDRANT_COLLECTION = "vi_ai_knowledge_chunks"
DEFAULT_RAG_RETRIEVAL_TOP_K = 4
DEFAULT_RAG_SCORE_THRESHOLD: float | None = None
DEFAULT_RAG_CHUNK_TOKEN_SIZE = 300
DEFAULT_RAG_CHUNK_OVERLAP_TOKEN_SIZE = 50
DEFAULT_RAG_EMBEDDING_PROVIDER = "deterministic"
DEFAULT_RAG_EMBEDDING_MODEL = "deterministic-text-v1"
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
    name: str
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ObservabilityConfig:
    log_enabled: bool = DEFAULT_LOG_ENABLED
    log_level: str = DEFAULT_LOG_LEVEL
    log_format: str = DEFAULT_LOG_FORMAT
    log_api_payload: bool = DEFAULT_LOG_API_PAYLOAD
    log_provider_payload: bool = DEFAULT_LOG_PROVIDER_PAYLOAD


@dataclass(frozen=True)
class ContextPolicyConfig:
    windows_token_budget: int = DEFAULT_CONTEXT_MAX_TOKEN_BUDGET
    truncation_token_budget: int = DEFAULT_CONTEXT_TRUNCATION_TOKEN_BUDGET
    summary_enabled: bool = DEFAULT_CONTEXT_SUMMARY_ENABLED
    summary_max_chars: int = DEFAULT_CONTEXT_SUMMARY_MAX_CHARS
    fallback_behavior: str = DEFAULT_CONTEXT_FALLBACK_BEHAVIOR
    message_overhead_tokens: int = DEFAULT_CONTEXT_MESSAGE_OVERHEAD_TOKENS


@dataclass(frozen=True)
class ContextStorageConfig:
    backend: str = DEFAULT_CONTEXT_STORE_BACKEND
    redis_url: str = DEFAULT_CONTEXT_REDIS_URL
    session_ttl_seconds: int = DEFAULT_CONTEXT_SESSION_TTL_SECONDS
    key_prefix: str = DEFAULT_CONTEXT_STORE_KEY_PREFIX
    allow_memory_fallback: bool = DEFAULT_CONTEXT_ALLOW_MEMORY_FALLBACK


@dataclass(frozen=True)
class ContextMemoryConfig:
    layered_memory_enabled: bool = DEFAULT_CONTEXT_LAYERED_MEMORY_ENABLED
    recent_raw_max_token_budget: int = DEFAULT_CONTEXT_RECENT_RAW_MAX_TOKEN_BUDGET
    recent_raw_min_keep_messages: int = DEFAULT_CONTEXT_RECENT_RAW_MIN_KEEP_MESSAGES
    rolling_summary_enabled: bool = DEFAULT_CONTEXT_ROLLING_SUMMARY_ENABLED
    rolling_summary_max_chars: int = DEFAULT_CONTEXT_ROLLING_SUMMARY_MAX_CHARS
    working_memory_enabled: bool = DEFAULT_CONTEXT_WORKING_MEMORY_ENABLED
    working_memory_max_items_per_section: int = (
        DEFAULT_CONTEXT_WORKING_MEMORY_MAX_ITEMS_PER_SECTION
    )
    working_memory_max_value_chars: int = DEFAULT_CONTEXT_WORKING_MEMORY_MAX_VALUE_CHARS


@dataclass(frozen=True)
class StreamingConfig:
    streaming_enabled: bool = DEFAULT_STREAMING_ENABLED
    stream_heartbeat_interval_seconds: float = DEFAULT_STREAM_HEARTBEAT_INTERVAL_SECONDS
    stream_request_timeout_seconds: float = DEFAULT_STREAM_REQUEST_TIMEOUT_SECONDS
    stream_emit_usage: bool = DEFAULT_STREAM_EMIT_USAGE
    stream_emit_trace: bool = DEFAULT_STREAM_EMIT_TRACE
    stream_cancel_enabled: bool = DEFAULT_STREAM_CANCEL_ENABLED


@dataclass(frozen=True)
class RAGConfig:
    enabled: bool = DEFAULT_RAG_ENABLED
    qdrant_url: str = DEFAULT_RAG_QDRANT_URL
    qdrant_api_key: str | None = None
    qdrant_collection: str = DEFAULT_RAG_QDRANT_COLLECTION
    retrieval_top_k: int = DEFAULT_RAG_RETRIEVAL_TOP_K
    score_threshold: float | None = DEFAULT_RAG_SCORE_THRESHOLD
    chunk_token_size: int = DEFAULT_RAG_CHUNK_TOKEN_SIZE
    chunk_overlap_token_size: int = DEFAULT_RAG_CHUNK_OVERLAP_TOKEN_SIZE
    embedding_provider: str = DEFAULT_RAG_EMBEDDING_PROVIDER
    embedding_model: str = DEFAULT_RAG_EMBEDDING_MODEL
    embedding_dimension: int = DEFAULT_RAG_EMBEDDING_DIMENSION


@dataclass(frozen=True)
class AppConfig:
    default_provider: str = "openai"
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    context_policy_config: ContextPolicyConfig = field(default_factory=ContextPolicyConfig)
    context_storage_config: ContextStorageConfig = field(default_factory=ContextStorageConfig)
    context_memory_config: ContextMemoryConfig = field(default_factory=ContextMemoryConfig)
    streaming_config: StreamingConfig = field(default_factory=StreamingConfig)
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
