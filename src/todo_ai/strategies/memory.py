"""In-memory storage strategy for todo-ai."""

from datetime import datetime, timezone
from typing import Any

from todo_ai.base import TodoList
from todo_ai.models import Task, TaskStatus


class InMemoryTodoList(TodoList):
    """In-memory implementation of TodoList.

    This is the simplest storage strategy. Tasks are stored in a dictionary
    and are lost when the process exits. Good for testing and simple use cases.
    """

    def __init__(self) -> None:
        """Initialize the in-memory todo list."""
        self._tasks: dict[str, Task] = {}

    async def create_task(
        self,
        content: str,
        priority: int = 0,
        agent_id: str | None = None,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            content=content,
            priority=priority,
            agent_id=agent_id,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        self._tasks[task.id] = task
        return task

    async def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    async def get_tasks(
        self,
        agent_id: str | None = None,
        status: TaskStatus | None = None,
        limit: int | None = None,
    ) -> list[Task]:
        """Get tasks with optional filtering."""
        tasks = list(self._tasks.values())

        if agent_id is not None:
            tasks = [t for t in tasks if t.agent_id == agent_id]

        if status is not None:
            tasks = [t for t in tasks if t.status == status]

        # Sort by priority (descending) then by created_at (ascending)
        tasks.sort(key=lambda t: (-t.priority, t.created_at))

        if limit is not None:
            tasks = tasks[:limit]

        return tasks

    async def update_task(
        self,
        task_id: str,
        content: str | None = None,
        status: TaskStatus | None = None,
        priority: int | None = None,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task | None:
        """Update a task."""
        task = self._tasks.get(task_id)
        if task is None:
            return None

        if content is not None:
            task.content = content
        if status is not None:
            task.status = status
        if priority is not None:
            task.priority = priority
        if dependencies is not None:
            task.dependencies = dependencies
        if metadata is not None:
            task.metadata = metadata

        task.updated_at = datetime.now(timezone.utc)
        return task

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    async def get_next_task(self, agent_id: str | None = None) -> Task | None:
        """Get the next available task to work on."""
        # Get all completed task IDs for dependency checking
        completed_ids = {
            task_id
            for task_id, task in self._tasks.items()
            if task.status == TaskStatus.COMPLETED
        }

        # Get all pending tasks
        tasks = await self.get_tasks(agent_id=agent_id, status=TaskStatus.PENDING)

        # Filter to only available tasks (dependencies satisfied)
        available_tasks = [t for t in tasks if t.is_available(completed_ids)]

        # Return highest priority (already sorted)
        return available_tasks[0] if available_tasks else None

    async def clear(self, agent_id: str | None = None) -> int:
        """Clear all tasks."""
        if agent_id is None:
            count = len(self._tasks)
            self._tasks.clear()
            return count

        # Clear only tasks for the specified agent
        to_delete = [
            task_id for task_id, task in self._tasks.items() if task.agent_id == agent_id
        ]
        for task_id in to_delete:
            del self._tasks[task_id]
        return len(to_delete)
