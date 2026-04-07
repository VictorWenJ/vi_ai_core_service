"""Chat route request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_prompt: str = Field(min_length=1, description="Single-turn user prompt.")
    provider: str | None = Field(default=None, description="Optional provider override.")
    model: str | None = Field(default=None, description="Optional model override.")
    temperature: float | None = Field(
        default=None,
        ge=0,
        le=2,
        description="Optional sampling temperature override.",
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,
        description="Optional max tokens override.",
    )
    system_prompt: str | None = Field(default=None, description="Optional system prompt.")
    stream: bool = Field(default=False, description="Streaming response toggle (reserved).")
    session_id: str | None = Field(default=None, description="Optional stateful session id.")
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation id for cross-request continuity.",
    )
    request_id: str | None = Field(default=None, description="Optional external request id.")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional metadata.")


class ChatUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str | None = None
    usage: ChatUsage | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] | None = None

