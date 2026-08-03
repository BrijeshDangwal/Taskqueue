import json
from datetime import datetime

from celery.signals import task_prerun, task_postrun, task_failure

from app.db import SessionLocal
from app.models import Job


@task_prerun.connect
def on_task_start(task_id=None, task=None, args=None, kwargs=None, **_):
    """Fires just before a worker runs a task. Mark it STARTED."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == task_id).first()
        if job:
            job.status = "STARTED"
            job.started_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


@task_postrun.connect
def on_task_finish(task_id=None, task=None, retval=None, state=None, **_):
    """Fires after a task returns. Record final state + result."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == task_id).first()
        if job:
            job.status = state              # SUCCESS or FAILURE
            job.finished_at = datetime.utcnow()
            if state == "SUCCESS":
                job.result = json.dumps(retval)
            db.commit()
    finally:
        db.close()


@task_failure.connect
def on_task_failure(task_id=None, exception=None, **_):
    """Fires when a task raises. Record the error message."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == task_id).first()
        if job:
            job.status = "FAILURE"
            job.error = str(exception)
            job.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()