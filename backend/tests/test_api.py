"""API skeleton: liveness, readiness and request-ID propagation."""

import pytest
from fastapi.testclient import TestClient

from app.api import main


@pytest.fixture
def client() -> TestClient:
    return TestClient(main.create_app())


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_without_database_is_503(client: TestClient) -> None:
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json() == {"status": "not_ready", "database": False}


def test_ready_with_database(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def ok() -> bool:
        return True

    monkeypatch.setattr(main, "ping_database", ok)
    resp = main.create_app()
    assert TestClient(resp).get("/ready").status_code == 200


def test_request_id_echoed(client: TestClient) -> None:
    resp = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert resp.headers["X-Request-ID"] == "abc123"


def test_request_id_generated(client: TestClient) -> None:
    assert len(client.get("/health").headers["X-Request-ID"]) == 32
