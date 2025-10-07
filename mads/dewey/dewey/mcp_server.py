# dewey/mcp_server.py
"""
WebSocket MCP server for Dewey.
"""
import asyncio
import json
import logging
import os
from typing import Any, Dict

import websockets
from websockets.server import WebSocketServerProtocol

from dewey import config
from dewey.database import db_pool
from dewey import tools
from dewey.godot import log_to_godot

logger = logging.getLogger(__name__)

# Godot logging configuration
GODOT_URL = os.getenv('GODOT_URL', 'ws://godot-mcp:9060')
LOGGING_ENABLED = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'

class DeweyMCPServer:
    """WebSocket MCP server for Dewey."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server = None

        # MCP tool definitions
        self.tools = {
            "dewey_get_conversation": {
                "description": "Retrieve all messages from a conversation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "description": "UUID of the conversation"}
                    },
                    "required": ["conversation_id"]
                }
            },
            "dewey_list_conversations": {
                "description": "List conversations with pagination and filtering",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Optional session ID filter"},
                        "limit": {"type": "integer", "description": "Maximum results (default 20)"},
                        "offset": {"type": "integer", "description": "Number to skip (default 0)"},
                        "sort_by": {"type": "string", "description": "Sort field: created_at or updated_at"}
                    }
                }
            },
            "dewey_search": {
                "description": "Full-text search across all messages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query string"},
                        "session_id": {"type": "string", "description": "Optional session ID filter"},
                        "start_date": {"type": "string", "description": "Optional start date (ISO format)"},
                        "end_date": {"type": "string", "description": "Optional end date (ISO format)"},
                        "limit": {"type": "integer", "description": "Maximum results (default 20)"},
                        "offset": {"type": "integer", "description": "Number to skip (default 0)"}
                    },
                    "required": ["query"]
                }
            },
            "dewey_get_startup_context": {
                "description": "Get the active startup context or a specific one by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Optional context name (defaults to active)"}
                    }
                }
            },
            "dewey_list_startup_contexts": {
                "description": "List all available startup contexts",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_content": {"type": "boolean", "description": "Include full content (default false)"}
                    }
                }
            },
            "dewey_query_logs": {
                "description": "Query logs with various filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "trace_id": {"type": "string", "description": "Filter by trace ID"},
                        "component": {"type": "string", "description": "Filter by component name"},
                        "level": {"type": "string", "description": "Minimum log level (TRACE, DEBUG, INFO, WARN, ERROR)"},
                        "start_time": {"type": "string", "description": "Start time filter (ISO format)"},
                        "end_time": {"type": "string", "description": "End time filter (ISO format)"},
                        "search": {"type": "string", "description": "Full-text search in message"},
                        "limit": {"type": "integer", "description": "Maximum results (1-1000, default 100)"}
                    }
                }
            },
            "dewey_get_log_stats": {
                "description": "Get statistics about the logs table",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }

    async def handle_request(self, websocket: WebSocketServerProtocol, path: str):
        """Handle incoming WebSocket connection."""
        logger.info(f"Client connected from {websocket.remote_address}")

        if LOGGING_ENABLED:
            await log_to_godot('INFO', 'Client connected', data={'client': str(websocket.remote_address)})

        try:
            async for message in websocket:
                try:
                    # Parse JSON-RPC request
                    request = json.loads(message)
                    response = await self.process_request(request)

                    # Send response
                    await websocket.send(json.dumps(response))

                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        },
                        "id": None
                    }
                    await websocket.send(json.dumps(error_response))

                except Exception as e:
                    logger.exception("Error processing request")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        },
                        "id": request.get("id") if isinstance(request, dict) else None
                    }
                    await websocket.send(json.dumps(error_response))

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON-RPC request."""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        logger.debug(f"Processing request: {method}")

        if LOGGING_ENABLED:
            await log_to_godot('TRACE', 'MCP request received', data={'method': method, 'id': request_id})

        # Handle MCP protocol methods
        if method == "initialize":
            logger.info("Client initializing MCP connection")
            return {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "dewey-mcp-server",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }

        elif method == "tools/list":
            logger.info(f"Listing {len(self.tools)} available tools")
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {"name": name, **spec}
                        for name, spec in self.tools.items()
                    ]
                },
                "id": request_id
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            logger.info(f"Calling tool: {tool_name}")

            if LOGGING_ENABLED:
                await log_to_godot('TRACE', 'Tool call started', data={'tool_name': tool_name, 'has_args': bool(arguments)})

            # Get the tool function
            tool_func = getattr(tools, tool_name, None)
            if not tool_func or not callable(tool_func):
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    },
                    "id": request_id
                }

            try:
                # Execute the tool
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**arguments)
                else:
                    result = tool_func(**arguments)

                if LOGGING_ENABLED:
                    await log_to_godot('TRACE', 'Tool call completed', data={'tool_name': tool_name, 'success': True})

                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    },
                    "id": request_id
                }

            except tools.ToolError as e:
                logger.error(f"Tool {tool_name} error: {str(e)}")

                if LOGGING_ENABLED:
                    await log_to_godot('ERROR', 'Tool error', data={'tool_name': tool_name, 'error': str(e), 'code': e.code})

                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": e.code,
                        "message": str(e)
                    },
                    "id": request_id
                }

            except Exception as e:
                logger.exception(f"Error executing tool {tool_name}")

                if LOGGING_ENABLED:
                    await log_to_godot('ERROR', 'Tool execution error', data={'tool_name': tool_name, 'error': str(e), 'type': type(e).__name__})

                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": request_id
                }

        # Legacy direct tool call (for backward compatibility)
        else:
            # Get the tool function
            tool_func = getattr(tools, method, None)
            if not tool_func or not callable(tool_func):
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }

        try:
            # Execute the tool
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**params)
            else:
                result = tool_func(**params)

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }

        except tools.ToolError as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": e.code,
                    "message": str(e)
                },
                "id": request_id
            }

        except Exception as e:
            logger.exception(f"Error executing tool {method}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": request_id
            }

    async def start(self):
        """Start the MCP server."""
        logger.info(f"Starting Dewey MCP Server on {self.host}:{self.port}")

        if LOGGING_ENABLED:
            await log_to_godot('INFO', 'Dewey MCP server starting', data={'host': self.host, 'port': self.port, 'godot_url': GODOT_URL})

        self.server = await websockets.serve(
            self.handle_request,
            self.host,
            self.port
        )

        logger.info("Dewey MCP Server is running")

        if LOGGING_ENABLED:
            await log_to_godot('INFO', 'Dewey MCP server running', data={'status': 'operational'})

    async def stop(self):
        """Stop the MCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Dewey MCP Server stopped")


async def main():
    """Main entry point for Dewey MCP Server."""
    # Initialize async database
    await db_pool.initialize()

    # Create and start server
    server = DeweyMCPServer(config.MCP_HOST, config.MCP_PORT)
    await server.start()

    # Run forever
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await server.stop()
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
