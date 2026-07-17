import time
from app.celery_app import celery_app

import redis as redis_lib
from app.config import settings

# A Redis client just for idempotency bookkeeping (separate concern from the broker).
_r = redis_lib.Redis.from_url(settings.REDIS_URL)

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

@celery_app.task(name="app.crash_test")
def crash_test(label: str) -> str:
    """Appends to a file each time it RUNS. Lets us count executions."""
    import datetime
    with open("/tmp/crash_test.log", "a") as f:
        f.write(f"{datetime.datetime.now()} RAN: {label}\n")
    print(f"[worker] crash_test started for {label!r} — sleeping 20s")
    time.sleep(20)   # long window to kill the worker mid-task
    print(f"[worker] crash_test FINISHED for {label!r}")
    return f"done: {label}"

@celery_app.task(name="app.idempotent_charge", bind=True)
def idempotent_charge(self, idempotency_key: str, amount: int) -> str:
    """Simulates charging a card exactly once, even if delivered many times.

    The idempotency_key identifies THIS unit of work. We record completion
    in Redis AFTER the side effect, so a crash before recording leads to a
    safe retry, and a redelivery after recording is skipped.
    """
    import datetime

    done_key = f"charge:done:{idempotency_key}"

    # 1. Have we already completed this exact work?
    existing = _r.get(done_key)
    if existing is not None:
        msg = f"SKIPPED (already charged): {idempotency_key}"
        print(f"[worker] {msg}")
        # return the ORIGINAL result — caller can't tell it was a duplicate
        return existing.decode()

    # 2. Not done yet — perform the side effect (the "charge").
    #    This is the line that must NOT run twice.
    with open("/tmp/charges.log", "a") as f:
        f.write(f"{datetime.datetime.now()} CHARGED ${amount} key={idempotency_key}\n")
    print(f"[worker] CHARGING ${amount} for {idempotency_key} — sleeping 20s")
    time.sleep(20)   # long window to kill mid-charge

    result = f"charged ${amount} (key={idempotency_key})"

    # 3. Record completion — AFTER the work succeeded.
    #    NX = only set if not exists; ex = expire after 1h (cleanup).
    _r.set(done_key, result, nx=True, ex=3600)
    print(f"[worker] recorded done for {idempotency_key}")

    return result