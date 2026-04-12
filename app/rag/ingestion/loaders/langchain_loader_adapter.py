"""LangChain document loaders 到内部模型的适配层。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from app.rag.ingestion.loaders.base import LoadedDocument


class LangChainLoaderAdapter:
    """将 LangChain loader 输出转换为项目内部 LoadedDocument。"""

    def load(
        self,
        *,
        file_path: str | Path,
        loader_factory: Callable[[str], Any],
        source_type: str,
    ) -> LoadedDocument:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        loader = loader_factory(str(path))
        raw_documents = list(loader.load())
        if not raw_documents:
            raise ValueError(f"LangChain loader returned empty documents for: {path}")

        texts: list[str] = []
        merged_metadata: dict[str, Any] = {}
        for raw_document in raw_documents:
            page_content = str(getattr(raw_document, "page_content", "") or "")
            if page_content.strip():
                texts.append(page_content)
            raw_metadata = dict(getattr(raw_document, "metadata", {}) or {})
            for key, value in raw_metadata.items():
                merged_metadata.setdefault(str(key), value)

        if not texts:
            raise ValueError(f"LangChain loader returned empty page_content for: {path}")

        return LoadedDocument(
            text="\n\n".join(texts),
            title=path.stem,
            source_type=source_type,
            origin_uri=str(path),
            file_name=path.name,
            metadata=merged_metadata,
        )

