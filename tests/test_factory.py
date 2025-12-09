"""Tests for todo-ai factory."""

import pytest

from todo_ai.factory import (
    create_todo_list,
    get_available_strategies,
    register_strategy,
)
from todo_ai.strategies.memory import InMemoryTodoList
from todo_ai.strategies.sqlite import SQLiteTodoList


class TestFactory:
    """Tests for the factory module."""

    def test_get_available_strategies(self) -> None:
        """Test getting available strategies."""
        strategies = get_available_strategies()
        assert "memory" in strategies
        assert "sqlite" in strategies

    def test_create_memory_list(self) -> None:
        """Test creating an in-memory todo list."""
        todo_list = create_todo_list("memory")
        assert isinstance(todo_list, InMemoryTodoList)

    def test_create_sqlite_list(self) -> None:
        """Test creating a SQLite todo list."""
        todo_list = create_todo_list("sqlite", db_path=":memory:")
        assert isinstance(todo_list, SQLiteTodoList)

    def test_create_unknown_strategy(self) -> None:
        """Test creating with unknown strategy raises error."""
        with pytest.raises(ValueError) as exc_info:
            create_todo_list("unknown")
        assert "Unknown strategy" in str(exc_info.value)

    def test_register_custom_strategy(self) -> None:
        """Test registering a custom strategy."""

        class CustomTodoList(InMemoryTodoList):
            """Custom todo list for testing."""

            pass

        def create_custom(**kwargs: object) -> CustomTodoList:
            return CustomTodoList()

        register_strategy("custom", create_custom)

        strategies = get_available_strategies()
        assert "custom" in strategies

        todo_list = create_todo_list("custom")
        assert isinstance(todo_list, CustomTodoList)

    def test_default_strategy_is_memory(self) -> None:
        """Test that default strategy is memory."""
        todo_list = create_todo_list()
        assert isinstance(todo_list, InMemoryTodoList)
