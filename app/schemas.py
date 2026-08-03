from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


class TaskSubmit(BaseModel):
    """Request body for POST /tasks."""
    seconds: int = Field(
        ...,
        ge=1,
        le=60,
        description="How long the simulated work should take.",
    )
    priority: Literal["high", "normal", "low"] = Field(
        default="normal",
        description="Which lane to route this job into.",
    )


class TaskSubmitResponse(BaseModel):
    """202 response — a receipt, not a result."""
    task_id: str
    status: str = "queued"


class TaskStatusResponse(BaseModel):
    """Response for GET /tasks/{task_id}."""
    task_id: str
    status: str
    result: Optional[Any] = None