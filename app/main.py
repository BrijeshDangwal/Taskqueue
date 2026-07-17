from fastapi import FastAPI, HTTPException, Response, status

from app.celery_app import celery_app
from app.schemas import TaskSubmit, TaskSubmitResponse, TaskStatusResponse
from app.tasks import slow_task

app = FastAPI(
    title="Distributed Task Queue",
    description="Submit long-running jobs; poll for results.",
    version="0.1.0",
)

TERMINAL_STATES = {"SUCCESS", "FAILURE"}


@app.get("/health")
def health():
    """Liveness check. Cheap, no dependencies."""
    return {"status": "ok"}


@app.post(
    "/tasks",
    response_model=TaskSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_task(payload: TaskSubmit, response: Response):
    """Accept a job, enqueue it, hand back a receipt.

    Returns 202 — NOT 200 — because the work is accepted, not completed.
    """
    async_result = slow_task.delay(payload.seconds)

    # The 'here's how to find out' half of the 202 contract.
    response.headers["Location"] = f"/tasks/{async_result.id}"

    return TaskSubmitResponse(task_id=async_result.id, status="queued")


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """Poll a task's state. Poll until status is terminal (SUCCESS/FAILURE).

    KNOWN LIMITATION (fixed in M4):
    Celery's AsyncResult returns PENDING for a task_id it has never seen.
    We cannot distinguish 'queued' from 'this ID is garbage'. So a client
    polling a typo'd ID will be told PENDING forever, and never exit its
    loop. The honest answer for an unknown ID is 404, but Celery has no
    record to check against. Fix: persist task_ids in Postgres at enqueue
    time, then 404 on IDs we never issued.
    """
    async_result = celery_app.AsyncResult(task_id)
    state = async_result.state

    result = None
    if state == "SUCCESS":
        result = async_result.result
    elif state == "FAILURE":
        # .result holds the exception object on failure — stringify it,
        # and never leak a traceback to the client.
        result = str(async_result.result)

    return TaskStatusResponse(task_id=task_id, status=state, result=result)