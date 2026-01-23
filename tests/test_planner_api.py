from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.authentication import create_access_token
from api.planner_api import app


client = TestClient(app)


def auth_headers(subject: str = "tester-1") -> dict[str, str]:
    token = create_access_token(subject)
    return {"Authorization": f"Bearer {token}"}


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_plan_success():
    payload = {
        "goal": "Ensure checkout flow reliability",
        "feature": "Checkout",
        "constraints": ["PCI compliance", "limited staging data"],
        "owner": "qa-team",
    }
    response = client.post("/plan", json=payload, headers=auth_headers())
    assert response.status_code == 200

    data = response.json()
    assert data["plan_id"]
    assert data["feature"] == payload["feature"]
    assert data["goal"] == payload["goal"]
    assert len(data["tasks"]) >= 1
    assert all("test_type" in task for task in data["tasks"])


def test_plan_missing_token_unauthorized():
    payload = {"goal": "G", "feature": "F"}
    response = client.post("/plan", json=payload)
    assert response.status_code == 401


def test_plan_blank_goal_validation():
    payload = {"goal": "   ", "feature": "Checkout"}
    response = client.post("/plan", json=payload, headers=auth_headers())
    assert response.status_code == 422


def test_assign_task_success():
    # Seed tasks by creating a plan
    plan_response = client.post(
        "/plan",
        json={"goal": "Reliability", "feature": "Search"},
        headers=auth_headers(),
    )
    assert plan_response.status_code == 200
    task_id = plan_response.json()["tasks"][0]["id"]

    assign_response = client.post(
        "/assign_task",
        json={"task_id": task_id, "owner": "qa-engineer"},
        headers=auth_headers(),
    )
    assert assign_response.status_code == 200
    data = assign_response.json()
    assert data["task_id"] == task_id
    assert data["owner"] == "qa-engineer"
    assert "assigned to qa-engineer" in data["message"]


def test_assign_task_unknown_task():
    response = client.post(
        "/assign_task",
        json={"task_id": "task-does-not-exist", "owner": "qa-engineer"},
        headers=auth_headers(),
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_assign_task_blank_owner_validation():
    response = client.post(
        "/assign_task",
        json={"task_id": "task-1", "owner": "   "},
        headers=auth_headers(),
    )
    assert response.status_code == 422

