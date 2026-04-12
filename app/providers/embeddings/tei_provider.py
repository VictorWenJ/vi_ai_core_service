"""Local TEI embedding provider."""

from __future__ import annotations

import json
import socket
from typing import Any, Callable
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.providers.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingProviderConfigurationError,
    EmbeddingProviderInvocationError,
    EmbeddingResult,
)


class TEIEmbeddingProvider(BaseEmbeddingProvider):
    """Embedding provider backed by local Text Embeddings Inference service."""

    provider_name = "tei"

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 30.0,
        default_model: str = "BAAI/bge-m3",
        endpoint_path: str = "/embed",
        urlopen: Callable[..., Any] | None = None,
    ) -> None:
        normalized_base_url = (base_url or "").strip().rstrip("/")
        if not normalized_base_url:
            raise EmbeddingProviderConfigurationError(
                "TEI_BASE_URL is required for TEI embedding provider."
            )
        if timeout_seconds <= 0:
            raise EmbeddingProviderConfigurationError(
                "TEI embedding timeout must be greater than 0 seconds."
            )
        normalized_endpoint_path = (endpoint_path or "").strip() or "/embed"
        if not normalized_endpoint_path.startswith("/"):
            normalized_endpoint_path = f"/{normalized_endpoint_path}"

        self._endpoint_url = f"{normalized_base_url}{normalized_endpoint_path}"
        self._timeout_seconds = timeout_seconds
        self._default_model = (default_model or "").strip() or "BAAI/bge-m3"
        self._urlopen = urlopen or urllib_request.urlopen

    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(
                vectors=[],
                model=model or self._default_model,
                dimensions=0,
            )
        invalid_indexes = [
            str(index)
            for index, text in enumerate(texts)
            if not isinstance(text, str)
        ]
        if invalid_indexes:
            raise EmbeddingProviderInvocationError(
                "TEI embedding input must be list[str]. "
                f"Invalid indexes: {', '.join(invalid_indexes)}."
            )

        response_payload = self._post_embeddings(texts)
        raw_vectors = self._extract_vectors(response_payload)
        vectors = self._normalize_vectors(raw_vectors)
        if len(vectors) != len(texts):
            raise EmbeddingProviderInvocationError(
                "TEI embedding response count mismatch: "
                f"expected {len(texts)}, got {len(vectors)}."
            )
        dimensions = len(vectors[0]) if vectors else 0
        return EmbeddingResult(
            vectors=vectors,
            model=model or self._default_model,
            dimensions=dimensions,
        )

    def _post_embeddings(self, texts: list[str]) -> Any:
        request_payload = json.dumps({"inputs": texts}, ensure_ascii=False).encode("utf-8")
        request = urllib_request.Request(
            self._endpoint_url,
            data=request_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with self._urlopen(request, timeout=self._timeout_seconds) as response:
                status_code = getattr(response, "status", None) or response.getcode()
                response_text = response.read().decode("utf-8", errors="replace")
        except urllib_error.HTTPError as exc:
            error_text = _read_error_payload(exc)
            raise EmbeddingProviderInvocationError(
                "TEI embedding request failed with HTTP "
                f"{exc.code}: {error_text or str(exc.reason)}"
            ) from exc
        except urllib_error.URLError as exc:
            raise EmbeddingProviderInvocationError(
                f"TEI embedding service unreachable: {exc.reason}"
            ) from exc
        except (socket.timeout, TimeoutError) as exc:
            raise EmbeddingProviderInvocationError(
                "TEI embedding request timed out."
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise EmbeddingProviderInvocationError(
                f"TEI embedding request failed: {exc}"
            ) from exc

        if status_code != 200:
            raise EmbeddingProviderInvocationError(
                "TEI embedding request failed with HTTP "
                f"{status_code}: {_truncate_text(response_text)}"
            )
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise EmbeddingProviderInvocationError(
                "TEI embedding response is not valid JSON."
            ) from exc

    @staticmethod
    def _extract_vectors(payload: Any) -> Any:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            raise EmbeddingProviderInvocationError(
                "TEI embedding response format is invalid."
            )
        if "embeddings" in payload:
            return payload["embeddings"]
        if "vectors" in payload:
            return payload["vectors"]
        if "data" in payload and isinstance(payload["data"], list):
            embeddings: list[Any] = []
            for index, item in enumerate(payload["data"]):
                if not isinstance(item, dict) or "embedding" not in item:
                    raise EmbeddingProviderInvocationError(
                        "TEI embedding response data item is invalid at index "
                        f"{index}."
                    )
                embeddings.append(item["embedding"])
            return embeddings
        raise EmbeddingProviderInvocationError(
            "TEI embedding response does not contain embeddings."
        )

    @staticmethod
    def _normalize_vectors(raw_vectors: Any) -> list[list[float]]:
        if not isinstance(raw_vectors, list):
            raise EmbeddingProviderInvocationError(
                "TEI embedding response vectors must be a list."
            )
        normalized_vectors: list[list[float]] = []
        for vector_index, vector in enumerate(raw_vectors):
            if not isinstance(vector, list):
                raise EmbeddingProviderInvocationError(
                    "TEI embedding response vector is invalid at index "
                    f"{vector_index}."
                )
            normalized_vector: list[float] = []
            for value_index, value in enumerate(vector):
                if not isinstance(value, (int, float)):
                    raise EmbeddingProviderInvocationError(
                        "TEI embedding value is invalid at "
                        f"vector {vector_index}, position {value_index}."
                    )
                normalized_vector.append(float(value))
            normalized_vectors.append(normalized_vector)

        if normalized_vectors:
            expected_dimensions = len(normalized_vectors[0])
            for vector_index, vector in enumerate(normalized_vectors):
                if len(vector) != expected_dimensions:
                    raise EmbeddingProviderInvocationError(
                        "TEI embedding vectors have inconsistent dimensions at index "
                        f"{vector_index}."
                    )
        return normalized_vectors


def _read_error_payload(exc: urllib_error.HTTPError) -> str:
    try:
        return _truncate_text(exc.read().decode("utf-8", errors="replace"))
    except Exception:  # pragma: no cover - best effort for error body
        return ""


def _truncate_text(value: str, *, limit: int = 500) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "..."
