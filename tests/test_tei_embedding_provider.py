from __future__ import annotations

import io
import json
import unittest
from urllib import error as urllib_error

from app.providers.embeddings.base import EmbeddingProviderInvocationError
from app.providers.embeddings.tei_provider import TEIEmbeddingProvider


class _FakeHTTPResponse:
    def __init__(self, *, status_code: int, payload_text: str) -> None:
        self.status = status_code
        self._payload_text = payload_text

    def read(self) -> bytes:
        return self._payload_text.encode("utf-8")

    def getcode(self) -> int:
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class TEIEmbeddingProviderTests(unittest.TestCase):
    def test_embed_texts_returns_vectors_for_batch_inputs(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["body"] = request.data.decode("utf-8")
            return _FakeHTTPResponse(
                status_code=200,
                payload_text=json.dumps([[0.1, 0.2], [0.3, 0.4]]),
            )

        provider = TEIEmbeddingProvider(
            base_url="http://tei:80",
            timeout_seconds=12.0,
            default_model="BAAI/bge-m3",
            urlopen=fake_urlopen,
        )

        result = provider.embed_texts(["first", "second"], model="BAAI/bge-m3")

        self.assertEqual(captured["url"], "http://tei:80/embed")
        self.assertEqual(captured["timeout"], 12.0)
        self.assertEqual(
            json.loads(captured["body"]),
            {"inputs": ["first", "second"]},
        )
        self.assertEqual(result.model, "BAAI/bge-m3")
        self.assertEqual(result.dimensions, 2)
        self.assertEqual(len(result.vectors), 2)
        self.assertEqual(result.vectors[0], [0.1, 0.2])

    def test_embed_texts_raises_when_tei_returns_http_error(self) -> None:
        def fake_urlopen(_request, timeout):
            raise urllib_error.HTTPError(
                url="http://tei:80/embed",
                code=503,
                msg="Service Unavailable",
                hdrs=None,
                fp=io.BytesIO(b'{"error":"busy"}'),
            )

        provider = TEIEmbeddingProvider(
            base_url="http://tei:80",
            urlopen=fake_urlopen,
        )

        with self.assertRaisesRegex(EmbeddingProviderInvocationError, "HTTP 503"):
            provider.embed_texts(["first"], model="BAAI/bge-m3")

    def test_embed_texts_raises_when_response_format_is_invalid(self) -> None:
        def fake_urlopen(_request, timeout):
            return _FakeHTTPResponse(
                status_code=200,
                payload_text=json.dumps({"unexpected": "shape"}),
            )

        provider = TEIEmbeddingProvider(
            base_url="http://tei:80",
            urlopen=fake_urlopen,
        )

        with self.assertRaisesRegex(
            EmbeddingProviderInvocationError,
            "does not contain embeddings",
        ):
            provider.embed_texts(["first"], model="BAAI/bge-m3")

    def test_embed_texts_raises_when_response_count_mismatches_input(self) -> None:
        def fake_urlopen(_request, timeout):
            return _FakeHTTPResponse(
                status_code=200,
                payload_text=json.dumps([[0.1, 0.2]]),
            )

        provider = TEIEmbeddingProvider(
            base_url="http://tei:80",
            urlopen=fake_urlopen,
        )

        with self.assertRaisesRegex(
            EmbeddingProviderInvocationError,
            "response count mismatch",
        ):
            provider.embed_texts(["first", "second"], model="BAAI/bge-m3")

    def test_embed_texts_raises_when_service_is_unreachable(self) -> None:
        def fake_urlopen(_request, timeout):
            raise urllib_error.URLError("connection refused")

        provider = TEIEmbeddingProvider(
            base_url="http://tei:80",
            urlopen=fake_urlopen,
        )

        with self.assertRaisesRegex(
            EmbeddingProviderInvocationError,
            "service unreachable",
        ):
            provider.embed_texts(["first"], model="BAAI/bge-m3")
