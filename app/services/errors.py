"""Service-facing error contract.

API 层应只依赖这些异常语义，不直接依赖 provider 层异常类型。
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base class for service-layer errors exposed to API handlers."""


class ServiceValidationError(ServiceError):
    """Raised when service input is invalid for current business constraints."""


class ServiceConfigurationError(ServiceError):
    """Raised when required runtime configuration is missing or invalid."""


class ServiceDependencyError(ServiceError):
    """Raised when an upstream dependency (for example provider) fails."""


class ServiceNotImplementedError(ServiceError):
    """Raised when a requested capability is intentionally not available yet."""

