# Redis Logger

**Version:** 1.0.1

A non-blocking, queue-based logger that sends structured logs to a Redis instance for consumption by Godot or other services.

## Description

This library provides a `RedisLogger` class that is ideal for high-throughput applications. Instead of logging directly to a destination, it pushes JSON-formatted log entries to a Redis list (acting as a queue). This decouples the application from the logging infrastructure, improving performance and resilience.

## Features

-   **Non-blocking:** Pushes logs to Redis quickly without waiting for a remote service.
-   **Resilient:** Automatically and gracefully falls back to logging to `stdout` if the Redis connection fails.
-   **Capped Queue:** Uses an atomic Lua script to ensure the log queue in Redis does not grow indefinitely, preventing memory issues.
-   **Data Redaction:** Automatically redacts sensitive fields (e.g., 'password', 'token') from structured log data.
-   **Structured Logging:** All logs are formatted as JSON objects.

## Usage

Instantiate the `RedisLogger` once per application/component and use its methods to log messages at different levels.

### Example

```python
from joshua.lib.redis_logger import RedisLogger
import time
import os

# Get Redis URL from environment or use a default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize the logger for your component
logger = RedisLogger(
    component="data-processor",
    redis_url=REDIS_URL,
    default_level="INFO"
)

def process_data(payload: dict, trace_id: str):
    logger.info(
        "Starting data processing",
        data={"record_count": len(payload.get("records", []))},
        trace_id=trace_id
    )

    try:
        # Simulate work
        time.sleep(0.1)
        if "api_key" in payload:
            # The logger will automatically redact the 'api_key' field
            logger.debug("Payload contains sensitive key", data=payload, trace_id=trace_id)

        # Simulate an error
        if len(payload.get("records", [])) == 0:
            raise ValueError("No records found in payload")

        logger.info("Data processing successful", trace_id=trace_id)

    except Exception as e:
        logger.error(
            f"Data processing failed: {e}",
            data={"error_type": type(e).__name__},
            trace_id=trace_id
        )

if __name__ == "__main__":
    process_data({"records": [1, 2, 3], "api_key": "secret123"}, "trace-abc-123")
    process_data({"records": []}, "trace-def-456")

    # Gracefully close the connection on application shutdown
    logger.close()
```

## Configuration

The `RedisLogger` is configured during instantiation:

`logger = RedisLogger(component, redis_url, default_level, redact_fields, max_queue_size, log_queue_name)`

-   `component` (str): **Required.** The name of your service or component.
-   `redis_url` (str): The Redis connection URL. Defaults to `"redis://localhost:6379"`.
-   `default_level` (str): The minimum log level to process. Defaults to `"INFO"`. Can be changed later with `logger.set_level("DEBUG")`.
-   `redact_fields` (list[str], optional): A list of additional dictionary keys to redact.
-   `max_queue_size` (int): The maximum number of log entries to keep in the Redis queue. Defaults to `100,000`.
-   `log_queue_name` (str): The name of the Redis list to use as a queue. Defaults to `"logs:queue"`.
