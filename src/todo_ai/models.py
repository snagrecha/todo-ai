"""Data models for todo-ai."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Task(BaseModel):
    """A task in the todo list."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(..., description="The task description/content")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task")
    priority: int = Field(default=0, description="Priority level (higher = more important)")
    agent_id: str | None = Field(default=None, description="ID of the agent this task belongs to")
    dependencies: list[str] = Field(
        default_factory=list, description="List of task IDs that must complete first"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata for the task"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"frozen": False}

    def is_available(self, completed_task_ids: set[str]) -> bool:
        """Check if this task is available to work on.

        A task is available if:
        - Its status is PENDING
        - All its dependencies are in the completed_task_ids set
        """
        if self.status != TaskStatus.PENDING:
            return False
        return all(dep_id in completed_task_ids for dep_id in self.dependencies)


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    content: str = Field(..., description="The task description/content")
    priority: int = Field(default=0, description="Priority level (higher = more important)")
    agent_id: str | None = Field(default=None, description="ID of the agent this task belongs to")
    dependencies: list[str] = Field(
        default_factory=list, description="List of task IDs that must complete first"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata for the task"
    )


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    content: str | None = Field(default=None, description="The task description/content")
    status: TaskStatus | None = Field(default=None, description="Current status of the task")
    priority: int | None = Field(default=None, description="Priority level (higher = more important)")
    dependencies: list[str] | None = Field(
        default=None, description="List of task IDs that must complete first"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Arbitrary metadata")
