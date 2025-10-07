import os
import sys
import json
import datetime
import logging
from typing import Optional, List, Dict, Any

import redis

# Define log levels
LEVELS = {"TRACE": 5, "DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
DEFAULT_REDACT_FIELDS = ['password', 'token', 'api_key', 'authorization', 'secret']
REDACTED_VALUE = "[REDACTED]"

class ICCMLogger:
    """Non-blocking logger that sends logs to Godot via Redis (REQ-LIB-003)"""

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
            self._load_lua_script()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            self._redis_available = False
            self.redis_client = None
            self._log_fallback_warning(f"Could not connect to Redis at {redis_url}. Reason: {e}. Falling back to local logging.")

    def _load_lua_script(self):
        """Load atomic FIFO queue management script (REQ-GOD-005)"""
        # REQ-PERF-003: Enforce 100,000 entry limit with FIFO drop
        script = """
        local queue = KEYS[1]
        local max_size = tonumber(ARGV[1])
        local log_entry = ARGV[2]

        local current_size = redis.call('LLEN', queue)
        if current_size >= max_size then
            redis.call('RPOP', queue)
        end
        redis.call('LPUSH', queue, log_entry)
        return current_size + 1
        """
        self.script_sha = self.redis_client.script_load(script)

    def set_level(self, level: str):
        """REQ-LIB-005: Dynamically change the log level"""
        new_level = LEVELS.get(level.upper())
        if new_level is not None:
            self.level = new_level
        else:
            self._log_fallback_warning(f"Invalid log level '{level}'. Level not changed.")

    def _redact(self, data: Any) -> Any:
        """REQ-SEC-001/002/003: Recursively redact sensitive fields"""
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
            return  # REQ-LIB-006: Filter logs below current level

        log_entry = {
            "component": self.component,
            "level": level_name,
            "message": message,
            "trace_id": trace_id,  # REQ-COR-004, REQ-COR-005
            "data": self._redact(data) if data else None,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        # REQ-LIB-003: Non-blocking push with local fallback
        if not self._redis_available:
            self._log_local(log_entry)
            return

        try:
            # Use Lua script for atomic FIFO queue management
            self.redis_client.evalsha(
                self.script_sha,
                1,
                self.log_queue_name,
                self.max_queue_size,
                json.dumps(log_entry)
            )
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            # REQ-LIB-004: Fallback on ANY Redis failure
            self._redis_available = False
            self._log_fallback_warning(f"Redis connection failed. Reason: {e}. Falling back to local logging.")
            self._log_local(log_entry)

    def _log_fallback_warning(self, message: str):
        """REQ-LIB-007: Log a warning indicating fallback mode"""
        print(f"[ICCMLogger WARNING] {self.component}: {message}", file=sys.stderr)

    def _log_local(self, log_entry: Dict):
        """Logs to stdout as a fallback"""
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
        """Gracefully close the Redis connection"""
        if self.redis_client:
            self.redis_client.close()
