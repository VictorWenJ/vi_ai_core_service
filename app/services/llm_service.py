"""向后兼容的 LLM 服务导出。

当前基础阶段保留 `LLMService` 作为稳定导入路径，实际编排由 `ChatService` 实现。
"""

from __future__ import annotations

from app.services.chat_service import ChatService


class LLMService(ChatService):
    """聊天编排服务的兼容别名。"""
