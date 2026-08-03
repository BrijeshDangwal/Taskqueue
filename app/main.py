import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Response, Depends, status
from sqlalchemy.orm import Session

from app.schemas import TaskSubmit, TaskSubmitResponse, TaskStatusResponse
from app.tasks import slow_task
from app.db import get_db
from app.models import Job

app = FastAPI(
    title="Distributed Task Queue",
    description="Submit long-running jobs; poll for results.",
    version="0.2.0",
)


@app.get("/health")
def health():
    """Liveness check. Cheap, no dependencies."""
    return {"status": "ok"}


@app.post(
    "/tasks",
    response_model=TaskSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_task(payload: TaskSubmit, response: Response, db: Session = Depends(get_db)):
    """Accept a job, record it in Postgres, enqueue it, return a receipt.

    Recording the row here is what lets GET return a real 404 for unknown
    IDs — we now have a registry of the IDs we actually issued.
    """
    async_result = slow_task.apply_async(
        args=[payload.seconds],
        queue=payload.priority,
    )

    # Insert the system-of-record row BEFORE returning.
    job = Job(
        id=async_result.id,
        task_name="app.slow_task",
        status="PENDING",
        priority=payload.priority,
        payload=json.dumps({"seconds": payload.seconds}),
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()

    response.headers["Location"] = f"/tasks/{async_result.id}"
    return TaskSubmitResponse(task_id=async_result.id, status="queued")


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Read a job's state from Postgres — the system-of-record.

    The PENDING lie is DEAD: an unknown ID isn't in the table, so we
    return an honest 404 instead of Celery's misleading 'PENDING'.
    """
    job = db.query(Job).filter(Job.id == task_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Task not found")

    result = json.loads(job.result) if job.result else None
    return TaskStatusResponse(
        task_id=job.id,
        status=job.status,
        result=result,
    )


@app.get("/tasks")
def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List jobs, optionally filtered by status — impossible with Redis,
    trivial with SQL. This is why the system-of-record exists."""
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    jobs = query.order_by(Job.created_at.desc()).limit(limit).all()

    return [
        {
            "task_id": j.id,
            "task_name": j.task_name,
            "status": j.status,
            "priority": j.priority,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]