"""Factory for creating TodoList instances."""

from collections.abc import Callable
from typing import Any

from todo_ai.base import TodoList
from todo_ai.strategies.memory import InMemoryTodoList
from todo_ai.strategies.sqlite import SQLiteTodoList

# Type alias for strategy factory functions
StrategyFactory = Callable[..., TodoList]

# Registry of available strategies
_strategies: dict[str, StrategyFactory] = {}


def register_strategy(name: str, factory: StrategyFactory) -> None:
    """Register a new storage strategy.

    Args:
        name: The name of the strategy (e.g., "memory", "sqlite")
        factory: A callable that creates a TodoList instance

    Example:
        >>> def create_redis_list(**kwargs):
        ...     return RedisTodoList(**kwargs)
        >>> register_strategy("redis", create_redis_list)
    """
    _strategies[name] = factory


def get_available_strategies() -> list[str]:
    """Get a list of all registered strategy names.

    Returns:
        List of strategy names
    """
    return list(_strategies.keys())


def create_todo_list(strategy: str = "memory", **kwargs: Any) -> TodoList:
    """Create a TodoList instance using the specified strategy.

    Args:
        strategy: The name of the strategy to use. Built-in options:
            - "memory": In-memory storage (default)
            - "sqlite": SQLite database storage
        **kwargs: Additional arguments passed to the strategy factory

    Returns:
        A TodoList instance

    Raises:
        ValueError: If the strategy is not registered

    Example:
        >>> # Create an in-memory todo list
        >>> todo = create_todo_list("memory")
        >>>
        >>> # Create a SQLite-backed todo list
        >>> todo = create_todo_list("sqlite", db_path="my_tasks.db")
    """
    if strategy not in _strategies:
        available = ", ".join(_strategies.keys())
        raise ValueError(
            f"Unknown strategy: {strategy}. Available strategies: {available}"
        )

    return _strategies[strategy](**kwargs)


# Register built-in strategies
def _create_memory_list(**kwargs: Any) -> InMemoryTodoList:
    """Create an in-memory todo list."""
    return InMemoryTodoList()


def _create_sqlite_list(**kwargs: Any) -> SQLiteTodoList:
    """Create a SQLite-backed todo list."""
    db_path = kwargs.get("db_path", "todo_ai.db")
    return SQLiteTodoList(db_path=db_path)


register_strategy("memory", _create_memory_list)
register_strategy("sqlite", _create_sqlite_list)
