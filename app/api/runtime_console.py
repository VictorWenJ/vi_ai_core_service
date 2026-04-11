"""Internal console runtime summary routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import get_internal_console_rag_service
from app.api.schemas.console import (
    RuntimeConfigSummaryResponse,
    RuntimeHealthResponse,
    RuntimeSummaryResponse,
)

router = APIRouter(tags=["runtime"])
_get_internal_console_rag_service = get_internal_console_rag_service


@router.get("/runtime/summary", response_model=RuntimeSummaryResponse)
def runtime_summary() -> RuntimeSummaryResponse:
    service = _get_internal_console_rag_service()
    return RuntimeSummaryResponse(**service.get_runtime_summary())


@router.get("/runtime/config-summary", response_model=RuntimeConfigSummaryResponse)
def runtime_config_summary() -> RuntimeConfigSummaryResponse:
    service = _get_internal_console_rag_service()
    return RuntimeConfigSummaryResponse(**service.get_runtime_config_summary())


@router.get("/runtime/health", response_model=RuntimeHealthResponse)
def runtime_health() -> RuntimeHealthResponse:
    service = _get_internal_console_rag_service()
    payload = service.get_runtime_health()
    return RuntimeHealthResponse(
        status=payload["status"],
        service=payload["service"],
        checked_at=payload["checked_at"],
        summary=RuntimeSummaryResponse(**payload["summary"]),
    )
