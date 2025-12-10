"""SQLite storage strategy for todo-ai."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from todo_ai.base import TodoList
from todo_ai.models import Task, TaskStatus


class SQLiteTodoList(TodoList):
    """SQLite-based implementation of TodoList.

    This strategy persists tasks to a SQLite database file. Good for
    single-agent deployments or local development where persistence
    is needed without an external database server.
    """

    def __init__(self, db_path: str | Path = "todo_ai.db") -> None:
        """Initialize the SQLite todo list.

        Args:
            db_path: Path to the SQLite database file. Use ":memory:" for
                     an in-memory database (useful for testing).
        """
        self._db_path = str(db_path)
        self._initialized = False
        # For in-memory databases, we need to keep a persistent connection
        # because each new connection to :memory: creates a fresh database
        self._persistent_conn: aiosqlite.Connection | None = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a database connection.

        For in-memory databases, returns a persistent connection.
        For file-based databases, creates a new connection each time.
        """
        if self._db_path == ":memory:":
            if self._persistent_conn is None:
                self._persistent_conn = await aiosqlite.connect(self._db_path)
            return self._persistent_conn
        return await aiosqlite.connect(self._db_path)

    async def _close_connection(self, conn: aiosqlite.Connection) -> None:
        """Close a connection if it's not the persistent one."""
        if self._db_path != ":memory:":
            await conn.close()

    async def _ensure_initialized(self) -> None:
        """Ensure the database schema is created."""
        if self._initialized:
            return

        conn = await self._get_connection()
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority INTEGER NOT NULL DEFAULT 0,
                    agent_id TEXT,
                    dependencies TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            """)
            await conn.commit()
        finally:
            await self._close_connection(conn)

        self._initialized = True

    def _row_to_task(self, row: aiosqlite.Row) -> Task:
        """Convert a database row to a Task object."""
        return Task(
            id=row["id"],
            content=row["content"],
            status=TaskStatus(row["status"]),
            priority=row["priority"],
            agent_id=row["agent_id"],
            dependencies=json.loads(row["dependencies"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def create_task(
        self,
        content: str,
        priority: int = 0,
        agent_id: str | None = None,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a new task."""
        await self._ensure_initialized()

        task = Task(
            content=content,
            priority=priority,
            agent_id=agent_id,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                INSERT INTO tasks (id, content, status, priority, agent_id,
                                   dependencies, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.content,
                    task.status.value,
                    task.priority,
                    task.agent_id,
                    json.dumps(task.dependencies),
                    json.dumps(task.metadata),
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                ),
            )
            await conn.commit()
        finally:
            await self._close_connection(conn)

        return task

    async def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        await self._ensure_initialized()

        conn = await self._get_connection()
        try:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_task(row)
        finally:
            await self._close_connection(conn)

    async def get_tasks(
        self,
        agent_id: str | None = None,
        status: TaskStatus | None = None,
        limit: int | None = None,
    ) -> list[Task]:
        """Get tasks with optional filtering."""
        await self._ensure_initialized()

        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[Any] = []

        if agent_id is not None:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if status is not None:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY priority DESC, created_at ASC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        conn = await self._get_connection()
        try:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_task(row) for row in rows]
        finally:
            await self._close_connection(conn)

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
        await self._ensure_initialized()

        # First check if task exists
        task = await self.get_task(task_id)
        if task is None:
            return None

        # Build update query
        updates: list[str] = []
        params: list[Any] = []

        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if status is not None:
            updates.append("status = ?")
            params.append(status.value)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if dependencies is not None:
            updates.append("dependencies = ?")
            params.append(json.dumps(dependencies))
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))

        if not updates:
            return task

        # Always update updated_at
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())

        params.append(task_id)

        conn = await self._get_connection()
        try:
            await conn.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            await conn.commit()
        finally:
            await self._close_connection(conn)

        return await self.get_task(task_id)

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        await self._ensure_initialized()

        conn = await self._get_connection()
        try:
            cursor = await conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await conn.commit()
            return cursor.rowcount > 0
        finally:
            await self._close_connection(conn)

    async def get_next_task(self, agent_id: str | None = None) -> Task | None:
        """Get the next available task to work on."""
        await self._ensure_initialized()

        # Get all completed task IDs for dependency checking
        completed_ids: set[str] = set()
        conn = await self._get_connection()
        try:
            async with conn.execute(
                "SELECT id FROM tasks WHERE status = ?", (TaskStatus.COMPLETED.value,)
            ) as cursor:
                rows = await cursor.fetchall()
                completed_ids = {row[0] for row in rows}
        finally:
            await self._close_connection(conn)

        # Get all pending tasks
        tasks = await self.get_tasks(agent_id=agent_id, status=TaskStatus.PENDING)

        # Filter to only available tasks (dependencies satisfied)
        available_tasks = [t for t in tasks if t.is_available(completed_ids)]

        # Return highest priority (already sorted)
        return available_tasks[0] if available_tasks else None

    async def clear(self, agent_id: str | None = None) -> int:
        """Clear all tasks."""
        await self._ensure_initialized()

        conn = await self._get_connection()
        try:
            if agent_id is None:
                cursor = await conn.execute("DELETE FROM tasks")
            else:
                cursor = await conn.execute(
                    "DELETE FROM tasks WHERE agent_id = ?", (agent_id,)
                )
            await conn.commit()
            return cursor.rowcount
        finally:
            await self._close_connection(conn)
