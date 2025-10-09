"""
Core implementation of the asynchronous, fault-tolerant logger.
"""
import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed
from websockets.protocol import State

# Internal logger for the library itself, not for application logs
internal_logger = logging.getLogger(__name__)


class Logger:
    """
    Manages a persistent WebSocket connection to send logs to Godot.

    This class handles connection, automatic reconnection with exponential
    backoff, and sending structured log messages. It is designed to fail
    silently, ensuring that logging issues never crash the application.

    Args:
        url: The WebSocket URL for the Godot logging service. Defaults to
             the `JOSHUA_LOGGER_URL` env var or 'ws://godot-mcp:9060'.
        timeout: The timeout in seconds for sending a log message. Defaults
                 to `JOSHUA_LOGGER_TIMEOUT` env var or 2.0.
    """

    def __init__(self, url: Optional[str] = None, timeout: Optional[float] = None):
        self.url = url or os.environ.get("JOSHUA_LOGGER_URL", "ws://godot-mcp:9060")
        self.timeout = timeout or float(os.environ.get("JOSHUA_LOGGER_TIMEOUT", 2.0))
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connection_lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None
        self._send_lock = asyncio.Lock()  # BUG FIX: Serialize send operations
        internal_logger.info(f"Logger initialized: url={self.url}, timeout={self.timeout}")

    async def _connect(self) -> None:
        """Establishes a connection, guarded by a lock."""
        async with self._connection_lock:
            if self._ws and self._ws.state == State.OPEN:
                return
            try:
                internal_logger.debug(f"Connecting to logger at {self.url}")
                self._ws = await websockets.connect(self.url, open_timeout=self.timeout)
                internal_logger.info(f"Logger connected to {self.url}")
            except Exception as e:
                internal_logger.warning(f"Logger connection failed: {e}")
                self._ws = None
                # Schedule a reconnect if connection fails
                if self._reconnect_task is None or self._reconnect_task.done():
                    self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """Continuously attempts to reconnect with exponential backoff."""
        delay = 1.0
        while True:
            if self._ws and self._ws.state == State.OPEN:
                internal_logger.debug("Reconnect loop exiting: connection established.")
                break
            internal_logger.info(f"Logger disconnected. Reconnecting in {delay:.1f}s...")
            await asyncio.sleep(delay)
            try:
                await self._connect()
            except Exception:
                pass  # _connect already logs the error
            delay = min(delay * 2, 60.0)  # Cap delay at 60 seconds

    async def _ensure_connected(self) -> None:
        """Ensure connection is established (for testing)."""
        await self._connect()

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
            if not self._ws or self._ws.state != State.OPEN:
                await self._connect()
                # If connection still fails, exit silently
                if not self._ws or self._ws.state != State.OPEN:
                    return

            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "logger_log",
                    "arguments": {
                        "level": level.upper(),
                        "message": message,
                        "component": component,
                        "data": data,
                        "trace_id": trace_id,
                    },
                },
                "id": str(uuid.uuid4()),
            }
            # BUG FIX: Use a lock to prevent concurrent writes to the websocket
            async with self._send_lock:
                await asyncio.wait_for(
                    self._ws.send(json.dumps(request)), timeout=self.timeout
                )
        except (ConnectionClosed, asyncio.TimeoutError) as e:
            internal_logger.warning(f"Could not send log, connection issue: {e}")
            self._ws = None  # Mark for reconnection
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._reconnect_loop())
        except Exception as e:
            # Catch all other exceptions to ensure silent failure
            internal_logger.error(f"Unexpected error in logger: {e}", exc_info=True)
            self._ws = None # Assume connection is bad
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def close(self) -> None:
        """Gracefully closes the logger connection."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
        if self._ws:
            await self._ws.close()
            self._ws = None
        internal_logger.info("Logger connection closed.")
