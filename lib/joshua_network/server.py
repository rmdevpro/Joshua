"""
joshua_network: Standard Server Implementation

This module provides a standardized WebSocket server that binds to 0.0.0.0
to ensure reliable container-to-container communication. It handles the
JSON-RPC 2.0 protocol, connection keep-alives, and a health check endpoint.
"""
import asyncio
import json
import logging
import traceback
from http import HTTPStatus
from typing import Any, Awaitable, Callable, Dict, Optional

import websockets
from websockets.datastructures import Headers
from websockets.server import WebSocketServerProtocol

from .errors import ToolError


class Server:
    """
    A standardized WebSocket server for JSON-RPC 2.0 communication.

    This server handles all WebSocket connection logic, JSON-RPC protocol
    details, and tool routing. Users only need to provide service metadata,
    tool definitions, and their corresponding async handlers.

    The server always binds to '0.0.0.0' to be accessible from other
    containers and exposes a '/healthz' endpoint for health checks.

    Args:
        name: The name of the service (e.g., "horace").
        version: The semantic version of the service (e.g., "1.0.0").
        port: The network port to listen on.
        tool_definitions: A dictionary mapping tool names to their schemas.
        tool_handlers: A dictionary mapping tool names to their async handlers.
        logger: An optional custom logger instance. If None, a default
                logger is created.
    """

    def __init__(
        self,
        name: str = "joshua_network_server",
        version: str = "1.0.0",
        port: int = 9000,
        tool_definitions: Optional[Dict[str, Any]] = None,
        tool_handlers: Optional[Dict[str, Callable[..., Awaitable[Any]]]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.name = name
        self.version = version
        self.port = port
        self.tool_definitions = tool_definitions or {}
        self.tool_handlers = tool_handlers or {}
        self.host = "0.0.0.0"  # CRITICAL: Always bind to 0.0.0.0
        self.logger = logger or self._create_default_logger()
        self._server: Optional[websockets.WebSocketServer] = None
        self._tool_handlers = tool_handlers or {}

    def _create_default_logger(self) -> logging.Logger:
        """Creates and configures a default logger for the server."""
        logger = logging.getLogger(f"joshua_network.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"%(asctime)s - {self.name} - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def is_serving(self) -> bool:
        """Returns True if the server is currently serving."""
        return self._server is not None

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handles the 'initialize' method, returning server capabilities."""
        self.logger.info(f"Initialize request from client: {params.get('clientInfo', {})}")
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": self.name, "version": self.version},
        }

    async def _handle_tools_list(self) -> Dict[str, Any]:
        """Handles the 'tools/list' method, returning available tools."""
        tools = [{"name": name, **definition} for name, definition in self.tool_definitions.items()]
        self.logger.info(f"Tools list requested: {len(tools)} tools available.")
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handles 'tools/call', routing to the appropriate tool handler."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tool_handlers:
            raise ToolError(f"Tool '{tool_name}' not found", code=-32601)

        self.logger.info(f"Calling tool: {tool_name}")
        try:
            handler = self.tool_handlers[tool_name]
            result = await handler(**arguments)
            return result
        except ToolError:
            raise  # Re-raise user-defined errors
        except Exception as e:
            self.logger.error(f"Tool {tool_name} failed: {e}\n{traceback.format_exc()}")
            raise ToolError(f"Tool execution failed: {str(e)}", code=-32000)

    async def _process_message(self, message_str: str) -> Optional[str]:
        """Parses a JSON-RPC message, routes it, and formats the response."""
        try:
            message = json.loads(message_str)
            msg_id = message.get("id")
            method = message.get("method")
            params = message.get("params", {})
        except json.JSONDecodeError as e:
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Invalid JSON: {str(e)}"}, "id": None})

        is_notification = "id" not in message

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            else:
                raise ToolError(f"Method '{method}' not supported", code=-32601)

            if is_notification:
                return None
            return json.dumps({"jsonrpc": "2.0", "result": result, "id": msg_id})

        except ToolError as e:
            if is_notification:
                self.logger.error(f"Error in notification '{method}': {e.message}")
                return None
            return json.dumps({"jsonrpc": "2.0", "error": {"code": e.code, "message": e.message}, "id": msg_id})
        except Exception as e:
            self.logger.error(f"Unexpected error handling '{method}': {e}\n{traceback.format_exc()}")
            if is_notification:
                return None
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal server error"}, "id": msg_id})

    async def _health_check_handler(self, path: str, request_headers: Headers) -> Optional[tuple]:
        """Responds to HTTP health checks at '/healthz'."""
        if path == "/healthz":
            self.logger.debug("Health check request received")
            return (HTTPStatus.OK, [("Content-Type", "text/plain")], b"OK\n")
        return None  # Let `websockets` handle the WebSocket upgrade

    async def _connection_handler(self, websocket: WebSocketServerProtocol) -> None:
        """Manages the lifecycle of a single client WebSocket connection."""
        remote_addr = websocket.remote_address
        self.logger.info(f"Client connected: {remote_addr}")
        try:
            async for message in websocket:
                response = await self._process_message(str(message))
                if response is not None:
                    await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {remote_addr}")
        except Exception as e:
            self.logger.error(f"Connection error with {remote_addr}: {e}")
        finally:
            self.logger.info(f"Client session ended: {remote_addr}")

    async def start(self) -> None:
        """Starts the server and runs it indefinitely."""
        self.logger.info(f"Starting {self.name} server v{self.version} on {self.host}:{self.port}")
        self.logger.info(f"Tools available: {list(self.tool_definitions.keys())}")

        self._server = await websockets.serve(
            self._connection_handler,
            self.host,
            self.port,
            process_request=self._health_check_handler,
            ping_interval=20,
            ping_timeout=20,
            max_size=200 * 1024 * 1024,  # 200MB
        )
        self.logger.info(f"✓ Server listening at ws://{self.host}:{self.port}")
        self.logger.info(f"✓ Health check available at http://{self.host}:{self.port}/healthz")
        await asyncio.Future()  # Run forever

    async def stop(self) -> None:
        """Gracefully stops the server."""
        if self._server:
            self.logger.info(f"Stopping {self.name} server...")
            self._server.close()
            await self._server.wait_closed()
            self.logger.info(f"✓ Server stopped.")
