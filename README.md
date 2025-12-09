# todo-ai

A task list management system for AI agents that helps them perform better over long-horizon tasks. Designed for multi-agent systems similar to those used by Claude, Manus, and other AI assistants.

## Features

- **Multiple Storage Strategies**: Choose from in-memory storage for simple use cases or SQLite for persistence
- **Task Dependencies**: Define task dependencies to ensure proper execution order
- **Priority-Based Scheduling**: Get the next available task based on priority and dependency satisfaction
- **Multi-Agent Support**: Isolate tasks by agent ID for multi-agent systems
- **MCP Server**: Expose task management via Model Context Protocol for easy integration with AI agents
- **Extensible**: Register custom storage strategies for your specific needs

## Installation

```bash
pip install todo-ai
```

Or install from source:

```bash
git clone https://github.com/snagrecha/todo-ai.git
cd todo-ai
pip install -e .
```

## Quick Start

### Python API

```python
import asyncio
from todo_ai import create_todo_list, Task, TaskStatus

async def main():
    # Create an in-memory todo list
    todo = create_todo_list("memory")
    
    # Create tasks
    task1 = await todo.create_task(
        content="Setup database",
        priority=10,
        agent_id="agent-1"
    )
    
    task2 = await todo.create_task(
        content="Run migrations",
        priority=5,
        agent_id="agent-1",
        dependencies=[task1.id]  # This task depends on task1
    )
    
    # Get the next available task (highest priority with satisfied dependencies)
    next_task = await todo.get_next_task(agent_id="agent-1")
    print(f"Next task: {next_task.content}")  # "Setup database"
    
    # Mark task as in progress
    await todo.mark_in_progress(next_task.id)
    
    # Mark task as completed
    await todo.mark_completed(next_task.id)
    
    # Now task2 is available since its dependency is satisfied
    next_task = await todo.get_next_task(agent_id="agent-1")
    print(f"Next task: {next_task.content}")  # "Run migrations"

asyncio.run(main())
```

### Using SQLite for Persistence

```python
from todo_ai import create_todo_list

# Create a SQLite-backed todo list
todo = create_todo_list("sqlite", db_path="my_tasks.db")

# Tasks will persist across restarts
```

## Storage Strategies

### InMemoryTodoList

The simplest storage strategy. Tasks are stored in a Python dictionary and are lost when the process exits. Good for testing and simple use cases.

```python
from todo_ai import create_todo_list

todo = create_todo_list("memory")
```

### SQLiteTodoList

Persists tasks to a SQLite database file. Good for single-agent deployments or local development where persistence is needed without an external database server.

```python
from todo_ai import create_todo_list

# File-based database
todo = create_todo_list("sqlite", db_path="tasks.db")

# In-memory database (useful for testing)
todo = create_todo_list("sqlite", db_path=":memory:")
```

### Custom Strategies

You can register your own storage strategies:

```python
from todo_ai import register_strategy, TodoList

class RedisTodoList(TodoList):
    # Implement all abstract methods
    ...

def create_redis_list(**kwargs):
    return RedisTodoList(**kwargs)

register_strategy("redis", create_redis_list)

# Now you can use it
todo = create_todo_list("redis", host="localhost", port=6379)
```

## Task Model

Tasks have the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique identifier (auto-generated UUID) |
| `content` | `str` | Task description |
| `status` | `TaskStatus` | Current status (pending, in_progress, completed, failed, blocked) |
| `priority` | `int` | Priority level (higher = more important, default 0) |
| `agent_id` | `str \| None` | ID of the agent this task belongs to |
| `dependencies` | `list[str]` | List of task IDs that must complete first |
| `metadata` | `dict` | Arbitrary metadata for the task |
| `created_at` | `datetime` | When the task was created |
| `updated_at` | `datetime` | When the task was last updated |

## API Reference

### TodoList Methods

| Method | Description |
|--------|-------------|
| `create_task(content, priority, agent_id, dependencies, metadata)` | Create a new task |
| `get_task(task_id)` | Get a task by ID |
| `get_tasks(agent_id, status, limit)` | Get tasks with optional filtering |
| `update_task(task_id, content, status, priority, dependencies, metadata)` | Update a task |
| `delete_task(task_id)` | Delete a task |
| `get_next_task(agent_id)` | Get the next available task to work on |
| `mark_in_progress(task_id)` | Mark a task as in progress |
| `mark_completed(task_id)` | Mark a task as completed |
| `mark_failed(task_id)` | Mark a task as failed |
| `mark_blocked(task_id)` | Mark a task as blocked |
| `clear(agent_id)` | Clear all tasks (optionally for a specific agent) |

## MCP Server

todo-ai includes an MCP (Model Context Protocol) server that exposes task management functionality to AI agents and other MCP clients.

### Running the MCP Server

```bash
# Run with in-memory storage (default)
todo-ai-mcp

# Run with SQLite storage
todo-ai-mcp --strategy sqlite --db-path tasks.db

# Run with SSE transport instead of stdio
todo-ai-mcp --transport sse
```

### MCP Server Configuration

You can also configure the server using environment variables:

```bash
export TODO_AI_STRATEGY=sqlite
export TODO_AI_DB_PATH=tasks.db
todo-ai-mcp
```

### Available MCP Tools

The MCP server exposes the following tools:

| Tool | Description |
|------|-------------|
| `create_task` | Create a new task |
| `get_task` | Get a task by ID |
| `list_tasks` | List tasks with optional filtering |
| `update_task` | Update a task |
| `delete_task` | Delete a task |
| `get_next_task` | Get the next available task |
| `mark_in_progress` | Mark a task as in progress |
| `mark_completed` | Mark a task as completed |
| `mark_failed` | Mark a task as failed |
| `mark_blocked` | Mark a task as blocked |
| `clear_tasks` | Clear all tasks |

### Using with Claude Desktop

Add the following to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "todo-ai": {
      "command": "todo-ai-mcp",
      "args": ["--strategy", "sqlite", "--db-path", "/path/to/tasks.db"]
    }
  }
}
```

### Using with Other MCP Clients

The MCP server supports both stdio and SSE transports. Use `--transport stdio` (default) for local integrations or `--transport sse` for HTTP-based integrations.

## Development

### Setup

```bash
git clone https://github.com/snagrecha/todo-ai.git
cd todo-ai
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Linting

```bash
ruff check .
ruff format .
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
