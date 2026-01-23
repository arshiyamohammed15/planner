from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Ensure CORS allowed origins are deterministic for tests before app import
os.environ.setdefault("PLANNER_ALLOWED_ORIGINS", "https://allowed.test")

from api.authentication import create_access_token  # noqa: E402
from api.planner_api import app  # noqa: E402


client = TestClient(app)


def auth_headers(subject: str = "tester-1") -> dict[str, str]:
    token = create_access_token(subject)
    return {"Authorization": f"Bearer {token}"}


def test_jwt_allows_access_to_plan():
    payload = {"goal": "Reliability", "feature": "Search"}
    resp = client.post("/plan", json=payload, headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["goal"] == payload["goal"]
    assert data["feature"] == payload["feature"]


def test_jwt_missing_token_rejected():
    payload = {"goal": "Reliability", "feature": "Search"}
    resp = client.post("/plan", json=payload)
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authorization header missing or invalid"


def test_input_validation_blank_goal_rejected():
    payload = {"goal": "   ", "feature": "Search"}
    resp = client.post("/plan", json=payload, headers=auth_headers())
    assert resp.status_code == 422


def test_input_validation_missing_feature_rejected():
    payload = {"goal": "Reliability"}
    resp = client.post("/plan", json=payload, headers=auth_headers())
    assert resp.status_code == 422


def test_cors_allows_configured_origin():
    headers = {
        "Origin": "https://allowed.test",
        "Access-Control-Request-Method": "POST",
    }
    resp = client.options("/plan", headers=headers)
    assert resp.status_code == 200
    # CORS middleware should echo allowed origin
    assert resp.headers.get("access-control-allow-origin") == "https://allowed.test"


def test_cors_blocks_disallowed_origin():
    headers = {
        "Origin": "https://blocked.example.com",
        "Access-Control-Request-Method": "POST",
    }
    resp = client.options("/plan", headers=headers)
    # Starlette returns 400 for disallowed CORS preflight
    assert resp.status_code in (400, 403)
    assert resp.headers.get("access-control-allow-origin") is None

