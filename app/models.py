from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Index

from app.db import Base


class Job(Base):
    """The system-of-record for every job submitted.
    Superset of what Redis holds — captures the full lifecycle."""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)          # the Celery task_id
    task_name = Column(String, nullable=False)     # e.g. "app.slow_task"
    status = Column(String, nullable=False, default="PENDING")
    priority = Column(String, nullable=False, default="normal")
    payload = Column(Text, nullable=True)          # input args, JSON-encoded
    result = Column(Text, nullable=True)           # return value
    error = Column(Text, nullable=True)            # exception message if failed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Indexes on the columns the dashboard filters/sorts on.
    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_created_at", "created_at"),
    )