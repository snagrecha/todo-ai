"""todo-ai: A task list management system for AI agents."""

from todo_ai.base import TodoList
from todo_ai.factory import create_todo_list, register_strategy
from todo_ai.models import Task, TaskStatus

__version__ = "0.1.0"

__all__ = [
    "Task",
    "TaskStatus",
    "TodoList",
    "create_todo_list",
    "register_strategy",
]
