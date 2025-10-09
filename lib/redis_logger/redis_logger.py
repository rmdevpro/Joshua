"""
Non-blocking, queue-based logger using Redis.

This module provides a robust logging class that sends structured logs to a
Redis list, which acts as a queue. It features automatic fallback to local
stdout logging if Redis is unavailable, and recursive redaction of sensitive
data.
"""
import datetime
import json
import sys
from typing import Any, Dict, List, Optional, Set

import redis

# Define log levels numerically for easy comparison
LEVELS: Dict[str, int] = {"TRACE": 5, "DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
DEFAULT_REDACT_FIELDS: List[str] = ['password', 'token', 'api_key', 'authorization', 'secret']
REDACTED_VALUE: str = "[REDACTED]"


class RedisLogger:
    """
    A non-blocking logger that sends logs to Godot via a Redis queue.

    This logger is designed for high-throughput services. It pushes log entries
    to a Redis list and relies on a separate consumer (like Godot) to process
    them. If Redis is unavailable, it gracefully falls back to logging to
    standard output.
    """

    def __init__(
        self,
        component: str,
        redis_url: str = "redis://localhost:6379",
        default_level: str = "INFO",
        redact_fields: Optional[List[str]] = None,
        max_queue_size: int = 100000,
        log_queue_name: str = "logs:queue",
    ):
        """
        Initializes the RedisLogger instance.

        Args:
            component: The name of the component or service.
            redis_url: The connection URL for the Redis server.
            default_level: The default logging level (e.g., "INFO").
            redact_fields: A list of additional field names to redact.
            max_queue_size: The maximum number of entries in the Redis queue.
                            Older entries are dropped if the limit is exceeded.
            log_queue_name: The name of the Redis list to use as a log queue.
        """
        self.component: str = component
        self.level: int = LEVELS.get(default_level.upper(), LEVELS["INFO"])
        self.redact_fields: Set[str] = set((redact_fields or []) + DEFAULT_REDACT_FIELDS)
        self.max_queue_size: int = max_queue_size
        self.log_queue_name: str = log_queue_name
        self.redis_client: Optional[redis.Redis] = None
        self.script_sha: Optional[str] = None
        self._redis_available: bool = False

        try:
            self.redis_client = redis.from_url(
                redis_url, socket_connect_timeout=1, decode_responses=True
            )
            self.redis_client.ping()
            self._redis_available = True
            self._load_lua_script()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            self._log_fallback_warning(
                f"Could not connect to Redis at {redis_url}. Reason: {e}. "
                "Falling back to local stdout logging."
            )

    def _load_lua_script(self) -> None:
        """Loads a Lua script for atomic, capped FIFO queue management."""
        if not self.redis_client:
            return
        # This script ensures that pushing to the queue and trimming it to
        # max_queue_size is an atomic operation.
        script = """
        local queue = KEYS[1]
        local max_size = tonumber(ARGV[1])
        local log_entry = ARGV[2]

        -- Trim the queue by popping from the right (oldest) if oversized
        local current_size = redis.call('LLEN', queue)
        if current_size >= max_size then
            redis.call('RPOP', queue)
        end
        -- Push the new entry to the left (newest)
        redis.call('LPUSH', queue, log_entry)
        return redis.call('LLEN', queue)
        """
        self.script_sha = self.redis_client.script_load(script)

    def set_level(self, level: str) -> None:
        """Dynamically changes the current log level."""
        new_level = LEVELS.get(level.upper())
        if new_level is not None:
            self.level = new_level
        else:
            self._log_fallback_warning(f"Invalid log level '{level}'. Level not changed.")

    def _redact(self, data: Any) -> Any:
        """Recursively redacts sensitive fields from a dictionary or list."""
        if isinstance(data, dict):
            clean_data = {}
            for key, value in data.items():
                if isinstance(key, str) and key.lower() in self.redact_fields:
                    clean_data[key] = REDACTED_VALUE
                else:
                    clean_data[key] = self._redact(value)
            return clean_data
        elif isinstance(data, list):
            # FIXED: Corrected iteration over `data` instead of undefined `value`.
            return [self._redact(item) for item in data]
        else:
            return data

    def _log(
        self,
        level_name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """Internal log handler to format and dispatch log entries."""
        level_num = LEVELS[level_name]
        if level_num < self.level:
            return  # Filter logs below the current level

        log_entry = {
            "component": self.component,
            "level": level_name,
            "message": message,
            "trace_id": trace_id,
            "data": self._redact(data) if data else None,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        if not self._redis_available or not self.redis_client or not self.script_sha:
            self._log_local(log_entry)
            return

        try:
            # Use the loaded Lua script for atomic FIFO queue management
            self.redis_client.evalsha(
                self.script_sha,
                1,
                self.log_queue_name,
                self.max_queue_size,
                json.dumps(log_entry),
            )
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            # Fallback on any Redis failure during the operation
            self._redis_available = False
            self._log_fallback_warning(
                f"Redis connection failed. Reason: {e}. Falling back to local stdout logging."
            )
            self._log_local(log_entry)

    def _log_fallback_warning(self, message: str) -> None:
        """Logs a warning to stderr indicating a fallback to local logging."""
        print(f"[RedisLogger WARNING] {self.component}: {message}", file=sys.stderr)

    def _log_local(self, log_entry: Dict[str, Any]) -> None:
        """Logs the formatted entry to stdout as a fallback."""
        print(json.dumps(log_entry), file=sys.stdout)

    def trace(self, message: str, data: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
        self._log("TRACE", message, data, trace_id)

    def debug(self, message: str, data: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
        self._log("DEBUG", message, data, trace_id)

    def info(self, message: str, data: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
        self._log("INFO", message, data, trace_id)

    def warn(self, message: str, data: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
        self._log("WARN", message, data, trace_id)

    def error(self, message: str, data: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
        self._log("ERROR", message, data, trace_id)

    def close(self) -> None:
        """Gracefully closes the Redis connection if it exists."""
        if self.redis_client:
            self.redis_client.close()
