"""Tests for API hardening: CORS allowlist, body limit, input limits."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_cors_rejects_unknown_origin() -> None:
    client = TestClient(app)
    response = client.options(
        "/v1/check",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_local_origin() -> None:
    client = TestClient(app)
    response = client.options(
        "/v1/check",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8501"


def test_request_body_limit() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/ask",
        content=b"x" * 1_100_000,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["diagnostics"][0]["code"] == "REQUEST_TOO_LARGE"


def test_ask_question_length_limit() -> None:
    client = TestClient(app)
    response = client.post("/v1/ask", json={"question": "x" * 2001})
    assert response.status_code == 422


def test_extract_text_length_limit() -> None:
    client = TestClient(app)
    response = client.post("/v1/extract-facts", json={"text": "x" * 20001})
    assert response.status_code == 422
