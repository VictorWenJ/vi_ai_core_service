"""Centralized application and provider configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_PROVIDER_NAMES = ("openai", "deepseek", "gemini", "doubao", "tongyi")
SUPPORTED_LOG_FORMATS = ("json",)
SUPPORTED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_LOG_ENABLED = True
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "json"
DEFAULT_LOG_API_PAYLOAD = False
DEFAULT_LOG_PROVIDER_PAYLOAD = False
DEFAULT_BASE_URLS: dict[str, str | None] = {
    "openai": None,
    "deepseek": "https://api.deepseek.com",
    "gemini": None,
    "doubao": None,
    "tongyi": None,
}


class ConfigError(ValueError):
    """Raised when application configuration is invalid."""


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for a single provider."""

    name: str
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ObservabilityConfig:
    """Configuration for observability and logging behavior."""

    log_enabled: bool = DEFAULT_LOG_ENABLED
    log_level: str = DEFAULT_LOG_LEVEL
    log_format: str = DEFAULT_LOG_FORMAT
    log_api_payload: bool = DEFAULT_LOG_API_PAYLOAD
    log_provider_payload: bool = DEFAULT_LOG_PROVIDER_PAYLOAD


@dataclass(frozen=True)
class AppConfig:
    """Top-level application configuration."""

    default_provider: str = "openai"
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)

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
                f"Supported providers: {', '.join(SUPPORTED_PROVIDER_NAMES)}."
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

        return cls(
            default_provider=default_provider,
            timeout_seconds=timeout_seconds,
            providers=providers,
            observability=observability,
        )

    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        normalized_name = provider_name.strip().lower()
        try:
            return self.providers[normalized_name]
        except KeyError as exc:
            raise ConfigError(
                f"Unsupported provider '{provider_name}'. "
                f"Supported providers: {', '.join(self.providers.keys())}."
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
        raise ConfigError(f"Environment variable '{name}' must be a number.") from exc


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
        f"Environment variable '{name}' must be a boolean "
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


def _load_dotenv(dotenv_path: str | None) -> None:
    dotenv_file = Path(dotenv_path) if dotenv_path else Path(".env")
    if not dotenv_file.exists():
        return

    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise ConfigError(
            "Missing dependency 'python-dotenv'. Install it with "
            "'pip install -r requirements.txt'."
        ) from exc

    # Keep real environment variables higher priority than local .env values.
    load_dotenv(dotenv_path=dotenv_file, override=False)
