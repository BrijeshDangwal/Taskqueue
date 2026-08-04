from prometheus_client import Gauge
import redis as redis_lib

from app.config import settings

# Gauges — values that go UP and DOWN (vs counters, which only rise).
queue_depth = Gauge(
    "taskqueue_queue_depth",
    "Number of tasks waiting in each priority lane",
    ["lane"],   # a label so we get one series per lane: high/normal/low
)

# A separate Redis client for reading queue lengths (LLEN).
_r = redis_lib.Redis.from_url(settings.REDIS_URL)

LANES = ["high", "normal", "low"]


def update_queue_depths():
    """Read the current length of each priority lane's Redis list and
    set the gauge. Called on each /metrics scrape."""
    for lane in LANES:
        depth = _r.llen(lane)   # LLEN — the queue depth metric from M1
        queue_depth.labels(lane=lane).set(depth)