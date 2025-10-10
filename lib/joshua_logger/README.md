# joshua_logger

Centralized logging library for Joshua components. Sends structured logs to Godot MCP service via WebSocket.

## Version

v1.0.0

## Features

- **Asynchronous logging** via WebSocket (non-blocking)
- **Fault-tolerant**: Never crashes the application on logging failures
- **Structured logging**: Supports metadata and trace IDs
- **Auto-reconnection**: Uses `joshua_network.Client` for robust connection management

## Installation

```python
# Add to your Python path
sys.path.insert(0, '/mnt/projects/Joshua/lib')
from joshua_logger import logger
```

## Usage

```python
import asyncio
from joshua_logger import logger

# Basic log
await logger.log("INFO", "Application started", "my-component")

# With structured data
await logger.log(
    "ERROR",
    "Database connection failed",
    "my-component",
    data={"host": "localhost", "port": 5432}
)

# With trace ID for request tracking
await logger.log(
    "DEBUG",
    "Processing request",
    "my-component",
    data={"request_id": "123"},
    trace_id="trace-abc-123"
)
```

## API Reference

### `logger.log(level, message, component, data=None, trace_id=None)`

Sends a structured log message to Godot.

**Parameters:**
- `level` (str): Log level - "TRACE", "DEBUG", "INFO", "WARN", "ERROR"
- `message` (str): The log message
- `component` (str): Name of the component generating the log
- `data` (dict, optional): Structured metadata (must be JSON-serializable)
- `trace_id` (str, optional): Request/operation trace ID for correlation

**Returns:** None (fire-and-forget)

## ⚠️ CRITICAL: Migration Guide

When migrating existing code to use joshua_logger, **you must use keyword arguments** for optional parameters:

### ✅ CORRECT
```python
await logger.log("INFO", "Message", "component", data={...}, trace_id="123")
```

### ❌ INCORRECT
```python
await logger.log("INFO", "Message", "component", {...}, "123")
# This will fail with: "Logger.log() takes from 4 to 6 positional arguments but 7 were given"
```

### Common Migration Patterns

**Pattern 1: Simple log (no metadata)**
```python
# Old custom logger
await custom_logger.log("INFO", "Message", "component")

# joshua_logger
await logger.log("INFO", "Message", "component")
```

**Pattern 2: Log with metadata**
```python
# Old custom logger (positional)
await custom_logger.log("ERROR", "Failed", "component", {"key": "value"})

# joshua_logger (keyword argument)
await logger.log("ERROR", "Failed", "component", data={"key": "value"})
```

**Pattern 3: Log with trace ID**
```python
# Old custom logger (positional)
await custom_logger.log("DEBUG", "Processing", "component", {}, trace_id)

# joshua_logger (keyword arguments)
await logger.log("DEBUG", "Processing", "component", data={}, trace_id=trace_id)
```

**Pattern 4: Fire-and-forget with asyncio.create_task**
```python
# Old (positional)
asyncio.create_task(logger.log("INFO", "Event", "component", {"data": "x"}, trace_id))

# New (keyword arguments)
asyncio.create_task(logger.log("INFO", "Event", "component", data={"data": "x"}, trace_id=trace_id))
```

## Configuration

Environment variables:
- `JOSHUA_LOGGER_URL`: WebSocket URL (default: `ws://godot-mcp:9060`)
- `JOSHUA_LOGGER_TIMEOUT`: Request timeout in seconds (default: `2.0`)

## Architecture

```
Your Component
    ↓ (async log call)
joshua_logger.Logger
    ↓ (WebSocket via joshua_network.Client)
Godot MCP Service (port 9060)
    ↓ (Redis queue)
Dewey MCP Service
    ↓ (PostgreSQL)
Database (persistent storage)
```

## Dependencies

- `joshua_network` (v1.0.0+) - WebSocket client with auto-reconnection
- Python 3.8+

## Error Handling

The logger is designed to **fail silently**. If logging fails:
- No exception is raised to the caller
- Error is logged internally via Python's logging module
- Application continues unaffected

This ensures logging issues never crash your application.

## Testing

Verify logs are being stored:

```python
# Send test log
await logger.log("INFO", "Test message", "test-component")

# Query via Godot MCP
# Use mcp__iccm__godot_logger_query tool with component="test-component"
```

## Version History

- **v1.0.0** (2025-10-10): Initial release
  - Fixed tool name: `godot_logger_log` (was `logger_log`)
  - Migrated to `joshua_network.Client`
  - Added comprehensive error handling

## License

Internal Joshua Project component - not for external distribution.
