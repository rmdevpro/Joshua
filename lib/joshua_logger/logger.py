"""
Core implementation of the asynchronous, fault-tolerant logger.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from joshua_network.client import Client

# Internal logger for the library itself, not for application logs
internal_logger = logging.getLogger(__name__)


class Logger:
    """
    Manages a persistent WebSocket connection to send logs to Godot.

    Uses joshua_network.Client for robust connection management and
    JSON-RPC communication. Designed to fail silently to ensure logging
    issues never crash the application.

    Args:
        url: The WebSocket URL for the Godot logging service. Defaults to
             the `JOSHUA_LOGGER_URL` env var or 'ws://godot-mcp:9060'.
        timeout: The timeout in seconds for sending a log message. Defaults
                 to `JOSHUA_LOGGER_TIMEOUT` env var or 2.0.
    """

    def __init__(self, url: Optional[str] = None, timeout: Optional[float] = None, backup_dir: Optional[str] = None):
        self.url = url or os.environ.get("JOSHUA_LOGGER_URL", "ws://godot-mcp:9060")
        self.timeout = timeout or float(os.environ.get("JOSHUA_LOGGER_TIMEOUT", 2.0))
        self.backup_dir = Path(backup_dir or os.environ.get("JOSHUA_LOGGER_BACKUP_DIR", "/tmp/joshua_logs"))
        self._client = Client(self.url, timeout=int(self.timeout))

        # Ensure backup directory exists
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            internal_logger.warning(f"Failed to create backup directory {self.backup_dir}: {e}")

        internal_logger.info(f"Logger initialized: url={self.url}, timeout={self.timeout}, backup_dir={self.backup_dir}")

    def _write_backup_log(self, level: str, message: str, component: str, data: Optional[Dict[str, Any]], trace_id: Optional[str]) -> None:
        """Write log to local filesystem as backup when Godot is unreachable."""
        try:
            # Create component-specific subdirectory
            component_dir = self.backup_dir / component
            component_dir.mkdir(parents=True, exist_ok=True)

            # Use date-based log file (one per day per component)
            today = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = component_dir / f"{today}.jsonl"

            # Create structured log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": level.upper(),
                "component": component,
                "message": message,
                "data": data,
                "trace_id": trace_id
            }

            # Append to log file (JSONL format - one JSON object per line)
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            # Ultimate fallback - log to stderr only
            internal_logger.error(f"Failed to write backup log: {e}", exc_info=True)

    async def log(
        self,
        level: str,
        message: str,
        component: str,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Sends a structured log message to the Godot service.

        If Godot is unreachable, writes to local backup logs at:
        {backup_dir}/{component}/{YYYY-MM-DD}.jsonl

        This method is fire-and-forget. It will not raise exceptions on
        failure.

        Args:
            level: The log level (e.g., 'INFO', 'ERROR').
            message: The primary log message string.
            component: The name of the component generating the log.
            data: Optional dictionary of structured data.
            trace_id: Optional ID for request tracing.
        """
        try:
            # Try to send to Godot first
            await self._client.call_tool(
                tool_name="godot_logger_log",
                arguments={
                    "level": level.upper(),
                    "message": message,
                    "component": component,
                    "data": data,
                    "trace_id": trace_id,
                }
            )
        except Exception as e:
            # Godot failed - write to local backup
            internal_logger.error(f"Failed to send log to Godot, writing to backup: {e}")
            self._write_backup_log(level, message, component, data, trace_id)

    async def close(self) -> None:
        """Gracefully closes the logger connection."""
        await self._client.disconnect()
        internal_logger.info("Logger connection closed.")
