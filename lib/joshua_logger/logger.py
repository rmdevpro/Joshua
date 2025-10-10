"""
Core implementation of the asynchronous, fault-tolerant logger.
"""
import asyncio
import logging
import os
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

    def __init__(self, url: Optional[str] = None, timeout: Optional[float] = None):
        self.url = url or os.environ.get("JOSHUA_LOGGER_URL", "ws://godot-mcp:9060")
        self.timeout = timeout or float(os.environ.get("JOSHUA_LOGGER_TIMEOUT", 2.0))
        self._client = Client(self.url, timeout=int(self.timeout))
        internal_logger.info(f"Logger initialized: url={self.url}, timeout={self.timeout}")

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
            # Use call_tool which sends tools/call JSON-RPC request
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
            # Fail silently but log internally for debugging
            internal_logger.error(f"Failed to send log message: {e}", exc_info=True)

    async def close(self) -> None:
        """Gracefully closes the logger connection."""
        await self._client.disconnect()
        internal_logger.info("Logger connection closed.")
