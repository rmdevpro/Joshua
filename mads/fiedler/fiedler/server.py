"""Fiedler MCP Server - Orchestra Conductor Prototype."""
import asyncio
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from .tools import (
    fiedler_list_models,
    fiedler_set_models,
    fiedler_set_output,
    fiedler_get_config,
    fiedler_send,
    fiedler_set_key,
    fiedler_delete_key,
    fiedler_list_keys,
)


# Create server instance
app = Server("fiedler")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Fiedler tools."""
    return [
        Tool(
            name="fiedler_list_models",
            description="List all available LLM models with their properties (name, provider, aliases, max_tokens, capabilities).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="fiedler_set_models",
            description="Configure default models for fiedler_send. Accepts list of model IDs or aliases.",
            inputSchema={
                "type": "object",
                "properties": {
                    "models": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of model IDs or aliases to use as defaults",
                    },
                },
                "required": ["models"],
            },
        ),
        Tool(
            name="fiedler_set_output",
            description="Configure output directory for fiedler_send results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_dir": {
                        "type": "string",
                        "description": "Path to output directory",
                    },
                },
                "required": ["output_dir"],
            },
        ),
        Tool(
            name="fiedler_get_config",
            description="Get current Fiedler configuration (models, output_dir, total_available_models).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="fiedler_send",
            description="Send prompt and optional package files to configured LLMs. Returns results from all models in parallel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "User prompt or question to send to models",
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of file paths to compile into package",
                    },
                    "models": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional override of default models (use model IDs or aliases)",
                    },
                },
                "required": ["prompt"],
            },
        ),
        Tool(
            name="fiedler_set_key",
            description="Store API key securely in system keyring (encrypted). Replaces need for environment variables.",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name: google, openai, together, or xai",
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key to store (will be encrypted by OS keyring)",
                        "format": "password",
                        "writeOnly": True,
                    },
                },
                "required": ["provider", "api_key"],
            },
        ),
        Tool(
            name="fiedler_delete_key",
            description="Delete stored API key from system keyring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name: google, openai, together, or xai",
                    },
                },
                "required": ["provider"],
            },
        ),
        Tool(
            name="fiedler_list_keys",
            description="List providers that have API keys stored in system keyring.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


# Tool dispatch table for sync tools
SYNC_TOOL_DISPATCH = {
    "fiedler_list_models": lambda args: fiedler_list_models(),
    "fiedler_set_models": lambda args: fiedler_set_models(args["models"]),
    "fiedler_set_output": lambda args: fiedler_set_output(args["output_dir"]),
    "fiedler_get_config": lambda args: fiedler_get_config(),
    "fiedler_set_key": lambda args: fiedler_set_key(args["provider"], args["api_key"]),
    "fiedler_delete_key": lambda args: fiedler_delete_key(args["provider"]),
    "fiedler_list_keys": lambda args: fiedler_list_keys(),
}


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls with dictionary-based dispatch and structured errors."""
    import json

    try:
        # Special handling for async fiedler_send
        if name == "fiedler_send":
            result = await asyncio.to_thread(
                fiedler_send,
                prompt=arguments["prompt"],
                files=arguments.get("files"),
                models=arguments.get("models"),
            )
        # Dispatch sync tools
        elif name in SYNC_TOOL_DISPATCH:
            result = SYNC_TOOL_DISPATCH[name](arguments)
        else:
            # Unknown tool
            error_response = {
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": f"Unknown tool: {name}",
                    "tool_name": name
                }
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

        # Format successful result
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except KeyError as e:
        # Missing required argument
        error_response = {
            "error": {
                "code": "MISSING_ARGUMENT",
                "message": f"Missing required argument: {e}",
                "argument": str(e)
            }
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
    except ValueError as e:
        # Invalid input (e.g., unknown model, file too large)
        error_response = {
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e)
            }
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
    except PermissionError as e:
        # File access denied
        error_response = {
            "error": {
                "code": "ACCESS_DENIED",
                "message": str(e)
            }
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
    except FileNotFoundError as e:
        # File not found
        error_response = {
            "error": {
                "code": "FILE_NOT_FOUND",
                "message": str(e)
            }
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
    except RuntimeError as e:
        # Provider/configuration errors
        error_response = {
            "error": {
                "code": "PROVIDER_ERROR",
                "message": str(e)
            }
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
    except Exception as e:
        # Unexpected internal error
        error_response = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {str(e)}",
                "type": type(e).__name__
            }
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]


async def _amain():
    """Async entry point for MCP server - WebSocket mode + HTTP Streaming Proxy."""
    import sys
    import websockets
    import json
    import logging
    from websockets.server import WebSocketServerProtocol
    from .proxy_server import start_proxy_server

    print("=== FIEDLER: _amain() ENTRY POINT ===", flush=True, file=sys.stderr)

    # Force logging to stderr with explicit configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr,
        force=True
    )
    logger = logging.getLogger(__name__)
    print("=== FIEDLER: Logger configured ===", flush=True, file=sys.stderr)
    logger.info("=== FIEDLER STARTUP: _amain() called ===")

    async def handle_client(websocket: WebSocketServerProtocol):
        """Handle WebSocket client connection."""
        logger.info(f"=== FIEDLER: Client connected from {websocket.remote_address} ===")

        try:
            async for message in websocket:
                try:
                    # Parse MCP request
                    request = json.loads(message)
                    method = request.get("method")
                    params = request.get("params", {})
                    request_id = request.get("id")

                    logger.info(f"Received request: {method}")

                    # Handle MCP protocol methods
                    if method == "initialize":
                        response = {
                            "jsonrpc": "2.0",
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {"tools": {}},
                                "serverInfo": {
                                    "name": "fiedler",
                                    "version": "1.0.0"
                                }
                            },
                            "id": request_id
                        }

                    elif method == "tools/list":
                        tools_list = await list_tools()
                        response = {
                            "jsonrpc": "2.0",
                            "result": {
                                "tools": [
                                    {
                                        "name": tool.name,
                                        "description": tool.description,
                                        "inputSchema": tool.inputSchema
                                    }
                                    for tool in tools_list
                                ]
                            },
                            "id": request_id
                        }

                    elif method == "tools/call":
                        tool_name = params.get("name")
                        arguments = params.get("arguments", {})

                        logger.info(f"Calling tool: {tool_name}")

                        # Call the tool via the app's handler
                        result = await call_tool(tool_name, arguments)

                        response = {
                            "jsonrpc": "2.0",
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": item.text
                                    }
                                    for item in result
                                ]
                            },
                            "id": request_id
                        }

                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            },
                            "id": request_id
                        }

                    # Send response
                    await websocket.send(json.dumps(response))

                except json.JSONDecodeError:
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
                    logger.exception(f"Error processing request: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        },
                        "id": request_id if 'request_id' in locals() else None
                    }
                    await websocket.send(json.dumps(error_response))

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")

    # Start HTTP Streaming Proxy on port 8081
    print("=== FIEDLER: Starting HTTP Streaming Proxy ===", flush=True, file=sys.stderr)
    proxy = await start_proxy_server(host="0.0.0.0", port=8081)
    print("=== FIEDLER: HTTP Streaming Proxy STARTED on port 8081 ===", flush=True, file=sys.stderr)
    logger.info("=== FIEDLER: HTTP Streaming Proxy RUNNING on port 8081 ===")

    # Start WebSocket MCP server on port 8080
    host = "0.0.0.0"
    port = 8080
    print(f"=== FIEDLER: About to start WebSocket server on {host}:{port} ===", flush=True, file=sys.stderr)
    logger.info(f"=== FIEDLER STARTUP: Starting WebSocket MCP server on {host}:{port} ===")

    try:
        print(f"=== FIEDLER: Calling websockets.serve ===", flush=True, file=sys.stderr)
        async with websockets.serve(handle_client, host, port):
            print(f"=== FIEDLER: WebSocket server STARTED on port {port} ===", flush=True, file=sys.stderr)
            logger.info(f"=== FIEDLER STARTUP: WebSocket MCP server RUNNING on ws://{host}:{port} ===")
            logger.info(f"=== FIEDLER STARTUP: Both servers operational (MCP: 8080, Proxy: 8081) ===")
            await asyncio.Future()  # Run forever
    except Exception as e:
        print(f"=== FIEDLER ERROR: {e} ===", flush=True, file=sys.stderr)
        logger.error(f"=== FIEDLER ERROR: Failed to start WebSocket server: {e} ===", exc_info=True)
        raise


def main():
    """Synchronous entry point for console script."""
    import sys
    print("=== FIEDLER: main() ENTRY POINT ===", flush=True, file=sys.stderr)
    print("=== FIEDLER: About to call asyncio.run(_amain()) ===", flush=True, file=sys.stderr)
    try:
        asyncio.run(_amain())
    except Exception as e:
        print(f"=== FIEDLER FATAL ERROR: {e} ===", flush=True, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
