"""Knowledge domain control-plane routes."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import (
    get_rag_build_service,
    get_rag_document_service,
    get_rag_inspector_service,
)
from app.api.error_mapping import build_service_http_exception
from app.api.schemas.control_plane import (
    BuildCreateRequest,
    BuildDetailResponse,
    BuildSummaryResponse,
    KnowledgeChunkDetailResponse,
    KnowledgeChunkVectorDetailResponse,
    KnowledgeChunkSummaryResponse,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentSummaryResponse,
    KnowledgeDocumentUploadResponse,
    RetrievalDebugRequest,
    RetrievalDebugResponse,
)

router = APIRouter(tags=["knowledge"])
_get_document_service = get_rag_document_service
_get_build_service = get_rag_build_service
_get_inspector_service = get_rag_inspector_service


@router.post(
    "/knowledge/documents/upload",
    response_model=KnowledgeDocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    document_id: str | None = Form(default=None),
    title: str | None = Form(default=None),
    source_type: str | None = Form(default=None),
    jurisdiction: str | None = Form(default=None),
    domain: str | None = Form(default=None),
    tags: str | None = Form(default=None),
) -> KnowledgeDocumentUploadResponse:
    started_at = perf_counter()
    service = _get_document_service()
    try:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8")
        tag_list = _parse_tags(tags)
        document = service.upload_document(
            content=content,
            file_name=file.filename or "uploaded.txt",
            document_id=document_id,
            title=title,
            source_type=source_type,
            jurisdiction=jurisdiction,
            domain=domain,
            tags=tag_list,
            metadata={"uploaded_via": "control_api"},
        )
    except Exception as exc:
        raise build_service_http_exception(
            exc,
            started_at=started_at,
            event_prefix="api.knowledge.upload",
            context_payload={"file_name": file.filename or "uploaded.txt"},
        ) from exc
    return KnowledgeDocumentUploadResponse(
        document_id=document.document_id,
        title=document.title,
        source_type=document.source_type,
        file_name=document.file_name,
        updated_at=document.updated_at,
        metadata=dict(document.metadata),
    )


@router.post("/knowledge/builds", response_model=BuildDetailResponse)
def create_build(payload: BuildCreateRequest) -> BuildDetailResponse:
    started_at = perf_counter()
    service = _get_build_service()
    try:
        build_payload = service.create_build(
            version_id=payload.version_id,
            force_rebuild_document_ids=payload.force_rebuild_document_ids,
            max_failure_ratio=payload.max_failure_ratio,
            max_empty_chunk_ratio=payload.max_empty_chunk_ratio,
        )
    except Exception as exc:
        raise build_service_http_exception(
            exc,
            started_at=started_at,
            event_prefix="api.knowledge.create_build",
        ) from exc
    return BuildDetailResponse(**_normalize_build_payload(build_payload))


@router.get("/knowledge/builds", response_model=list[BuildSummaryResponse])
def list_builds() -> list[BuildSummaryResponse]:
    service = _get_inspector_service()
    return [
        BuildSummaryResponse(**_build_summary_payload(build_payload))
        for build_payload in service.list_builds()
    ]


@router.get("/knowledge/builds/{build_id}", response_model=BuildDetailResponse)
def get_build(build_id: str) -> BuildDetailResponse:
    service = _get_inspector_service()
    build_payload = service.get_build(build_id)
    if build_payload is None:
        raise HTTPException(status_code=404, detail=f"build_id '{build_id}' 不存在。")
    return BuildDetailResponse(**_normalize_build_payload(build_payload))


@router.get("/knowledge/documents", response_model=list[KnowledgeDocumentSummaryResponse])
def list_documents() -> list[KnowledgeDocumentSummaryResponse]:
    service = _get_inspector_service()
    return [
        KnowledgeDocumentSummaryResponse(**document_payload)
        for document_payload in service.list_documents()
    ]


@router.get(
    "/knowledge/documents/{document_id}",
    response_model=KnowledgeDocumentDetailResponse,
)
def get_document(document_id: str) -> KnowledgeDocumentDetailResponse:
    service = _get_inspector_service()
    document_payload = service.get_document(document_id)
    if document_payload is None:
        raise HTTPException(status_code=404, detail=f"document_id '{document_id}' 不存在。")
    return KnowledgeDocumentDetailResponse(**document_payload)


@router.get(
    "/knowledge/documents/{document_id}/chunks",
    response_model=list[KnowledgeChunkSummaryResponse],
)
def list_document_chunks(document_id: str) -> list[KnowledgeChunkSummaryResponse]:
    service = _get_inspector_service()
    chunks_payload = service.list_document_chunks(document_id)
    if chunks_payload is None:
        raise HTTPException(status_code=404, detail=f"document_id '{document_id}' 不存在。")
    return [KnowledgeChunkSummaryResponse(**chunk_payload) for chunk_payload in chunks_payload]


@router.get("/knowledge/chunks/{chunk_id}", response_model=KnowledgeChunkDetailResponse)
def get_chunk(chunk_id: str) -> KnowledgeChunkDetailResponse:
    service = _get_inspector_service()
    chunk_payload = service.get_chunk(chunk_id)
    if chunk_payload is None:
        raise HTTPException(status_code=404, detail=f"chunk_id '{chunk_id}' 不存在。")
    return KnowledgeChunkDetailResponse(**chunk_payload)


@router.get(
    "/knowledge/chunks/{chunk_id}/vector",
    response_model=KnowledgeChunkVectorDetailResponse,
)
def get_chunk_vector_detail(chunk_id: str) -> KnowledgeChunkVectorDetailResponse:
    service = _get_inspector_service()
    vector_payload = service.get_chunk_vector_detail(chunk_id=chunk_id)
    if vector_payload is None:
        raise HTTPException(status_code=404, detail=f"chunk_id '{chunk_id}' 不存在。")
    return KnowledgeChunkVectorDetailResponse(**vector_payload)


@router.post("/knowledge/retrieval/debug", response_model=RetrievalDebugResponse)
def retrieval_debug(payload: RetrievalDebugRequest) -> RetrievalDebugResponse:
    started_at = perf_counter()
    service = _get_inspector_service()
    try:
        debug_payload = service.retrieval_debug(
            query_text=payload.query_text,
            metadata_filter=payload.metadata_filter,
            top_k=payload.top_k,
        )
    except Exception as exc:
        raise build_service_http_exception(
            exc,
            started_at=started_at,
            event_prefix="api.knowledge.retrieval_debug",
            context_payload={"query_text": payload.query_text},
        ) from exc
    return RetrievalDebugResponse(**debug_payload)


def _parse_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    return [segment.strip() for segment in raw_tags.split(",") if segment.strip()]


def _build_summary_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _normalize_build_payload(payload)
    return {
        "metadata": payload["metadata"],
        "statistics": payload["statistics"],
        "quality_gate": payload["quality_gate"],
    }


def _normalize_build_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "to_dict"):
        return dict(payload.to_dict())
    raise ValueError("build payload 格式不正确。")
