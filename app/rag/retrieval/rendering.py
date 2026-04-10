"""Rendering utilities for retrieval output."""

from __future__ import annotations

from app.rag.models import RetrievedChunk


def render_knowledge_block(
    retrieved_chunks: list[RetrievedChunk],
    *,
    max_snippet_chars: int = 280,
) -> str | None:
    if not retrieved_chunks:
        return None

    lines = ["[knowledge_block]"]
    for index, chunk in enumerate(retrieved_chunks, start=1):
        title = chunk.title or "untitled"
        source = chunk.origin_uri or "n/a"
        snippet = _snippet(chunk.text, max_snippet_chars=max_snippet_chars)
        lines.append(
            f"{index}. title={title}; source={source}; score={chunk.score:.4f}"
        )
        lines.append(f"   snippet={snippet}")
    return "\n".join(lines)


def _snippet(text: str, *, max_snippet_chars: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_snippet_chars:
        return normalized
    if max_snippet_chars <= 3:
        return normalized[:max_snippet_chars]
    return f"{normalized[: max_snippet_chars - 3]}..."
