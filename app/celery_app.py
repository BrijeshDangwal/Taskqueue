from celery import Celery
from app.config import settings

# The Celery application instance.
# - broker: where tasks are QUEUED (producer pushes here, worker pulls from here)
# - backend: where RESULTS are STORED (worker writes here, producer reads here)
celery_app = Celery(
    "taskqueue",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Ensure Celery discovers the tasks defined in app/tasks.py
celery_app.autodiscover_tasks(["app"])

# Import tasks so they register when the worker starts.
import app.tasks  # noqa: E402, F401