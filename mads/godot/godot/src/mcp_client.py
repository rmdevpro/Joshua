"""
MCP Client - WebSocket-based MCP client using JSON-RPC protocol
Based on Gemini-2.5-Pro recommendation (correlation_id: b5afd3b0)
"""
import asyncio
import json
import uuid
from typing import Any, Dict, Optional

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.protocol import State
from joshua_logger import Logger

logger = Logger()


class MCPClient:
    """A WebSocket-based MCP client using the JSON-RPC protocol."""

    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.timeout = timeout
        self.websocket: Optional[WebSocketClientProtocol] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._listen_task: Optional[asyncio.Task] = None

    @property
    def is_connected(self) -> bool:
        """Check if the WebSocket is connected and open."""
        return self.websocket is not None and self.websocket.state == State.OPEN

    async def connect(self):
        """Establishes a WebSocket connection and starts the listener task."""
        if self.is_connected:
            await logger.log("WARN", "Already connected.", "godot-mcp-client")
            return

        try:
            await logger.log("INFO", f"Connecting to MCP server at {self.url}...", "godot-mcp-client")
            # Set max_size=200MB for large conversations (trusted private network)
            # Default 1MB limit is DoS protection for public internet, not needed here
            self.websocket = await websockets.connect(self.url, max_size=209715200)
            self._listen_task = asyncio.create_task(self._listen())
            await logger.log("INFO", f"Successfully connected to {self.url}", "godot-mcp-client")
        except Exception as e:
            await logger.log("ERROR", f"Failed to connect to {self.url}: {e}", "godot-mcp-client")
            raise

    async def disconnect(self):
        """Closes the WebSocket connection and cancels the listener task."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            await logger.log("INFO", "Disconnected from MCP server.", "godot-mcp-client")

    async def _listen(self):
        """Background task that listens for responses from the server."""
        try:
            async for message in self.websocket:
                try:
                    response = json.loads(message)
                    request_id = response.get("id")

                    if request_id and request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        if "error" in response:
                            future.set_exception(Exception(response["error"].get("message", "Unknown error")))
                        else:
                            future.set_result(response.get("result"))
                    else:
                        await logger.log("WARN", f"Received response for unknown request ID: {request_id}", "godot-mcp-client")
                except json.JSONDecodeError as e:
                    await logger.log("ERROR", f"Failed to decode message: {e}", "godot-mcp-client")
        except asyncio.CancelledError:
            await logger.log("INFO", "Listener task cancelled.", "godot-mcp-client")
        except Exception as e:
            await logger.log("ERROR", f"Error in listener task: {e}", "godot-mcp-client")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """
        Calls a tool on the MCP server via JSON-RPC.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            Exception if call fails or times out
        """
        if not self.is_connected:
            await self.connect()

        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            },
            "id": request_id
        }

        future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            await self.websocket.send(json.dumps(request))
            await logger.log("DEBUG", f"Sent request {request_id} for tool {tool_name}", "godot-mcp-client")

            result = await asyncio.wait_for(future, timeout=self.timeout)
            await logger.log("DEBUG", f"Received response for request {request_id}", "godot-mcp-client")
            return result

        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            await logger.log("ERROR", f"Request {request_id} timed out after {self.timeout}s", "godot-mcp-client")
            raise Exception(f"Tool call '{tool_name}' timed out")
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            await logger.log("ERROR", f"Error calling tool {tool_name}: {e}", "godot-mcp-client")
            raise
