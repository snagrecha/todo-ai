"""Tests for InMemoryTodoList storage strategy."""

import pytest

from todo_ai.models import TaskStatus
from todo_ai.strategies.memory import InMemoryTodoList


@pytest.fixture
def todo_list() -> InMemoryTodoList:
    """Create a fresh InMemoryTodoList for each test."""
    return InMemoryTodoList()


class TestInMemoryTodoList:
    """Tests for InMemoryTodoList."""

    @pytest.mark.asyncio
    async def test_create_task(self, todo_list: InMemoryTodoList) -> None:
        """Test creating a task."""
        task = await todo_list.create_task(content="Test task")
        assert task.content == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.id is not None

    @pytest.mark.asyncio
    async def test_create_task_with_options(self, todo_list: InMemoryTodoList) -> None:
        """Test creating a task with all options."""
        task = await todo_list.create_task(
            content="Test task",
            priority=5,
            agent_id="agent-1",
            dependencies=["dep-1"],
            metadata={"key": "value"},
        )
        assert task.content == "Test task"
        assert task.priority == 5
        assert task.agent_id == "agent-1"
        assert task.dependencies == ["dep-1"]
        assert task.metadata == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_task(self, todo_list: InMemoryTodoList) -> None:
        """Test getting a task by ID."""
        created = await todo_list.create_task(content="Test task")
        retrieved = await todo_list.get_task(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content == "Test task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, todo_list: InMemoryTodoList) -> None:
        """Test getting a non-existent task."""
        result = await todo_list.get_task("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_tasks_empty(self, todo_list: InMemoryTodoList) -> None:
        """Test getting tasks from empty list."""
        tasks = await todo_list.get_tasks()
        assert tasks == []

    @pytest.mark.asyncio
    async def test_get_tasks_all(self, todo_list: InMemoryTodoList) -> None:
        """Test getting all tasks."""
        await todo_list.create_task(content="Task 1")
        await todo_list.create_task(content="Task 2")
        await todo_list.create_task(content="Task 3")

        tasks = await todo_list.get_tasks()
        assert len(tasks) == 3

    @pytest.mark.asyncio
    async def test_get_tasks_by_agent_id(self, todo_list: InMemoryTodoList) -> None:
        """Test filtering tasks by agent ID."""
        await todo_list.create_task(content="Task 1", agent_id="agent-1")
        await todo_list.create_task(content="Task 2", agent_id="agent-2")
        await todo_list.create_task(content="Task 3", agent_id="agent-1")

        tasks = await todo_list.get_tasks(agent_id="agent-1")
        assert len(tasks) == 2
        assert all(t.agent_id == "agent-1" for t in tasks)

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, todo_list: InMemoryTodoList) -> None:
        """Test filtering tasks by status."""
        task1 = await todo_list.create_task(content="Task 1")
        await todo_list.create_task(content="Task 2")
        await todo_list.mark_completed(task1.id)

        pending = await todo_list.get_tasks(status=TaskStatus.PENDING)
        assert len(pending) == 1

        completed = await todo_list.get_tasks(status=TaskStatus.COMPLETED)
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_get_tasks_with_limit(self, todo_list: InMemoryTodoList) -> None:
        """Test limiting number of tasks returned."""
        for i in range(5):
            await todo_list.create_task(content=f"Task {i}")

        tasks = await todo_list.get_tasks(limit=3)
        assert len(tasks) == 3

    @pytest.mark.asyncio
    async def test_get_tasks_sorted_by_priority(self, todo_list: InMemoryTodoList) -> None:
        """Test that tasks are sorted by priority (descending)."""
        await todo_list.create_task(content="Low priority", priority=1)
        await todo_list.create_task(content="High priority", priority=10)
        await todo_list.create_task(content="Medium priority", priority=5)

        tasks = await todo_list.get_tasks()
        assert tasks[0].content == "High priority"
        assert tasks[1].content == "Medium priority"
        assert tasks[2].content == "Low priority"

    @pytest.mark.asyncio
    async def test_update_task(self, todo_list: InMemoryTodoList) -> None:
        """Test updating a task."""
        task = await todo_list.create_task(content="Original")
        updated = await todo_list.update_task(task.id, content="Updated")

        assert updated is not None
        assert updated.content == "Updated"
        # updated_at should be >= original (may be equal if update is very fast)
        assert updated.updated_at >= task.created_at

    @pytest.mark.asyncio
    async def test_update_task_status(self, todo_list: InMemoryTodoList) -> None:
        """Test updating task status."""
        task = await todo_list.create_task(content="Test")
        updated = await todo_list.update_task(task.id, status=TaskStatus.IN_PROGRESS)

        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, todo_list: InMemoryTodoList) -> None:
        """Test updating a non-existent task."""
        result = await todo_list.update_task("non-existent", content="Updated")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_task(self, todo_list: InMemoryTodoList) -> None:
        """Test deleting a task."""
        task = await todo_list.create_task(content="Test")
        result = await todo_list.delete_task(task.id)
        assert result is True

        retrieved = await todo_list.get_task(task.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, todo_list: InMemoryTodoList) -> None:
        """Test deleting a non-existent task."""
        result = await todo_list.delete_task("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_next_task(self, todo_list: InMemoryTodoList) -> None:
        """Test getting the next available task."""
        await todo_list.create_task(content="Low priority", priority=1)
        await todo_list.create_task(content="High priority", priority=10)

        next_task = await todo_list.get_next_task()
        assert next_task is not None
        assert next_task.content == "High priority"

    @pytest.mark.asyncio
    async def test_get_next_task_with_dependencies(
        self, todo_list: InMemoryTodoList
    ) -> None:
        """Test that tasks with unsatisfied dependencies are skipped."""
        dep_task = await todo_list.create_task(content="Dependency", priority=1)
        await todo_list.create_task(
            content="Dependent task",
            priority=10,
            dependencies=[dep_task.id],
        )
        await todo_list.create_task(content="Independent task", priority=5)

        # Should return independent task since dependent task has unsatisfied deps
        next_task = await todo_list.get_next_task()
        assert next_task is not None
        assert next_task.content == "Independent task"

        # Complete the dependency
        await todo_list.mark_completed(dep_task.id)

        # Now should return the dependent task (higher priority)
        next_task = await todo_list.get_next_task()
        assert next_task is not None
        assert next_task.content == "Dependent task"

    @pytest.mark.asyncio
    async def test_get_next_task_empty(self, todo_list: InMemoryTodoList) -> None:
        """Test getting next task from empty list."""
        next_task = await todo_list.get_next_task()
        assert next_task is None

    @pytest.mark.asyncio
    async def test_get_next_task_all_completed(
        self, todo_list: InMemoryTodoList
    ) -> None:
        """Test getting next task when all are completed."""
        task = await todo_list.create_task(content="Test")
        await todo_list.mark_completed(task.id)

        next_task = await todo_list.get_next_task()
        assert next_task is None

    @pytest.mark.asyncio
    async def test_get_next_task_by_agent(self, todo_list: InMemoryTodoList) -> None:
        """Test getting next task filtered by agent."""
        await todo_list.create_task(content="Agent 1 task", agent_id="agent-1", priority=1)
        await todo_list.create_task(content="Agent 2 task", agent_id="agent-2", priority=10)

        next_task = await todo_list.get_next_task(agent_id="agent-1")
        assert next_task is not None
        assert next_task.content == "Agent 1 task"

    @pytest.mark.asyncio
    async def test_mark_in_progress(self, todo_list: InMemoryTodoList) -> None:
        """Test marking a task as in progress."""
        task = await todo_list.create_task(content="Test")
        updated = await todo_list.mark_in_progress(task.id)

        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_mark_completed(self, todo_list: InMemoryTodoList) -> None:
        """Test marking a task as completed."""
        task = await todo_list.create_task(content="Test")
        updated = await todo_list.mark_completed(task.id)

        assert updated is not None
        assert updated.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_mark_failed(self, todo_list: InMemoryTodoList) -> None:
        """Test marking a task as failed."""
        task = await todo_list.create_task(content="Test")
        updated = await todo_list.mark_failed(task.id)

        assert updated is not None
        assert updated.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_mark_blocked(self, todo_list: InMemoryTodoList) -> None:
        """Test marking a task as blocked."""
        task = await todo_list.create_task(content="Test")
        updated = await todo_list.mark_blocked(task.id)

        assert updated is not None
        assert updated.status == TaskStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_clear_all(self, todo_list: InMemoryTodoList) -> None:
        """Test clearing all tasks."""
        await todo_list.create_task(content="Task 1")
        await todo_list.create_task(content="Task 2")
        await todo_list.create_task(content="Task 3")

        count = await todo_list.clear()
        assert count == 3

        tasks = await todo_list.get_tasks()
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_clear_by_agent(self, todo_list: InMemoryTodoList) -> None:
        """Test clearing tasks for a specific agent."""
        await todo_list.create_task(content="Agent 1 task 1", agent_id="agent-1")
        await todo_list.create_task(content="Agent 1 task 2", agent_id="agent-1")
        await todo_list.create_task(content="Agent 2 task", agent_id="agent-2")

        count = await todo_list.clear(agent_id="agent-1")
        assert count == 2

        tasks = await todo_list.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].agent_id == "agent-2"
