"""Citation formatter based on retrieved chunks."""

from __future__ import annotations

import hashlib

from app.rag.models import Citation, RetrievedChunk


def build_citations(
    retrieved_chunks: list[RetrievedChunk],
    *,
    snippet_max_chars: int = 220,
) -> list[Citation]:
    citations: list[Citation] = []
    for chunk in retrieved_chunks:
        snippet = _build_snippet(chunk.text, max_chars=snippet_max_chars)
        citations.append(
            Citation(
                citation_id=_build_citation_id(chunk.document_id, chunk.chunk_id),
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                title=chunk.title,
                snippet=snippet,
                origin_uri=chunk.origin_uri,
                source_type=chunk.source_type,
                updated_at=chunk.updated_at,
                metadata={
                    "score": round(chunk.score, 6),
                    **dict(chunk.metadata or {}),
                },
            )
        )
    return citations


def _build_citation_id(document_id: str, chunk_id: str) -> str:
    payload = f"{document_id}:{chunk_id}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:16]


def _build_snippet(text: str, *, max_chars: int) -> str:
    stripped = " ".join(text.split())
    if len(stripped) <= max_chars:
        return stripped
    if max_chars <= 3:
        return stripped[:max_chars]
    return f"{stripped[:max_chars - 3]}..."
