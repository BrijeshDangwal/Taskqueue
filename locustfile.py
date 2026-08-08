"""Load test scenarios for the task queue.

Run with:
  locust -f locustfile.py

Then open http://localhost:8089, pick a user class, set users + spawn rate,
and point it at http://localhost:8000.
"""
import random
from locust import HttpUser, task, between


class SubmitOnlyUser(HttpUser):
    """Scenario 1: hammer the submit endpoint — max producer throughput.
    Measures how fast the API can accept and enqueue work."""
    wait_time = between(0.0, 0.1)   # near-constant hammering

    @task
    def submit(self):
        priority = random.choice(["high", "normal", "low"])
        self.client.post(
            "/tasks",
            json={"seconds": 2, "priority": priority},
            name="POST /tasks",          # groups all submits under one label
        )


class SubmitAndPollUser(HttpUser):
    """Scenario 2: realistic full flow — submit, then poll status a few times.
    Exercises the submit path AND the Postgres-backed read path."""
    wait_time = between(0.5, 2.0)      # human-like pacing

    @task
    def submit_and_poll(self):
        # 1. submit
        with self.client.post(
            "/tasks",
            json={"seconds": 2, "priority": random.choice(["high", "normal", "low"])},
            name="POST /tasks",
            catch_response=True,
        ) as resp:
            if resp.status_code != 202:
                resp.failure(f"expected 202, got {resp.status_code}")
                return
            task_id = resp.json()["task_id"]

        # 2. poll status a few times (like a real client waiting for the result)
        for _ in range(3):
            self.client.get(f"/tasks/{task_id}", name="GET /tasks/{id}")
