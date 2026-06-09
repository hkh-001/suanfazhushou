from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok() -> None:
    # Health check does not touch the database, so we use a plain TestClient without DB override.
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "status": "ok",
            "service": "backend",
            "app_name": "AlgoMentor AI",
            "environment": "development",
        }
    }
