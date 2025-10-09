# MCP Logger

**Version:** 1.0.1

An asynchronous, WebSocket-based logging client for sending logs to the Godot MCP.

## Description

This library provides a single, simple async function `log_to_godot` for sending structured log entries to a Godot MCP instance. It is designed to be "fire-and-forget" and will fail silently without raising exceptions to ensure that logging failures do not impact the application's core functionality.

## Usage

Import the `log_to_godot` function and call it from within an `async` context. It is often useful to wrap the call in `asyncio.create_task` to send the log without waiting for it to complete.

### Example

```python
import asyncio
from joshua.lib.mcp_logger import log_to_godot

async def process_request(request_id: str):
    # Log the start of an operation
    await log_to_godot(
        level="INFO",
        message=f"Processing request {request_id}",
        component="my-service",
        trace_id=request_id
    )

    # Do some work...
    await asyncio.sleep(0.5)

    # Log completion
    await log_to_godot(
        level="INFO",
        message=f"Finished processing request {request_id}",
        component="my-service",
        data={"status": "success", "duration_ms": 500},
        trace_id=request_id
    )

async def main():
    # Example of running multiple logging tasks concurrently
    tasks = [process_request(f"req-{i}") for i in range(3)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

### Non-blocking Call Pattern

For applications where you do not want to `await` the logging call, use `asyncio.create_task`:

```python
import asyncio
from joshua.lib.mcp_logger import log_to_godot

async def handle_event(event_data, trace_id):
    # ... some initial logic ...

    # Send a log without blocking the current function's execution
    asyncio.create_task(log_to_godot(
        "TRACE",
        "Event received",
        component="event-handler",
        data=event_data,
        trace_id=trace_id
    ))

    # ... continue with other logic immediately ...
```

## API Reference

`async def log_to_godot(level, message, component, data, trace_id, godot_url, timeout)`

-   `level` (str): The log level (e.g., "ERROR", "WARN", "INFO", "DEBUG").
-   `message` (str): The primary log message.
-   `component` (str, optional): The name of the service. Defaults to `"dewey"`.
-   `data` (dict, optional): A dictionary of structured data. Defaults to `None`.
-   `trace_id` (str, optional): A correlation ID. Defaults to `None`.
-   `godot_url` (str, optional): The WebSocket URL for Godot MCP. Defaults to `"ws://godot-mcp:9060"`.
-   `timeout` (float, optional): Connection and response timeout in seconds. Defaults to `1.0`.
