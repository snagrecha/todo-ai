"""MCP server for todo-ai.

This module provides an MCP (Model Context Protocol) server that exposes
todo-ai functionality to AI agents and other MCP clients.
"""

import argparse
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from todo_ai.base import TodoList
from todo_ai.factory import create_todo_list, get_available_strategies
from todo_ai.models import TaskStatus


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncIterator[dict[str, TodoList]]:
    """Lifespan context manager for the MCP server."""
    # Get configuration from environment variables
    strategy = os.environ.get("TODO_AI_STRATEGY", "memory")
    db_path = os.environ.get("TODO_AI_DB_PATH", "todo_ai.db")

    # Create the todo list instance
    if strategy == "sqlite":
        todo_list = create_todo_list(strategy, db_path=db_path)
    else:
        todo_list = create_todo_list(strategy)

    yield {"todo_list": todo_list}


# Create the MCP server
mcp = FastMCP(
    name="todo-ai",
    instructions="""
    todo-ai is a task list management system for AI agents.

    Use these tools to manage tasks:
    - create_task: Create a new task
    - get_task: Get a task by ID
    - list_tasks: List all tasks with optional filtering
    - update_task: Update a task's properties
    - delete_task: Delete a task
    - get_next_task: Get the next available task to work on
    - mark_in_progress: Mark a task as in progress
    - mark_completed: Mark a task as completed
    - mark_failed: Mark a task as failed
    - clear_tasks: Clear all tasks
    """,
    lifespan=lifespan,
)


def _get_todo_list() -> TodoList:
    """Get the todo list from the current context."""
    ctx = mcp.get_context()
    todo_list: TodoList = ctx.request_context.lifespan_context["todo_list"]
    return todo_list


@mcp.tool()
async def create_task(
    content: str,
    priority: int = 0,
    agent_id: str | None = None,
    dependencies: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new task.

    Args:
        content: The task description/content
        priority: Priority level (higher = more important, default 0)
        agent_id: ID of the agent this task belongs to (optional)
        dependencies: List of task IDs that must complete first (optional)
        metadata: Arbitrary metadata for the task (optional)

    Returns:
        The created task as a dictionary
    """
    todo_list = _get_todo_list()
    task = await todo_list.create_task(
        content=content,
        priority=priority,
        agent_id=agent_id,
        dependencies=dependencies,
        metadata=metadata,
    )
    return task.model_dump(mode="json")


@mcp.tool()
async def get_task(task_id: str) -> dict[str, Any] | None:
    """Get a task by ID.

    Args:
        task_id: The ID of the task to retrieve

    Returns:
        The task as a dictionary, or None if not found
    """
    todo_list = _get_todo_list()
    task = await todo_list.get_task(task_id)
    if task is None:
        return None
    return task.model_dump(mode="json")


@mcp.tool()
async def list_tasks(
    agent_id: str | None = None,
    status: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """List tasks with optional filtering.

    Args:
        agent_id: Filter by agent ID (optional)
        status: Filter by task status: pending, in_progress, completed, failed, blocked (optional)
        limit: Maximum number of tasks to return (optional)

    Returns:
        List of tasks as dictionaries
    """
    todo_list = _get_todo_list()
    task_status = TaskStatus(status) if status else None
    tasks = await todo_list.get_tasks(agent_id=agent_id, status=task_status, limit=limit)
    return [task.model_dump(mode="json") for task in tasks]


@mcp.tool()
async def update_task(
    task_id: str,
    content: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    dependencies: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Update a task.

    Args:
        task_id: The ID of the task to update
        content: New task content (optional)
        status: New task status: pending, in_progress, completed, failed, blocked (optional)
        priority: New priority level (optional)
        dependencies: New list of dependencies (optional)
        metadata: New metadata (replaces existing, optional)

    Returns:
        The updated task as a dictionary, or None if not found
    """
    todo_list = _get_todo_list()
    task_status = TaskStatus(status) if status else None
    task = await todo_list.update_task(
        task_id=task_id,
        content=content,
        status=task_status,
        priority=priority,
        dependencies=dependencies,
        metadata=metadata,
    )
    if task is None:
        return None
    return task.model_dump(mode="json")


@mcp.tool()
async def delete_task(task_id: str) -> bool:
    """Delete a task.

    Args:
        task_id: The ID of the task to delete

    Returns:
        True if the task was deleted, False if not found
    """
    todo_list = _get_todo_list()
    return await todo_list.delete_task(task_id)


@mcp.tool()
async def get_next_task(agent_id: str | None = None) -> dict[str, Any] | None:
    """Get the next available task to work on.

    Returns the highest priority task that is:
    - In PENDING status
    - Has all dependencies completed

    Args:
        agent_id: Filter by agent ID (optional)

    Returns:
        The next available task as a dictionary, or None if no tasks are available
    """
    todo_list = _get_todo_list()
    task = await todo_list.get_next_task(agent_id=agent_id)
    if task is None:
        return None
    return task.model_dump(mode="json")


@mcp.tool()
async def mark_in_progress(task_id: str) -> dict[str, Any] | None:
    """Mark a task as in progress.

    Args:
        task_id: The ID of the task

    Returns:
        The updated task as a dictionary, or None if not found
    """
    todo_list = _get_todo_list()
    task = await todo_list.mark_in_progress(task_id)
    if task is None:
        return None
    return task.model_dump(mode="json")


@mcp.tool()
async def mark_completed(task_id: str) -> dict[str, Any] | None:
    """Mark a task as completed.

    Args:
        task_id: The ID of the task

    Returns:
        The updated task as a dictionary, or None if not found
    """
    todo_list = _get_todo_list()
    task = await todo_list.mark_completed(task_id)
    if task is None:
        return None
    return task.model_dump(mode="json")


@mcp.tool()
async def mark_failed(task_id: str) -> dict[str, Any] | None:
    """Mark a task as failed.

    Args:
        task_id: The ID of the task

    Returns:
        The updated task as a dictionary, or None if not found
    """
    todo_list = _get_todo_list()
    task = await todo_list.mark_failed(task_id)
    if task is None:
        return None
    return task.model_dump(mode="json")


@mcp.tool()
async def mark_blocked(task_id: str) -> dict[str, Any] | None:
    """Mark a task as blocked.

    Args:
        task_id: The ID of the task

    Returns:
        The updated task as a dictionary, or None if not found
    """
    todo_list = _get_todo_list()
    task = await todo_list.mark_blocked(task_id)
    if task is None:
        return None
    return task.model_dump(mode="json")


@mcp.tool()
async def clear_tasks(agent_id: str | None = None) -> int:
    """Clear all tasks.

    Args:
        agent_id: If provided, only clear tasks for this agent (optional)

    Returns:
        Number of tasks deleted
    """
    todo_list = _get_todo_list()
    return await todo_list.clear(agent_id=agent_id)


def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="todo-ai MCP server")
    parser.add_argument(
        "--strategy",
        choices=get_available_strategies(),
        default="memory",
        help="Storage strategy to use (default: memory)",
    )
    parser.add_argument(
        "--db-path",
        default="todo_ai.db",
        help="Path to SQLite database (only used with sqlite strategy)",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport to use (default: stdio)",
    )
    args = parser.parse_args()

    # Set environment variables for the lifespan context
    os.environ["TODO_AI_STRATEGY"] = args.strategy
    os.environ["TODO_AI_DB_PATH"] = args.db_path

    # Run the server
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()
