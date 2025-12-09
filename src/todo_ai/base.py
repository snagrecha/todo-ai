"""Abstract base class for todo list implementations."""

from abc import ABC, abstractmethod
from typing import Any

from todo_ai.models import Task, TaskStatus


class TodoList(ABC):
    """Abstract base class for todo list storage strategies.

    All storage implementations must inherit from this class and implement
    all abstract methods.
    """

    @abstractmethod
    async def create_task(
        self,
        content: str,
        priority: int = 0,
        agent_id: str | None = None,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a new task.

        Args:
            content: The task description/content
            priority: Priority level (higher = more important)
            agent_id: ID of the agent this task belongs to
            dependencies: List of task IDs that must complete first
            metadata: Arbitrary metadata for the task

        Returns:
            The created task
        """
        ...

    @abstractmethod
    async def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_tasks(
        self,
        agent_id: str | None = None,
        status: TaskStatus | None = None,
        limit: int | None = None,
    ) -> list[Task]:
        """Get tasks with optional filtering.

        Args:
            agent_id: Filter by agent ID
            status: Filter by task status
            limit: Maximum number of tasks to return

        Returns:
            List of tasks matching the filters
        """
        ...

    @abstractmethod
    async def update_task(
        self,
        task_id: str,
        content: str | None = None,
        status: TaskStatus | None = None,
        priority: int | None = None,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task | None:
        """Update a task.

        Args:
            task_id: The ID of the task to update
            content: New task content
            status: New task status
            priority: New priority level
            dependencies: New list of dependencies
            metadata: New metadata (replaces existing)

        Returns:
            The updated task if found, None otherwise
        """
        ...

    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: The ID of the task to delete

        Returns:
            True if the task was deleted, False if not found
        """
        ...

    @abstractmethod
    async def get_next_task(self, agent_id: str | None = None) -> Task | None:
        """Get the next available task to work on.

        Returns the highest priority task that is:
        - In PENDING status
        - Has all dependencies completed
        - Optionally filtered by agent_id

        Args:
            agent_id: Filter by agent ID

        Returns:
            The next available task, or None if no tasks are available
        """
        ...

    async def mark_in_progress(self, task_id: str) -> Task | None:
        """Mark a task as in progress.

        Args:
            task_id: The ID of the task

        Returns:
            The updated task if found, None otherwise
        """
        return await self.update_task(task_id, status=TaskStatus.IN_PROGRESS)

    async def mark_completed(self, task_id: str) -> Task | None:
        """Mark a task as completed.

        Args:
            task_id: The ID of the task

        Returns:
            The updated task if found, None otherwise
        """
        return await self.update_task(task_id, status=TaskStatus.COMPLETED)

    async def mark_failed(self, task_id: str) -> Task | None:
        """Mark a task as failed.

        Args:
            task_id: The ID of the task

        Returns:
            The updated task if found, None otherwise
        """
        return await self.update_task(task_id, status=TaskStatus.FAILED)

    async def mark_blocked(self, task_id: str) -> Task | None:
        """Mark a task as blocked.

        Args:
            task_id: The ID of the task

        Returns:
            The updated task if found, None otherwise
        """
        return await self.update_task(task_id, status=TaskStatus.BLOCKED)

    @abstractmethod
    async def clear(self, agent_id: str | None = None) -> int:
        """Clear all tasks.

        Args:
            agent_id: If provided, only clear tasks for this agent

        Returns:
            Number of tasks deleted
        """
        ...
