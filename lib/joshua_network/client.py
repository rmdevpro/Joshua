"""
joshua_network: Standard Client Implementation

This module provides a standardized WebSocket client for JSON-RPC 2.0
communication. It features automatic connection and robust request/response
handling.
"""
import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Optional

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed
from websockets.protocol import State

logger = logging.getLogger(__name__)


class Client:
    """
    An asynchronous WebSocket client for JSON-RPC 2.0 communication.

    Manages connection state, request/response matching, and timeouts.
    The connection is established on the first request.

    Args:
        url: The WebSocket URL of the server (e.g., "ws://localhost:9000").
        timeout: The default request timeout in seconds.
    """

    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.timeout = timeout
        self.websocket: Optional[WebSocketClientProtocol] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._listen_task: Optional[asyncio.Task] = None
        self._connection_lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Returns True if the WebSocket is connected and open."""
        return self.websocket is not None and self.websocket.state == State.OPEN

    async def connect(self) -> None:
        """Establishes a WebSocket connection if not already connected."""
        async with self._connection_lock:
            if self.is_connected:
                return

            logger.info(f"Connecting to server at {self.url}...")
            try:
                # 200MB max frame size to match server
                self.websocket = await websockets.connect(
                    self.url, max_size=200 * 1024 * 1024
                )
                self._listen_task = asyncio.create_task(self._listen())
                logger.info(f"Successfully connected to {self.url}")
            except Exception as e:
                logger.error(f"Failed to connect to {self.url}: {e}")
                self.websocket = None
                raise

    async def disconnect(self) -> None:
        """Closes the WebSocket connection and cleans up background tasks."""
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
            logger.info("Disconnected from server.")

        # CRITICAL BUG FIX: Fail all pending requests to prevent hangs
        for future in self._pending_requests.values():
            if not future.done():
                future.set_exception(ConnectionClosed(None, None))
        self._pending_requests.clear()

    async def _listen(self) -> None:
        """Listens for incoming messages and resolves pending request futures."""
        try:
            async for message in self.websocket:
                try:
                    response = json.loads(message)
                    req_id = response.get("id")
                    if req_id in self._pending_requests:
                        future = self._pending_requests.pop(req_id)
                        if "error" in response:
                            future.set_exception(Exception(response["error"]))
                        else:
                            future.set_result(response.get("result"))
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {message}")
        except ConnectionClosed:
            logger.warning("Connection was closed.")
        except asyncio.CancelledError:
            logger.info("Listener task cancelled.")
        except Exception as e:
            logger.error(f"Error in listener task: {e}")
        finally:
            # Clean up any pending requests on disconnect
            for future in self._pending_requests.values():
                if not future.done():
                    future.set_exception(ConnectionClosed(None, None))
            self._pending_requests.clear()

    async def _send_json_rpc_request(self, method: str, params: Optional[Dict[str, Any]]) -> Any:
        """Connects if necessary and sends a JSON-RPC request."""
        if not self.is_connected:
            await self.connect()

        request_id = str(uuid.uuid4())
        request = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": request_id}
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            await self.websocket.send(json.dumps(request))
            return await asyncio.wait_for(future, timeout=self.timeout)
        except (asyncio.TimeoutError, ConnectionClosed) as e:
            self._pending_requests.pop(request_id, None)
            logger.error(f"Request '{method}' failed: {type(e).__name__}")
            raise
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            logger.error(f"An unexpected error occurred during request '{method}': {e}")
            raise

    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Calls a remote tool via the 'tools/call' method.

        Args:
            tool_name: The name of the tool to execute.
            arguments: A dictionary of arguments for the tool.

        Returns:
            The result returned by the tool.
        """
        return await self._send_json_rpc_request(
            "tools/call", {"name": tool_name, "arguments": arguments or {}}
        )

    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Sends a generic JSON-RPC request.

        Args:
            method: The JSON-RPC method name.
            params: A dictionary of parameters for the method.

        Returns:
            The result from the JSON-RPC response.
        """
        return await self._send_json_rpc_request(method, params)
