from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.server import app


class HTTPSmokeIntegrationTests(unittest.TestCase):
    def test_health_smoke(self) -> None:
        client = TestClient(app)
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

