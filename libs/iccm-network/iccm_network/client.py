"""
MCP Client - WebSocket-based MCP client using JSON-RPC protocol

Provides standardized MCP client with 200MB frame size for private trusted network.
Based on Godot's mcp_client.py pattern, adapted for library reuse.
"""
import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Optional

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.protocol import State

logger = logging.getLogger(__name__)


class MCPClient:
    """A WebSocket-based MCP client using the JSON-RPC protocol."""

    def __init__(self, url: str, timeout: int = 10):
        """
        Initialize MCP client.

        Args:
            url: WebSocket URL to connect to (e.g., ws://localhost:9001)
            timeout: Request timeout in seconds (default 10)
        """
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
            logger.warning("Already connected.")
            return

        try:
            logger.info(f"Connecting to MCP server at {self.url}...")
            # Set max_size=200MB for large conversations (trusted private network)
            # Default 1MB limit is DoS protection for public internet, not needed here
            self.websocket = await websockets.connect(self.url, max_size=209715200)
            self._listen_task = asyncio.create_task(self._listen())
            logger.info(f"Successfully connected to {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.url}: {e}")
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
            logger.info("Disconnected from MCP server.")

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
                        logger.warning(f"Received response for unknown request ID: {request_id}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
        except asyncio.CancelledError:
            logger.info("Listener task cancelled.")
        except Exception as e:
            logger.error(f"Error in listener task: {e}")

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
            logger.debug(f"Sent request {request_id} for tool {tool_name}")

            result = await asyncio.wait_for(future, timeout=self.timeout)
            logger.debug(f"Received response for request {request_id}")
            return result

        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            logger.error(f"Request {request_id} timed out after {self.timeout}s")
            raise Exception(f"Tool call '{tool_name}' timed out")
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise

    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """
        Send a raw JSON-RPC request to the server.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            Response result

        Raises:
            Exception if request fails or times out
        """
        if not self.is_connected:
            await self.connect()

        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id
        }

        future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            await self.websocket.send(json.dumps(request))
            logger.debug(f"Sent request {request_id} for method {method}")

            result = await asyncio.wait_for(future, timeout=self.timeout)
            logger.debug(f"Received response for request {request_id}")
            return result

        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            logger.error(f"Request {request_id} timed out after {self.timeout}s")
            raise Exception(f"Request '{method}' timed out")
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            logger.error(f"Error sending request {method}: {e}")
            raise
