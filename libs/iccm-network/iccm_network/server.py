"""
iccm-network: Standard MCP Server Implementation

This module provides a standardized WebSocket MCP server that eliminates
connection issues caused by inconsistent binding and configuration.

Key Design Principles:
- ALWAYS bind to 0.0.0.0 for container-to-container communication
- Implement JSON-RPC 2.0 protocol correctly
- Standardized error handling with MCPToolError
- Zero configuration required - just works

Based on synthesis of:
- Dewey (most reliable reference implementation)
- Fiedler (HTTP proxy integration patterns)
- Gemini-2.5-pro analysis (root cause identification)
"""

import asyncio
import json
import logging
from http import HTTPStatus
from typing import Dict, Any, Callable, Awaitable, Optional
import traceback

import websockets
from websockets.server import WebSocketServerProtocol


class MCPToolError(Exception):
    """
    Custom exception for tool-specific errors.

    Provides standardized error responses following JSON-RPC 2.0 spec.

    Args:
        message: Human-readable error description
        code: JSON-RPC error code (default -32000 for server error)
        data: Optional additional error data
    """
    def __init__(self, message: str, code: int = -32000, data: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data


class MCPServer:
    """
    Standardized MCP WebSocket server.

    Handles all WebSocket connection, JSON-RPC protocol, and tool routing.
    Components only need to provide tool definitions and handlers.

    Example:
        ```python
        server = MCPServer(
            name="horace",
            version="1.0.0",
            port=8070,
            tool_definitions={
                "horace_register_file": {
                    "description": "Register a file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            tool_handlers={
                "horace_register_file": register_file_handler
            }
        )
        await server.start()
        ```

    Args:
        name: Service name (e.g., "horace", "dewey")
        version: Service version (e.g., "1.0.0")
        port: Port to listen on
        tool_definitions: Dict mapping tool names to MCP tool schemas
        tool_handlers: Dict mapping tool names to async handler functions
        logger: Optional custom logger (creates default if None)
    """

    def __init__(
        self,
        name: str,
        version: str,
        port: int,
        tool_definitions: Dict[str, Any],
        tool_handlers: Dict[str, Callable[..., Awaitable[Any]]],
        logger: Optional[logging.Logger] = None
    ):
        self.name = name
        self.version = version
        self.port = port
        self.tool_definitions = tool_definitions
        self.tool_handlers = tool_handlers

        # CRITICAL: Always bind to 0.0.0.0 for container networking
        # This is NOT configurable - it must be 0.0.0.0 for relay to connect
        self.host = "0.0.0.0"

        # Setup logging
        self.logger = logger or self._create_default_logger()

        # Server instance (set during start())
        self._server = None

    def _create_default_logger(self) -> logging.Logger:
        """Create default logger with standard format."""
        logger = logging.getLogger(f"iccm_network.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP 'initialize' method.

        Returns server capabilities and metadata.
        """
        self.logger.info(f"Initialize request from client: {params.get('clientInfo', {})}")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }

    async def _handle_tools_list(self) -> Dict[str, Any]:
        """
        Handle MCP 'tools/list' method.

        Returns list of available tools with their schemas.
        """
        tools = [
            {
                "name": name,
                **definition
            }
            for name, definition in self.tool_definitions.items()
        ]

        self.logger.info(f"Tools list requested: {len(tools)} tools available")
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP 'tools/call' method.

        Routes to appropriate tool handler and handles errors.
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tool_handlers:
            raise MCPToolError(
                f"Tool '{tool_name}' not found",
                code=-32601  # Method not found
            )

        self.logger.info(f"Calling tool: {tool_name}")

        try:
            handler = self.tool_handlers[tool_name]
            result = await handler(**arguments)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }

        except MCPToolError:
            # Re-raise MCPToolError as-is
            raise

        except Exception as e:
            # Wrap unexpected errors
            self.logger.error(f"Tool {tool_name} failed: {e}\n{traceback.format_exc()}")
            raise MCPToolError(
                f"Tool execution failed: {str(e)}",
                code=-32603,  # Internal error
                data={"traceback": traceback.format_exc()}
            )

    async def _handle_message(self, message_str: str) -> Optional[str]:
        """
        Handle incoming JSON-RPC message.

        Parses, routes to handler, and formats response.
        Returns None for notifications (per JSON-RPC 2.0 spec).
        """
        try:
            message = json.loads(message_str)
        except json.JSONDecodeError as e:
            # Parse error always gets a response (id is null)
            return json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,  # Parse error
                    "message": f"Invalid JSON: {str(e)}"
                },
                "id": None
            })

        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        # Check if this is a notification (no id field)
        is_notification = ("id" not in message)

        try:
            # Route to appropriate handler
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            else:
                raise MCPToolError(
                    f"Method '{method}' not supported",
                    code=-32601  # Method not found
                )

            # JSON-RPC 2.0: Do NOT respond to notifications
            if is_notification:
                self.logger.debug(f"Notification received: {method} (no response sent)")
                return None

            # Success response
            return json.dumps({
                "jsonrpc": "2.0",
                "result": result,
                "id": msg_id
            })

        except MCPToolError as e:
            # JSON-RPC 2.0: Do NOT respond to notification errors
            if is_notification:
                self.logger.error(f"Notification error in {method}: {e.message}")
                return None

            # Standardized error response
            return json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "data": e.data
                },
                "id": msg_id
            })

        except Exception as e:
            # Unexpected error
            self.logger.error(f"Unexpected error handling {method}: {e}\n{traceback.format_exc()}")

            # JSON-RPC 2.0: Do NOT respond to notification errors
            if is_notification:
                return None

            return json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,  # Internal error
                    "message": f"Internal server error: {str(e)}",
                    "data": {"traceback": traceback.format_exc()}
                },
                "id": msg_id
            })

    async def _health_check_handler(
        self, path: str, request_headers: Dict[str, str]
    ) -> Optional[tuple]:
        """
        Simple HTTP health check handler.

        Returns OK for /healthz requests, None for WebSocket upgrades.
        """
        if path == "/healthz":
            self.logger.debug("Health check requested")
            return (HTTPStatus.OK, [("Content-Type", "text/plain")], b"OK\n")
        return None  # Let websockets handle it as a WebSocket upgrade

    async def _connection_handler(self, websocket: WebSocketServerProtocol):
        """
        Handle WebSocket connection lifecycle.

        Processes messages until client disconnects.
        """
        client_id = id(websocket)
        self.logger.info(f"Client {client_id} connected")

        try:
            async for message in websocket:
                response = await self._handle_message(message)

                # JSON-RPC 2.0: Only send response if not a notification
                if response is not None:
                    await websocket.send(response)

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            self.logger.error(f"Connection error for client {client_id}: {e}")
        finally:
            self.logger.info(f"Client {client_id} session ended")

    async def start(self):
        """
        Start the MCP server and run forever.

        Binds to 0.0.0.0:{port} and handles connections.
        Includes WebSocket keep-alives and HTTP health check endpoint.
        """
        self.logger.info(f"Starting {self.name} MCP server v{self.version}")
        self.logger.info(f"Binding to {self.host}:{self.port}")
        self.logger.info(f"Tools available: {list(self.tool_definitions.keys())}")

        self._server = await websockets.serve(
            self._connection_handler,
            self.host,
            self.port,
            process_request=self._health_check_handler,  # HTTP health check
            ping_interval=20,  # Send ping every 20 seconds
            ping_timeout=20,   # Close connection if pong not received in 20s
            max_size=209715200  # 200MB max frame size (private trusted network)
        )

        self.logger.info(f"✓ {self.name} MCP server listening on ws://{self.host}:{self.port}")
        self.logger.info(f"✓ Health check available at http://{self.host}:{self.port}/healthz")

        # Run forever
        await asyncio.Future()

    async def stop(self):
        """
        Gracefully stop the server.

        Useful for testing and controlled shutdown.
        """
        if self._server:
            self.logger.info(f"Stopping {self.name} MCP server")
            self._server.close()
            await self._server.wait_closed()
            self.logger.info(f"✓ {self.name} MCP server stopped")
