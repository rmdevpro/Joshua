#!/mnt/projects/ICCM/fiedler/.venv/bin/python3
"""
Fiedler stdio-to-WebSocket Adapter

Bridges Claude Code's stdio MCP transport to Fiedler's WebSocket server.

Usage in Claude Code MCP config:
{
  "fiedler": {
    "type": "stdio",
    "command": "python3",
    "args": ["/mnt/projects/ICCM/fiedler/stdio_adapter.py"]
  }
}

Architecture:
  Claude Code (stdio) → This Adapter → ws://localhost:9010 → Fiedler WebSocket Server
"""

import sys
import asyncio
import websockets
import json


FIEDLER_WS_URL = "ws://localhost:9010"


async def stdio_to_websocket():
    """Main adapter loop: bidirectional stdio ↔ WebSocket relay."""

    # Connect to Fiedler WebSocket server
    try:
        async with websockets.connect(FIEDLER_WS_URL) as websocket:

            # Task 1: Read from stdin, send to WebSocket
            async def stdin_to_ws():
                loop = asyncio.get_event_loop()
                while True:
                    # Read line from stdin (blocking, run in executor)
                    line = await loop.run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break

                    # Send to WebSocket
                    await websocket.send(line.strip())

            # Task 2: Read from WebSocket, write to stdout
            async def ws_to_stdout():
                while True:
                    message = await websocket.recv()
                    # Write to stdout (JSON-RPC messages are single lines)
                    print(message, flush=True)

            # Run both tasks concurrently
            await asyncio.gather(
                stdin_to_ws(),
                ws_to_stdout()
            )

    except websockets.exceptions.WebSocketException as e:
        print(json.dumps({
            "jsonrpc": "2.0",
            "error": {
                "code": -32000,
                "message": f"Failed to connect to Fiedler WebSocket: {str(e)}"
            }
        }), file=sys.stderr, flush=True)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal adapter error: {str(e)}"
            }
        }), file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(stdio_to_websocket())
    except KeyboardInterrupt:
        sys.exit(0)
