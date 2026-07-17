from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_submit_task_returns_202_and_valid_id():
    r = client.post("/tasks", json={"seconds": 1})
    assert r.status_code == 202
    body = r.json()
    assert "task_id" in body
    assert len(body["task_id"]) > 0
    assert body["status"] == "queued"
    assert r.headers["location"] == f"/tasks/{body['task_id']}"


def test_submit_rejects_invalid_payload():
    r = client.post("/tasks", json={"seconds": 999})
    assert r.status_code == 422