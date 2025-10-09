"""
Asynchronous, WebSocket-based logging client for the Godot MCP.

This module provides a simple, fire-and-forget function to send log messages
to a Godot MCP instance that exposes the `logger_log` tool.
"""
import asyncio
import json
import sys
from typing import Any, Dict, Optional

import websockets
from websockets.exceptions import WebSocketException


async def log_to_godot(
    level: str,
    message: str,
    component: str = "dewey",
    data: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    godot_url: str = "ws://godot-mcp:9060",
    timeout: float = 1.0,
) -> None:
    """
    Send a log entry to Godot via the MCP `logger_log` tool.

    This function is designed to be non-blocking and to fail silently. Logging
    should never cause the primary application to crash or hang.

    Args:
        level: The log level (e.g., "ERROR", "WARN", "INFO", "DEBUG", "TRACE").
        message: The primary log message.
        component: The name of the component or service generating the log.
        data: Optional structured data to include with the log entry.
        trace_id: Optional trace ID for request correlation across services.
        godot_url: The WebSocket URL of the Godot MCP instance.
        timeout: Connection and response timeout in seconds.
    """
    try:
        async with websockets.connect(godot_url, open_timeout=timeout) as ws:
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "logger_log",
                    "arguments": {
                        "level": level,
                        "message": message,
                        "component": component,
                        "data": data,
                        "trace_id": trace_id,
                    },
                },
                "id": 1,
            }

            await ws.send(json.dumps(request))

            # Optionally wait for a response, but time out quickly.
            # The primary goal is to send the log, not process a response.
            try:
                _ = await asyncio.wait_for(ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                # Response timeout is acceptable, as we've sent the log.
                pass

    except (WebSocketException, OSError, asyncio.TimeoutError) as e:
        # Silently fail on expected connection or communication errors.
        # Logging should not disrupt application flow. For debugging,
        # one might temporarily log this error to stderr.
        # print(f"MCP Logger failed: {e}", file=sys.stderr)
        pass
