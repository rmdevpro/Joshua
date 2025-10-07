"""MCP-based logging client for Godot (Python implementation)."""
import json
import asyncio
from typing import Optional, Dict, Any
import websockets

async def log_to_godot(
    level: str,
    message: str,
    component: str = 'dewey',
    data: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    godot_url: str = 'ws://godot-mcp:9060',
    timeout: float = 1.0
) -> None:
    """
    Send log to Godot via MCP logger_log tool.

    Args:
        level: Log level (ERROR, WARN, INFO, DEBUG, TRACE)
        message: Log message
        component: Component name
        data: Optional structured data
        trace_id: Optional trace ID for request correlation
        godot_url: Godot MCP WebSocket URL
        timeout: Connection/response timeout in seconds

    Note:
        Silently fails on error - logging should never break the application
    """
    try:
        async with websockets.connect(godot_url, open_timeout=timeout) as ws:
            request = {
                'jsonrpc': '2.0',
                'method': 'tools/call',
                'params': {
                    'name': 'logger_log',
                    'arguments': {
                        'level': level,
                        'message': message,
                        'component': component,
                        'data': data,
                        'trace_id': trace_id
                    }
                },
                'id': 1
            }

            await ws.send(json.dumps(request))

            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                # Response timeout - continue silently
                pass

    except Exception:
        # Silently fail - logging should never break the application
        pass
