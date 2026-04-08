"""面向 Service 层的错误契约。

API 层应只依赖这些异常语义，不直接依赖 Provider 层异常类型。
"""

from __future__ import annotations


class ServiceError(Exception):
    """暴露给 API 处理器的 Service 层错误基类。"""


class ServiceValidationError(ServiceError):
    """当 Service 输入不满足当前业务约束时抛出。"""


class ServiceConfigurationError(ServiceError):
    """当必需运行时配置缺失或无效时抛出。"""


class ServiceDependencyError(ServiceError):
    """当上游依赖（例如 Provider）失败时抛出。"""


class ServiceNotImplementedError(ServiceError):
    """当请求能力尚未提供且为有意保留时抛出。"""
