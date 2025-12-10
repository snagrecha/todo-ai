"""Tests for todo-ai models."""


from todo_ai.models import Task, TaskCreate, TaskStatus, TaskUpdate


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values(self) -> None:
        """Test that all expected status values exist."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.BLOCKED.value == "blocked"


class TestTask:
    """Tests for Task model."""

    def test_create_task_with_defaults(self) -> None:
        """Test creating a task with default values."""
        task = Task(content="Test task")
        assert task.content == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 0
        assert task.agent_id is None
        assert task.dependencies == []
        assert task.metadata == {}
        assert task.id is not None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_create_task_with_all_fields(self) -> None:
        """Test creating a task with all fields specified."""
        task = Task(
            content="Test task",
            status=TaskStatus.IN_PROGRESS,
            priority=5,
            agent_id="agent-1",
            dependencies=["task-1", "task-2"],
            metadata={"key": "value"},
        )
        assert task.content == "Test task"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == 5
        assert task.agent_id == "agent-1"
        assert task.dependencies == ["task-1", "task-2"]
        assert task.metadata == {"key": "value"}

    def test_task_is_available_no_dependencies(self) -> None:
        """Test is_available with no dependencies."""
        task = Task(content="Test task", status=TaskStatus.PENDING)
        assert task.is_available(set()) is True

    def test_task_is_available_with_satisfied_dependencies(self) -> None:
        """Test is_available with satisfied dependencies."""
        task = Task(
            content="Test task",
            status=TaskStatus.PENDING,
            dependencies=["task-1", "task-2"],
        )
        completed_ids = {"task-1", "task-2", "task-3"}
        assert task.is_available(completed_ids) is True

    def test_task_is_available_with_unsatisfied_dependencies(self) -> None:
        """Test is_available with unsatisfied dependencies."""
        task = Task(
            content="Test task",
            status=TaskStatus.PENDING,
            dependencies=["task-1", "task-2"],
        )
        completed_ids = {"task-1"}
        assert task.is_available(completed_ids) is False

    def test_task_is_available_non_pending_status(self) -> None:
        """Test is_available returns False for non-pending tasks."""
        task = Task(content="Test task", status=TaskStatus.IN_PROGRESS)
        assert task.is_available(set()) is False

        task = Task(content="Test task", status=TaskStatus.COMPLETED)
        assert task.is_available(set()) is False

    def test_task_serialization(self) -> None:
        """Test task serialization to dict."""
        task = Task(content="Test task", priority=5)
        data = task.model_dump()
        assert data["content"] == "Test task"
        assert data["priority"] == 5
        assert data["status"] == TaskStatus.PENDING


class TestTaskCreate:
    """Tests for TaskCreate schema."""

    def test_create_with_content_only(self) -> None:
        """Test creating TaskCreate with content only."""
        create = TaskCreate(content="Test task")
        assert create.content == "Test task"
        assert create.priority == 0
        assert create.agent_id is None
        assert create.dependencies == []
        assert create.metadata == {}

    def test_create_with_all_fields(self) -> None:
        """Test creating TaskCreate with all fields."""
        create = TaskCreate(
            content="Test task",
            priority=10,
            agent_id="agent-1",
            dependencies=["dep-1"],
            metadata={"foo": "bar"},
        )
        assert create.content == "Test task"
        assert create.priority == 10
        assert create.agent_id == "agent-1"
        assert create.dependencies == ["dep-1"]
        assert create.metadata == {"foo": "bar"}


class TestTaskUpdate:
    """Tests for TaskUpdate schema."""

    def test_update_empty(self) -> None:
        """Test creating empty TaskUpdate."""
        update = TaskUpdate()
        assert update.content is None
        assert update.status is None
        assert update.priority is None
        assert update.dependencies is None
        assert update.metadata is None

    def test_update_with_fields(self) -> None:
        """Test creating TaskUpdate with fields."""
        update = TaskUpdate(
            content="Updated content",
            status=TaskStatus.COMPLETED,
            priority=5,
        )
        assert update.content == "Updated content"
        assert update.status == TaskStatus.COMPLETED
        assert update.priority == 5
