import time
from app.celery_app import celery_app

@celery_app.task(name="app.add")
def add(x: int, y: int) -> int:
    """Trivial task — proves args serialize across the broker."""
    return x + y

@celery_app.task(name="app.slow_task")
def slow_task(seconds: int) -> str:
    """Simulates real slow work (LLM call, image resize, report gen)."""
    print(f"[worker] sleeping {seconds}s...")
    time.sleep(seconds)
    return f"slept {seconds}s"