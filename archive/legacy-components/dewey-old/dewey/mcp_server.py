# dewey/mcp_server.py
"""
WebSocket MCP server for Dewey.
"""
import asyncio
import json
import logging
from typing import Any, Dict

import websockets
from websockets.server import WebSocketServerProtocol

from dewey import config
from dewey.database import db_pool
from dewey import tools

logger = logging.getLogger(__name__)

class DeweyMCPServer:
    """WebSocket MCP server for Dewey."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server = None

        # MCP tool definitions
        self.tools = {
            "dewey_begin_conversation": {
                "description": "Start a new conversation and return its ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Optional session ID to group conversations"},
                        "metadata": {"type": "object", "description": "Optional metadata as key-value pairs"}
                    }
                }
            },
            "dewey_store_message": {
                "description": "Store a single message in a conversation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "description": "UUID of the conversation"},
                        "role": {"type": "string", "description": "Role: user, assistant, or system"},
                        "content": {"type": "string", "description": "Message content"},
                        "turn_number": {"type": "integer", "description": "Optional turn number"},
                        "metadata": {"type": "object", "description": "Optional metadata"}
                    },
                    "required": ["conversation_id", "role", "content"]
                }
            },
            "dewey_store_messages_bulk": {
                "description": "Store multiple messages at once (up to 1000). Supports file references for large payloads.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "description": "Array of message objects with role and content (inline)",
                            "items": {"type": "object"}
                        },
                        "messages_file": {
                            "type": "string",
                            "description": "Path to JSON file containing message array (file reference - industry standard for large payloads)"
                        },
                        "conversation_id": {"type": "string", "description": "Optional existing conversation ID"},
                        "session_id": {"type": "string", "description": "Optional session ID for new conversation"},
                        "metadata": {"type": "object", "description": "Optional metadata for new conversation"}
                    }
                }
            },
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
            "dewey_delete_conversation": {
                "description": "Delete a conversation and all its messages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "description": "UUID of the conversation"},
                        "force": {"type": "boolean", "description": "Force delete without confirmation"}
                    },
                    "required": ["conversation_id"]
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
            "dewey_set_startup_context": {
                "description": "Create or update a startup context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Context name"},
                        "content": {"type": "string", "description": "Context content"},
                        "set_active": {"type": "boolean", "description": "Make this the active context"}
                    },
                    "required": ["name", "content"]
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
            "dewey_delete_startup_context": {
                "description": "Delete a startup context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Context name"},
                        "force": {"type": "boolean", "description": "Force delete without confirmation"}
                    },
                    "required": ["name"]
                }
            }
        }

    async def handle_request(self, websocket: WebSocketServerProtocol, path: str):
        """Handle incoming WebSocket connection."""
        logger.info(f"Client connected from {websocket.remote_address}")

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

        self.server = await websockets.serve(
            self.handle_request,
            self.host,
            self.port
        )

        logger.info("Dewey MCP Server is running")

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
