from fastapi.testclient import TestClient

from backend.app.main import app


def test_auth_and_unauthorized_history() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/soil/analyses").status_code == 401
        response = client.post("/api/v1/auth/register", json={"email": "test-unique-user@example.com", "password": "correct-horse-battery-staple"})
        assert response.status_code in {201, 409}


def test_rejects_unsupported_upload() -> None:
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"email": "phase-test@example.com", "password": "correct-horse-battery-staple"})
        if login.status_code != 200:
            login = client.post("/api/v1/auth/register", json={"email": "phase-test@example.com", "password": "correct-horse-battery-staple"})
        token = login.json()["data"]["access_token"]
        response = client.post("/api/v1/soil/analyze", headers={"Authorization": f"Bearer {token}"}, files={"upload": ("evil.exe", b"not an image", "application/octet-stream")})
        assert response.status_code == 415


def test_cors_preflight_accepts_supported_development_origins() -> None:
    with TestClient(app) as client:
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            response = client.options(
                "/api/v1/auth/register",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin
