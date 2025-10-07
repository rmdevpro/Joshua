Here is the complete implementation of the Godot unified logging infrastructure, following all specified requirements.

### File Structure Overview

```
.
├── godot/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── redis.conf
│   ├── README.md
│   └── src/
│       ├── __init__.py
│       ├── config.py
│       ├── mcp_server.py
│       └── worker.py
├── dewey/
│   ├── docker-compose.yml.patch
│   ├── db/
│   │   └── schema.sql
│   └── src/
│       └── tools.py
├── client_libs/
│   ├── python/
│   │   ├── godot/
│   │   │   ├── __init__.py
│   │   │   └── loglib.py
│   │   └── setup.py
│   └── javascript/
│       ├── loglib.js
│       └── package.json
└── docs/
    └── integration_guide.md
```

---

### 1. Godot Container (Redis + Worker + MCP Server)

#### `godot/docker-compose.yml`

```yaml
version: '3.8'

services:
  godot:
    build: .
    container_name: godot-mcp
    restart: unless-stopped
    ports:
      - "9060:9060" # MCP server port
    environment:
      # Connection to Dewey's MCP server
      - DEWEY_MCP_URL=ws://dewey:8080 # Assumes dewey is the service name on the same network
      - DEWEY_CONNECT_TIMEOUT=30

      # Worker Configuration
      - BATCH_SIZE=100
      - BATCH_TIMEOUT_MS=100
      - RETRY_MAX_ATTEMPTS=5
      - RETRY_INITIAL_DELAY=1
      - RETRY_MAX_DELAY=30

      # Redis Configuration (passed to worker/mcp, not redis itself)
      - REDIS_HOST=localhost # Redis runs inside the same container
      - REDIS_PORT=6379
      - LOG_QUEUE_NAME=logs:queue
      - MAX_QUEUE_SIZE=100000 # Critical REQ-GOD-004 & REQ-PERF-003

    volumes:
      - godot_redis_data:/data
    networks:
      - iccm_network

volumes:
  godot_redis_data:

networks:
  iccm_network:
    driver: bridge
```

#### `godot/Dockerfile`

```Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
# procps is for `ps`, supervisord is for process management
RUN apt-get update && apt-get install -y redis-server supervisor procps && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY src/ /app/src/
COPY redis.conf /etc/redis/redis.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Install Python dependencies
RUN pip install --no-cache-dir "redis>=5.0" "mcp-tools-py>=0.4.0" "httpx>=0.25.0" "asyncio-redis-rate-limit"

# Expose ports
EXPOSE 6379 # Redis
EXPOSE 9060 # MCP Server

# Command to run the application using supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

#### `godot/supervisord.conf`
*(This file is needed to run multiple processes in one container, a simple and robust solution for this use case)*
```ini
[supervisord]
nodaemon=true

[program:redis]
command=redis-server /etc/redis/redis.conf
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:worker]
command=python -u src/worker.py
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autorestart=true
startsecs=5

[program:mcp_server]
command=python -u src/mcp_server.py
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autorestart=true
startsecs=5
```

#### `godot/redis.conf`

```conf
# General
port 6379
bind 127.0.0.1

# Persistence (REQ-REL-001)
appendonly yes
appendfsync everysec
dir /data

# Memory Management
# maxmemory is not set here; the queue is capped by clients/worker logic.
# This avoids Redis evicting other important keys if they are ever used.
# The queue size limit is handled by the worker/client libraries.

# Logging
loglevel notice
logfile ""
```

#### `godot/src/config.py`

```python
import os

# --- Godot General Config ---
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
LOG_QUEUE_NAME = os.environ.get("LOG_QUEUE_NAME", "logs:queue")
MAX_QUEUE_SIZE = int(os.environ.get("MAX_QUEUE_SIZE", 100000)) # REQ-GOD-004, REQ-PERF-003

# --- Worker Config ---
DEWEY_MCP_URL = os.environ.get("DEWEY_MCP_URL", "ws://localhost:8080")
DEWEY_CONNECT_TIMEOUT = int(os.environ.get("DEWEY_CONNECT_TIMEOUT", 30))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 100))
BATCH_TIMEOUT_MS = int(os.environ.get("BATCH_TIMEOUT_MS", 100))
RETRY_MAX_ATTEMPTS = int(os.environ.get("RETRY_MAX_ATTEMPTS", 5))
RETRY_INITIAL_DELAY = int(os.environ.get("RETRY_INITIAL_DELAY", 1))
RETRY_MAX_DELAY = int(os.environ.get("RETRY_MAX_DELAY", 30))

# --- MCP Server Config ---
MCP_PORT = int(os.environ.get("MCP_PORT", 9060))
```

#### `godot/src/worker.py`

```python
import asyncio
import json
import logging
import time
import redis.asyncio as redis
from mcp_tools.mcp_client import MCPClient
import src.config as config

# Godot uses standard logging to stdout, not loglib (REQ-MAINT-002)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [WORKER] %(message)s')

async def send_batch_to_dewey(mcp_client, batch):
    """Sends a batch of logs to Dewey with retry logic."""
    if not batch:
        return
    
    log_entries = [json.loads(item) for item in batch]
    
    delay = config.RETRY_INITIAL_DELAY
    for attempt in range(config.RETRY_MAX_ATTEMPTS):
        try:
            if not mcp_client.is_connected:
                logging.warning("Dewey client disconnected. Attempting to reconnect...")
                await mcp_client.connect()
                logging.info("Reconnected to Dewey.")

            logging.info(f"Sending batch of {len(log_entries)} logs to Dewey.")
            await mcp_client.call_tool("dewey_store_logs_batch", {"logs": log_entries})
            logging.info(f"Successfully sent batch of {len(log_entries)} logs.")
            return
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed to send batch to Dewey: {e}")
            if attempt + 1 == config.RETRY_MAX_ATTEMPTS:
                logging.critical("Max retries reached. Discarding batch.")
                # In a real production system, you might move this to a dead-letter queue.
                # For a debugging tool, dropping is acceptable after many retries.
                break
            
            logging.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, config.RETRY_MAX_DELAY)

async def main():
    """Main worker loop to consume logs from Redis and send to Dewey."""
    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
    mcp_client = MCPClient(config.DEWEY_MCP_URL, timeout=config.DEWEY_CONNECT_TIMEOUT)

    logging.info("Godot worker starting...")
    logging.info(f"Connecting to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}")
    logging.info(f"Connecting to Dewey at {config.DEWEY_MCP_URL}")

    await mcp_client.connect()

    while True:
        try:
            batch = []
            start_time = time.monotonic()

            while len(batch) < config.BATCH_SIZE and (time.monotonic() - start_time) * 1000 < config.BATCH_TIMEOUT_MS:
                try:
                    # Use BRPOP with a short timeout to avoid blocking forever
                    # Timeout is in seconds, so convert from ms
                    timeout = max(0.1, (config.BATCH_TIMEOUT_MS / 1000))
                    result = await redis_client.brpop(config.LOG_QUEUE_NAME, timeout=timeout)
                    if result:
                        _, item = result
                        batch.append(item)
                    else:
                        # Timeout hit, break inner loop to process what we have
                        break
                except redis.ConnectionError as e:
                    logging.error(f"Redis connection error: {e}. Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    # Re-initialize client on connection failure
                    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
                    break # Break inner loop to retry connection

            if batch:
                await send_batch_to_dewey(mcp_client, batch)
            
            # Safety trim to enforce max queue size (REQ-GOD-005, REQ-PERF-003)
            # This acts as a secondary enforcement if clients fail to do so.
            # LTRIM keeps elements from index 0 to MAX_QUEUE_SIZE-1
            await redis_client.ltrim(config.LOG_QUEUE_NAME, 0, config.MAX_QUEUE_SIZE - 1)

        except Exception as e:
            logging.critical(f"Unhandled exception in main worker loop: {e}", exc_info=True)
            await asyncio.sleep(5) # Avoid fast-spinning crash loop

if __name__ == "__main__":
    asyncio.run(main())
```

#### `godot/src/mcp_server.py`

```python
import asyncio
import json
import logging
import redis.asyncio as redis
from mcp_tools.mcp_server import MCPServer
from mcp_tools.mcp_client import MCPClient
import src.config as config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [MCP_SERVER] %(message)s')

redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
dewey_client = MCPClient(config.DEWEY_MCP_URL)

async def logger_log(component: str, level: str, message: str, trace_id: str = None, data: dict = None):
    """Facade tool to push a single log entry to the Redis queue."""
    log_entry = {
        "component": component,
        "level": level.upper(),
        "message": message,
        "trace_id": trace_id,
        "data": data,
        "created_at": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
    }
    await redis_client.lpush(config.LOG_QUEUE_NAME, json.dumps(log_entry))
    # Enforce queue size limit immediately
    await redis_client.ltrim(config.LOG_QUEUE_NAME, 0, config.MAX_QUEUE_SIZE - 1)
    return {"status": "ok", "message": "Log entry queued."}

async def logger_query(**kwargs):
    """Facade tool that calls dewey_query_logs."""
    logging.info(f"Forwarding query to Dewey: {kwargs}")
    return await dewey_client.call_tool("dewey_query_logs", kwargs)

async def logger_clear(**kwargs):
    """Facade tool that calls dewey_clear_logs."""
    logging.info(f"Forwarding clear command to Dewey: {kwargs}")
    return await dewey_client.call_tool("dewey_clear_logs", kwargs)

async def logger_set_level(component: str, level: str):
    """
    Sets the log level for a component.
    NOTE: This implementation stores the config in Redis. Client libraries would
    need to be extended to poll this for dynamic updates. For now, it serves
    as a central config store.
    """
    valid_levels = {'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'}
    if level.upper() not in valid_levels:
        raise ValueError(f"Invalid log level '{level}'. Must be one of {valid_levels}")
    
    await redis_client.hset("logger_config:levels", component, level.upper())
    return {"status": "ok", "message": f"Log level for '{component}' set to '{level.upper()}'."}

async def main():
    logging.info("Starting Godot MCP Server...")
    logging.info(f"Connecting to Dewey at {config.DEWEY_MCP_URL}")
    await dewey_client.connect()
    logging.info("Connected to Dewey.")

    server = MCPServer()
    server.register_tool(logger_log)
    server.register_tool(logger_query)
    server.register_tool(logger_clear)
    server.register_tool(logger_set_level)

    logging.info(f"Godot MCP server listening on port {config.MCP_PORT}")
    await server.start(port=config.MCP_PORT)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 2. Dewey Updates (Log Storage Tools)

#### `dewey/docker-compose.yml.patch`
*Apply this change to Dewey's existing `docker-compose.yml` file.*

```yaml
services:
  dewey:
    # ... existing config ...
    environment:
      # ... existing vars ...
      - LOG_RETENTION_DAYS=7
    networks:
      - iccm_network # Ensure Dewey is on the same network as Godot

# Add this if it doesn't exist
networks:
  iccm_network:
    driver: bridge
```

#### `dewey/db/schema.sql`

```sql
-- Enable UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- REQ-DEW-002: Log entry schema
-- REQ-DEW-005: Partitioning by range on created_at
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trace_id UUID,
    component TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE')),
    message TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create a default partition for safety, though daily partitions are expected
CREATE TABLE logs_default PARTITION OF logs DEFAULT;

-- Indexes for efficient querying (REQ-DEW-006, REQ-DEW-007)
-- Note: Indexes must be created on the partitioned table, and they will be
-- automatically created on new partitions.
CREATE INDEX idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX idx_logs_trace_id ON logs(trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX idx_logs_component_time ON logs(component, created_at DESC);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_message_fts ON logs USING gin(to_tsvector('english', message));
CREATE INDEX idx_logs_data ON logs USING gin(data jsonb_path_ops);

-- Example function and cron job for daily partition management
-- This would typically be managed by an operator or a tool like pg_partman.
-- For this project, we provide a sample function. A cron job in the Dewey
-- container or an external scheduler would call this daily.

CREATE OR REPLACE FUNCTION create_daily_log_partition()
RETURNS void AS $$
DECLARE
    partition_date TEXT;
    partition_name TEXT;
BEGIN
    partition_date := to_char(NOW() + interval '1 day', 'YYYY_MM_DD');
    partition_name := 'logs_' || partition_date;

    IF NOT EXISTS(SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF logs FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            (NOW() + interval '1 day')::date,
            (NOW() + interval '2 days')::date
        );
        RAISE NOTICE 'Created partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- To run daily: SELECT create_daily_log_partition();
```

#### `dewey/src/tools.py`
*(This file should be merged with Dewey's existing `tools.py`)*

```python
import os
import json
import logging
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import execute_values, Json

# Assume db_pool is an existing connection pool for Dewey
# from .database import db_pool

# --- NEW LOGGING TOOLS ---

# REQ-DEW-001: Batch log storage tool
async def dewey_store_logs_batch(logs: list):
    """
    Stores a batch of log entries in the database.
    REQ-DEW-004: Uses a single transaction.
    """
    if not logs:
        return {"status": "ok", "message": "No logs to store."}
    
    # REQ-DEW-003: Validate log levels
    valid_levels = {'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'}
    for log in logs:
        if log.get('level', '').upper() not in valid_levels:
            raise ValueError(f"Invalid log level in batch: {log.get('level')}")

    # Prepare data for execute_values
    insert_data = [
        (
            log.get('trace_id'),
            log.get('component'),
            log.get('level', '').upper(),
            log.get('message'),
            Json(log.get('data')) if log.get('data') else None,
            log.get('created_at', datetime.now(timezone.utc).isoformat())
        ) for log in logs
    ]
    
    query = """
        INSERT INTO logs (trace_id, component, level, message, data, created_at)
        VALUES %s
    """

    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            execute_values(cur, query, insert_data)
        conn.commit()
        return {"status": "ok", "inserted_count": len(insert_data)}
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Failed to batch insert logs: {e}")
        raise
    finally:
        if conn:
            db_pool.putconn(conn)

# REQ-DEW-006: Log query tool
async def dewey_query_logs(
    trace_id: str = None,
    component: str = None,
    level: str = None,
    start_time: str = None,
    end_time: str = None,
    search: str = None,
    limit: int = 100
):
    """Queries logs with various filters."""
    # REQ-DEW-006: Limit clamp
    limit = min(max(1, limit), 1000)

    query_parts = ["SELECT id, trace_id, component, level, message, data, created_at, (NOW() - created_at) as age FROM logs"]
    where_clauses = []
    params = []

    if trace_id:
        where_clauses.append("trace_id = %s")
        params.append(trace_id)
    if component:
        where_clauses.append("component = %s")
        params.append(component)
    if level:
        levels = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR']
        try:
            min_level_index = levels.index(level.upper())
            allowed_levels = levels[min_level_index:]
            where_clauses.append("level = ANY(%s)")
            params.append(allowed_levels)
        except ValueError:
            raise ValueError(f"Invalid level: {level}")
    if start_time:
        where_clauses.append("created_at >= %s")
        params.append(start_time)
    if end_time:
        where_clauses.append("created_at <= %s")
        params.append(end_time)
    if search:
        # REQ-DEW-006: Full-text search
        where_clauses.append("to_tsvector('english', message) @@ websearch_to_tsquery('english', %s)")
        params.append(search)

    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))
    
    query_parts.append("ORDER BY created_at DESC")
    query_parts.append("LIMIT %s")
    params.append(limit)

    final_query = " ".join(query_parts)
    
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(final_query, tuple(params))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            # REQ-DEW-008: Include 'age'
            results = [dict(zip(columns, row)) for row in rows]
            return results
    finally:
        db_pool.putconn(conn)

# REQ-DEW-009: Log clearing tool
async def dewey_clear_logs(before_time: str = None, component: str = None, level: str = None):
    """Clears logs based on criteria, with a default retention policy."""
    where_clauses = []
    params = []

    if before_time:
        where_clauses.append("created_at < %s")
        params.append(before_time)
    else:
        # Default retention policy from env var
        retention_days = int(os.environ.get("LOG_RETENTION_DAYS", 7))
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        where_clauses.append("created_at < %s")
        params.append(cutoff_date.isoformat())

    if component:
        where_clauses.append("component = %s")
        params.append(component)
    if level:
        where_clauses.append("level = %s")
        params.append(level.upper())

    if not where_clauses:
        raise ValueError("clear_logs requires at least one filter to prevent accidental deletion.")

    query = f"DELETE FROM logs WHERE {' AND '.join(where_clauses)}"
    
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            deleted_count = cur.rowcount
        conn.commit()
        return {"status": "ok", "deleted_count": deleted_count}
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)
        
# REQ-DEW-010: Log statistics tool
async def dewey_get_log_stats():
    """Returns statistics about the logs table."""
    queries = {
        "total_count": "SELECT COUNT(*) FROM logs;",
        "count_by_component": "SELECT component, COUNT(*) FROM logs GROUP BY component;",
        "count_by_level": "SELECT level, COUNT(*) FROM logs GROUP BY level;",
        "time_range": "SELECT MIN(created_at), MAX(created_at) FROM logs;",
        "db_size": "SELECT pg_size_pretty(pg_total_relation_size('logs'));"
    }
    
    stats = {}
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(queries["total_count"])
            stats["total_count"] = cur.fetchone()[0]
            
            cur.execute(queries["count_by_component"])
            stats["count_by_component"] = dict(cur.fetchall())
            
            cur.execute(queries["count_by_level"])
            stats["count_by_level"] = dict(cur.fetchall())
            
            cur.execute(queries["time_range"])
            min_ts, max_ts = cur.fetchone()
            stats["oldest_log_at"] = min_ts.isoformat() if min_ts else None
            stats["newest_log_at"] = max_ts.isoformat() if max_ts else None
            
            cur.execute(queries["db_size"])
            stats["estimated_db_size"] = cur.fetchone()[0]
            
        return stats
    finally:
        db_pool.putconn(conn)

```

---

### 3. Client Libraries

#### `client_libs/python/setup.py`

```python
from setuptools import setup, find_packages

setup(
    name="godot-loglib",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "redis>=5.0",
    ],
    description="Godot Unified Logging Client Library for Python",
)
```

#### `client_libs/python/godot/loglib.py`

```python
import os
import sys
import json
import uuid
import datetime
import logging
from typing import Optional, List, Dict, Any

import redis

# Define log levels
LEVELS = {"TRACE": 5, "DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
DEFAULT_REDACT_FIELDS = ['password', 'token', 'api_key', 'authorization', 'secret']
REDACTED_VALUE = "[REDACTED]"

class ICCMLogger:
    """A non-blocking logger that sends logs to Godot via Redis."""

    def __init__(self,
                 component: str,
                 redis_url: str = "redis://localhost:6379",
                 default_level: str = "INFO",
                 redact_fields: Optional[List[str]] = None,
                 max_queue_size: int = 100000,
                 log_queue_name: str = "logs:queue"):
        
        self.component = component
        self.level = LEVELS.get(default_level.upper(), LEVELS["INFO"])
        self.redact_fields = set((redact_fields or []) + DEFAULT_REDACT_FIELDS)
        self.max_queue_size = max_queue_size
        self.log_queue_name = log_queue_name
        
        try:
            self.redis_client = redis.from_url(redis_url, socket_connect_timeout=1, decode_responses=True)
            self.redis_client.ping()
            self._redis_available = True
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            self._redis_available = False
            self.redis_client = None
            self._log_fallback_warning(f"Could not connect to Redis at {redis_url}. Reason: {e}. Falling back to local logging.")

    def set_level(self, level: str):
        """REQ-LIB-005: Dynamically change the log level."""
        new_level = LEVELS.get(level.upper())
        if new_level is not None:
            self.level = new_level
        else:
            self._log_fallback_warning(f"Invalid log level '{level}'. Level not changed.")
            
    def _redact(self, data: Any) -> Any:
        """REQ-SEC-001/002/003: Recursively redact sensitive fields in a dictionary."""
        if not isinstance(data, dict):
            return data
        
        clean_data = {}
        for key, value in data.items():
            if isinstance(key, str) and key.lower() in self.redact_fields:
                clean_data[key] = REDACTED_VALUE
            elif isinstance(value, dict):
                clean_data[key] = self._redact(value)
            elif isinstance(value, list):
                clean_data[key] = [self._redact(item) for item in value]
            else:
                clean_data[key] = value
        return clean_data

    def _log(self, level_name: str, message: str, data: Optional[Dict] = None, trace_id: Optional[str] = None):
        level_num = LEVELS[level_name]
        if level_num < self.level:
            return # REQ-LIB-006: Filter logs below current level

        log_entry = {
            "component": self.component,
            "level": level_name,
            "message": message,
            "trace_id": trace_id, # REQ-COR-004, REQ-COR-005 (handles null)
            "data": self._redact(data) if data else None,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        # REQ-LIB-003: Non-blocking push with local fallback
        if not self._redis_available:
            self._log_local(log_entry)
            return

        try:
            # Atomic push and trim to enforce FIFO drop (REQ-GOD-005)
            # This is a more robust way than checking LLEN first.
            pipe = self.redis_client.pipeline()
            pipe.lpush(self.log_queue_name, json.dumps(log_entry))
            pipe.ltrim(self.log_queue_name, 0, self.max_queue_size - 1)
            pipe.execute()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            # REQ-LIB-004: Fallback on ANY Redis failure
            self._redis_available = False
            self._log_fallback_warning(f"Redis connection failed. Reason: {e}. Falling back to local logging.")
            self._log_local(log_entry)

    def _log_fallback_warning(self, message: str):
        """REQ-LIB-007: Log a warning indicating fallback mode."""
        print(f"[ICCMLogger WARNING] {self.component}: {message}", file=sys.stderr)

    def _log_local(self, log_entry: Dict):
        """Logs to stdout as a fallback."""
        print(json.dumps(log_entry), file=sys.stdout)

    # REQ-LIB-001: Public log methods
    def trace(self, message: str, data: Optional[Dict] = None, trace_id: Optional[str] = None):
        self._log("TRACE", message, data, trace_id)

    def debug(self, message: str, data: Optional[Dict] = None, trace_id: Optional[str] = None):
        self._log("DEBUG", message, data, trace_id)

    def info(self, message: str, data: Optional[Dict] = None, trace_id: Optional[str] = None):
        self._log("INFO", message, data, trace_id)

    def warn(self, message: str, data: Optional[Dict] = None, trace_id: Optional[str] = None):
        self._log("WARN", message, data, trace_id)

    def error(self, message: str, data: Optional[Dict] = None, trace_id: Optional[str] = None):
        self._log("ERROR", message, data, trace_id)
        
    def close(self):
        """Gracefully close the Redis connection."""
        if self.redis_client:
            self.redis_client.close()
```

#### `client_libs/javascript/package.json`

```json
{
  "name": "godot-loglib",
  "version": "1.0.0",
  "description": "Godot Unified Logging Client Library for Node.js",
  "main": "loglib.js",
  "dependencies": {
    "redis": "^4.6.10"
  }
}
```

#### `client_libs/javascript/loglib.js`

```javascript
const redis = require('redis');

const LEVELS = { "TRACE": 5, "DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40 };
const DEFAULT_REDACT_FIELDS = new Set(['password', 'token', 'api_key', 'authorization', 'secret']);
const REDACTED_VALUE = "[REDACTED]";

class ICCMLogger {
    /**
     * A non-blocking logger that sends logs to Godot via Redis.
     * @param {object} options
     * @param {string} options.component - The name of the component logging.
     * @param {string} [options.redisUrl='redis://localhost:6379'] - The Redis connection URL.
     * @param {string} [options.defaultLevel='INFO'] - The default logging level.
     * @param {string[]} [options.redactFields=[]] - Additional fields to redact.
     * @param {number} [options.maxQueueSize=100000] - The maximum size of the Redis log queue.
     * @param {string} [options.logQueueName='logs:queue'] - The name of the Redis list for logs.
     */
    constructor({ component, redisUrl = 'redis://localhost:6379', defaultLevel = 'INFO', redactFields = [], maxQueueSize = 100000, logQueueName = 'logs:queue' }) {
        if (!component) {
            throw new Error('ICCMLogger requires a "component" name.');
        }
        this.component = component;
        this.level = LEVELS[defaultLevel.toUpperCase()] || LEVELS.INFO;
        this.redactFields = new Set([...DEFAULT_REDACT_FIELDS, ...redactFields]);
        this.maxQueueSize = maxQueueSize;
        this.logQueueName = logQueueName;
        this._redisAvailable = false;
        
        this.redisClient = redis.createClient({
            url: redisUrl,
            socket: { connectTimeout: 1000 }
        });

        this.redisClient.on('error', (err) => {
            if (this._redisAvailable) {
                this._logFallbackWarning(`Redis connection error: ${err.message}. Falling back to local logging.`);
            }
            this._redisAvailable = false;
        });

        this.redisClient.on('ready', () => {
            if (!this._redisAvailable) {
                console.log(`[ICCMLogger INFO] ${this.component}: Successfully connected to Redis.`);
            }
            this._redisAvailable = true;
        });

        // Fire-and-forget connection attempt
        this.redisClient.connect().catch(err => {
            this._logFallbackWarning(`Could not connect to Redis at ${redisUrl}. Reason: ${err.message}. Falling back to local logging.`);
        });
    }

    /** REQ-LIB-005: Dynamically change the log level. */
    setLevel(level) {
        const newLevel = LEVELS[level.toUpperCase()];
        if (newLevel !== undefined) {
            this.level = newLevel;
        } else {
            this._logFallbackWarning(`Invalid log level '${level}'. Level not changed.`);
        }
    }

    /** REQ-SEC-001/002/003: Recursively redact sensitive fields. */
    _redact(data) {
        if (data === null || typeof data !== 'object') {
            return data;
        }

        if (Array.isArray(data)) {
            return data.map(item => this._redact(item));
        }

        const cleanData = {};
        for (const key in data) {
            if (Object.prototype.hasOwnProperty.call(data, key)) {
                if (this.redactFields.has(key.toLowerCase())) {
                    cleanData[key] = REDACTED_VALUE;
                } else {
                    cleanData[key] = this._redact(data[key]);
                }
            }
        }
        return cleanData;
    }

    /** Internal log method. */
    async _log(levelName, message, data, traceId) {
        const levelNum = LEVELS[levelName];
        if (levelNum < this.level) {
            return; // REQ-LIB-006: Filter logs below current level
        }

        const logEntry = {
            component: this.component,
            level: levelName,
            message: message,
            trace_id: traceId || null, // REQ-COR-004, REQ-COR-005
            data: data ? this._redact(data) : null,
            created_at: new Date().toISOString()
        };

        // REQ-LIB-003: Non-blocking push with local fallback
        if (!this._redisAvailable) {
            this._logLocal(logEntry);
            return;
        }

        try {
            // REQ-LIB-004: Atomic push and trim
            await this.redisClient.multi()
                .lPush(this.logQueueName, JSON.stringify(logEntry))
                .lTrim(this.logQueueName, 0, this.maxQueueSize - 1)
                .exec();
        } catch (err) {
            this._redisAvailable = false;
            this._logFallbackWarning(`Redis command failed. Reason: ${err.message}. Falling back to local logging.`);
            this._logLocal(logEntry);
        }
    }

    /** REQ-LIB-007: Log a warning indicating fallback mode. */
    _logFallbackWarning(message) {
        console.warn(`[ICCMLogger WARNING] ${this.component}: ${message}`);
    }

    /** Logs to stdout as a fallback. */
    _logLocal(logEntry) {
        console.log(JSON.stringify(logEntry));
    }

    // REQ-LIB-001: Public log methods
    trace(message, data, traceId) { this._log('TRACE', message, data, traceId); }
    debug(message, data, traceId) { this._log('DEBUG', message, data, traceId); }
    info(message, data, traceId) { this._log('INFO', message, data, traceId); }
    warn(message, data, traceId) { this._log('WARN', message, data, traceId); }
    error(message, data, traceId) { this._log('ERROR', message, data, traceId); }

    /** Gracefully close the Redis connection. */
    async close() {
        if (this.redisClient && this.redisClient.isOpen) {
            await this.redisClient.quit();
        }
    }
}

module.exports = { ICCMLogger };
```

---

### 4. Documentation

#### `godot/README.md`

```markdown
# Godot: Unified Logging Infrastructure

Godot provides a centralized logging system for the ICCM platform. It is designed as a debugging tool for small development teams running on a single Docker host.

## Architecture

Godot consists of three main services running within a single Docker container:

1.  **Redis Server**: An in-memory data store that acts as a log queue. It is configured for persistence (AOF) to survive restarts.
2.  **Log Worker**: A Python script that continuously consumes logs from the Redis queue, batches them, and sends them to Dewey for permanent storage. It includes retry logic with exponential backoff to handle Dewey downtime.
3.  **MCP Server**: Exposes a set of facade tools for interacting with the logging system (querying, clearing logs) without directly accessing Dewey.

This architecture decouples log producers (your services) from the log storage system (Dewey), providing a resilient buffer.

## Running Godot

Godot is designed to be run with Docker Compose.

```bash
# From the godot/ directory
docker-compose up --build -d
```

### Environment Variables

| Variable              | Description                                              | Default                  |
| --------------------- | -------------------------------------------------------- | ------------------------ |
| `DEWEY_MCP_URL`       | WebSocket URL for the Dewey MCP server.                  | `ws://dewey:8080`        |
| `BATCH_SIZE`          | Max number of logs to batch before sending to Dewey.     | `100`                    |
| `BATCH_TIMEOUT_MS`    | Max time (ms) to wait before sending an incomplete batch.| `100`                    |
| `MAX_QUEUE_SIZE`      | Max number of logs to buffer in Redis (FIFO drop).       | `100000`                 |
| `RETRY_MAX_ATTEMPTS`  | Max retry attempts for sending a batch to Dewey.         | `5`                      |

## MCP Tools (Port 9060)

Godot provides the following MCP tools as facades to Dewey:

-   **`logger_log(component, level, message, trace_id, data)`**: Manually queue a log entry.
-   **`logger_query(...)`**: Query logs. Accepts the same parameters as `dewey_query_logs` (`trace_id`, `component`, `level`, `search`, etc.).
-   **`logger_clear(...)`**: Clear logs. Accepts the same parameters as `dewey_clear_logs` (`before_time`, `component`).
-   **`logger_set_level(component, level)`**: Sets a log level for a component in a central Redis config. (Note: client libraries do not currently poll this).

---
```

#### `docs/integration_guide.md`

```markdown
# Godot Logging: Integration Guide

This guide explains how to integrate your ICCM component with the Godot unified logging system.

## 1. Adding the Client Library

Choose the library that matches your component's language.

### Python Components (Relay, Dewey, Fiedler)

1.  Add `godot-loglib` to your `requirements.txt` or install it:
    ```bash
    pip install -e /path/to/client_libs/python/
    ```
    *(In a real scenario, this would be published to a private package index)*

2.  Initialize the logger in your application's entry point.

    ```python
    # In your main application file (e.g., app.py)
    import os
    from godot.loglib import ICCMLogger

    # Initialize the logger once and share it
    logger = ICCMLogger(
        component=os.environ.get("COMPONENT_NAME", "my-component"),
        redis_url=os.environ.get("GODOT_REDIS_URL", "redis://godot-mcp:6379"),
        default_level=os.environ.get("LOG_LEVEL", "INFO")
    )
    ```

### JavaScript/Node.js Components (Gates)

1.  Add the `godot-loglib` package to your `package.json` dependencies:
    ```json
    "dependencies": {
      "godot-loglib": "file:../path/to/client_libs/javascript",
      "redis": "^4.6.10"
    }
    ```
    Then run `npm install`.

2.  Initialize the logger in your application's entry point.

    ```javascript
    // In your main application file (e.g., server.js)
    const { ICCMLogger } = require('godot-loglib');

    // Initialize the logger once and share it
    const logger = new ICCMLogger({
        component: process.env.COMPONENT_NAME || 'my-component',
        redisUrl: process.env.GODOT_REDIS_URL || 'redis://godot-mcp:6379',
        defaultLevel: process.env.LOG_LEVEL || 'INFO'
    });
    ```

## 2. Propagating Trace IDs (REQ-COR-002)

To correlate requests across multiple services, you must propagate the `trace_id`. The MCP Relay should generate it, and all other services should extract and use it.

**Example: Express.js Middleware (Gates)**

```javascript
const { v4: uuidv4 } = require('uuid');

app.use((req, res, next) => {
    // Extract trace_id from header, or generate a new one if this is the entry point (e.g., Relay)
    req.traceId = req.headers['x-trace-id'] || uuidv4();
    res.setHeader('X-Trace-ID', req.traceId); // Pass it along in responses
    next();
});
```

**Example: Flask Middleware (Relay)**

```python
import uuid
from flask import request, g

@app.before_request
def before_request_func():
    # Extract trace_id or generate a new one
    trace_id = request.headers.get('X-Trace-ID') or str(uuid.uuid4())
    g.trace_id = trace_id

@app.after_request
def after_request_func(response):
    if hasattr(g, 'trace_id'):
        response.headers['X-Trace-ID'] = g.trace_id
    return response
```

## 3. Using the Logger

Once initialized, you can call the logging methods from anywhere in your application.

**Python Example:**

```python
from flask import g # Assuming Flask context for trace_id
# from my_app import logger # Import the shared logger instance

@app.route('/some-endpoint')
def some_endpoint():
    trace_id = g.get('trace_id')
    
    logger.info("Received request for some-endpoint", trace_id=trace_id)

    try:
        # Business logic...
        result_data = {"key": "value", "secret": "should_be_redacted"}
        logger.debug("Processing complete", data=result_data, trace_id=trace_id)
        return {"status": "ok"}
    except Exception as e:
        logger.error(
            f"An error occurred: {e}",
            data={"error_details": str(e)},
            trace_id=trace_id
        )
        return {"error": "Internal Server Error"}, 500
```

**JavaScript Example:**

```javascript
// const logger = require('./logger'); // Import the shared logger instance

app.post('/some-endpoint', (req, res) => {
    const { traceId } = req; // From middleware

    logger.info("Received request for some-endpoint", null, traceId);

    try {
        // Business logic...
        const resultData = { key: "value", token: "should_be_redacted" };
        logger.debug("Processing complete", resultData, traceId);
        res.json({ status: "ok" });
    } catch (e) {
        logger.error(
            `An error occurred: ${e.message}`,
            { error_details: e.stack },
            traceId
        );
        res.status(500).json({ error: "Internal Server Error" });
    }
});
```

## 4. Local Fallback Mechanism

If the Godot Redis server is unreachable for any reason (network issue, container down), the client library will **automatically** fall back to logging to `stdout` (for the log entry) and `stderr` (for a warning message).

This ensures that:
1.  Your application does not crash due to logging failures.
2.  You do not lose logs during a Godot outage; they will be available in the component's container logs (`docker logs <container_name>`).
3.  You are clearly warned that the central log store may be incomplete.
```
