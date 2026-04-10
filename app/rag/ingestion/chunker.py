"""Structure-aware, token-aware chunker with overlap."""

from __future__ import annotations

import re
from uuid import uuid4

from app.context.policies.tokenizer import BaseTokenCounter, build_default_token_counter
from app.rag.models import KnowledgeChunk, KnowledgeDocument


class StructuredTokenChunker:
    """Chunk markdown/text with structure-first and token budget fallback."""

    _HEADING_SPLIT = re.compile(r"(?m)(?=^#{1,6}\s)")
    _PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")

    def __init__(self, token_counter: BaseTokenCounter | None = None) -> None:
        self._token_counter = token_counter or build_default_token_counter()

    def chunk_document(
        self,
        document: KnowledgeDocument,
        *,
        chunk_token_size: int,
        overlap_token_size: int,
        embedding_model: str,
    ) -> list[KnowledgeChunk]:
        if chunk_token_size <= 0:
            raise ValueError("chunk_token_size must be greater than 0.")
        if overlap_token_size < 0:
            raise ValueError("overlap_token_size must be >= 0.")
        if overlap_token_size >= chunk_token_size:
            raise ValueError("overlap_token_size must be smaller than chunk_token_size.")

        structural_blocks = self._split_structural_blocks(document.content)
        merged_blocks = self._merge_blocks_by_token_budget(
            blocks=structural_blocks,
            token_budget=chunk_token_size,
        )

        finalized_texts: list[str] = []
        for block in merged_blocks:
            finalized_texts.extend(
                self._split_with_token_budget_and_overlap(
                    text=block,
                    token_budget=chunk_token_size,
                    overlap_tokens=overlap_token_size,
                )
            )

        chunks: list[KnowledgeChunk] = []
        for index, chunk_text in enumerate(finalized_texts):
            token_count = self._token_counter.count_text_tokens(chunk_text)
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"chk_{uuid4().hex}",
                    document_id=document.document_id,
                    chunk_text=chunk_text,
                    chunk_index=index,
                    token_count=token_count,
                    embedding_model=embedding_model,
                    metadata={
                        "title": document.title,
                        "origin_uri": document.origin_uri,
                        "source_type": document.source_type,
                        "jurisdiction": document.jurisdiction,
                        "domain": document.domain,
                        "effective_at": document.effective_at,
                        "updated_at": document.updated_at,
                        "visibility": document.visibility,
                        "file_name": document.file_name,
                        "document_tags": list(document.tags),
                        "document_metadata": dict(document.metadata),
                    },
                )
            )
        return chunks

    def _split_structural_blocks(self, content: str) -> list[str]:
        text = content.strip()
        if not text:
            return []

        sections = self._HEADING_SPLIT.split(text)
        blocks: list[str] = []
        for section in sections:
            stripped_section = section.strip()
            if not stripped_section:
                continue
            paragraphs = self._PARAGRAPH_SPLIT.split(stripped_section)
            for paragraph in paragraphs:
                stripped_paragraph = paragraph.strip()
                if stripped_paragraph:
                    blocks.append(stripped_paragraph)
        return blocks or [text]

    def _merge_blocks_by_token_budget(
        self,
        *,
        blocks: list[str],
        token_budget: int,
    ) -> list[str]:
        if not blocks:
            return []

        merged: list[str] = []
        current = ""
        for block in blocks:
            candidate = block if not current else f"{current}\n\n{block}"
            candidate_tokens = self._token_counter.count_text_tokens(candidate)
            if candidate_tokens <= token_budget:
                current = candidate
                continue

            if current:
                merged.append(current)
                current = ""

            block_tokens = self._token_counter.count_text_tokens(block)
            if block_tokens <= token_budget:
                current = block
            else:
                merged.append(block)

        if current:
            merged.append(current)
        return merged

    def _split_with_token_budget_and_overlap(
        self,
        *,
        text: str,
        token_budget: int,
        overlap_tokens: int,
    ) -> list[str]:
        base_chunks: list[str] = []
        remaining = text.strip()

        while remaining:
            head = self._token_counter.truncate_text_to_tokens(
                remaining,
                token_budget,
                keep_tail=False,
            ).strip()
            if not head:
                break
            base_chunks.append(head)
            if len(head) >= len(remaining):
                break
            remaining = remaining[len(head) :].strip()

        if overlap_tokens <= 0 or len(base_chunks) <= 1:
            return base_chunks

        chunks_with_overlap: list[str] = [base_chunks[0]]
        for index in range(1, len(base_chunks)):
            overlap_text = self._token_counter.truncate_text_to_tokens(
                base_chunks[index - 1],
                overlap_tokens,
                keep_tail=True,
            ).strip()
            current_chunk = base_chunks[index]
            if overlap_text and not current_chunk.startswith(overlap_text):
                current_chunk = f"{overlap_text}\n{current_chunk}".strip()
            chunks_with_overlap.append(current_chunk)
        return chunks_with_overlap
