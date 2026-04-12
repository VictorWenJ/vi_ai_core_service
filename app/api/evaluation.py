"""Evaluation domain control-plane routes."""

from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, HTTPException

from app.api.deps import get_rag_evaluation_service
from app.api.error_mapping import build_service_http_exception
from app.api.schemas.control_plane import (
    EvaluationRunCaseResponse,
    EvaluationRunCreateRequest,
    EvaluationRunDetailResponse,
    EvaluationRunSummaryResponse,
)

router = APIRouter(tags=["evaluation"])
_get_evaluation_service = get_rag_evaluation_service


@router.post("/evaluation/rag/runs", response_model=EvaluationRunDetailResponse)
def create_evaluation_run(payload: EvaluationRunCreateRequest) -> EvaluationRunDetailResponse:
    started_at = perf_counter()
    service = _get_evaluation_service()
    try:
        run_result = service.create_evaluation_run(
            dataset_id=payload.dataset_id,
            version_id=payload.version_id,
            samples=[sample.model_dump() for sample in payload.samples],
            run_metadata=dict(payload.metadata) or {"trigger": "control_api"},
        )
    except Exception as exc:
        raise build_service_http_exception(
            exc,
            started_at=started_at,
            event_prefix="api.evaluation.create_run",
        ) from exc
    return EvaluationRunDetailResponse(**_to_run_summary_payload(run_result))


@router.get("/evaluation/rag/runs", response_model=list[EvaluationRunSummaryResponse])
def list_evaluation_runs() -> list[EvaluationRunSummaryResponse]:
    service = _get_evaluation_service()
    return [
        EvaluationRunSummaryResponse(**_to_run_summary_payload(run_result))
        for run_result in service.list_evaluation_runs()
    ]


@router.get("/evaluation/rag/runs/{run_id}", response_model=EvaluationRunDetailResponse)
def get_evaluation_run(run_id: str) -> EvaluationRunDetailResponse:
    service = _get_evaluation_service()
    run_result = service.get_evaluation_run(run_id)
    if run_result is None:
        raise HTTPException(status_code=404, detail=f"run_id '{run_id}' 不存在。")
    return EvaluationRunDetailResponse(**_to_run_summary_payload(run_result))


@router.get("/evaluation/rag/runs/{run_id}/cases", response_model=list[EvaluationRunCaseResponse])
def list_evaluation_run_cases(run_id: str) -> list[EvaluationRunCaseResponse]:
    service = _get_evaluation_service()
    run_result = service.get_evaluation_run(run_id)
    if run_result is None:
        raise HTTPException(status_code=404, detail=f"run_id '{run_id}' 不存在。")
    return [EvaluationRunCaseResponse(**case.to_dict()) for case in run_result.cases]


def _to_run_summary_payload(run_result) -> dict[str, object]:
    return {
        "run_id": run_result.run_id,
        "dataset_id": run_result.dataset_id,
        "dataset_version_id": run_result.dataset_version_id,
        "started_at": run_result.started_at,
        "completed_at": run_result.completed_at,
        "summary": run_result.summary.to_dict(),
        "metadata": dict(run_result.metadata),
        "case_count": len(run_result.cases),
    }
