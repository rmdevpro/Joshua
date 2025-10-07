"""
iccm-network: Standardized MCP networking library for ICCM components

This library eliminates the recurring WebSocket connection issues that have
plagued ICCM development by providing a battle-tested, zero-configuration
MCP server implementation.

Problem Solved:
- Components binding to 127.0.0.1 instead of 0.0.0.0 (can't connect from network)
- Inconsistent JSON-RPC 2.0 protocol implementation
- Different error handling approaches across components
- Hours wasted debugging timeouts and connection failures

Usage:
    ```python
    from iccm_network import MCPServer, MCPToolError

    # Define your tools
    async def my_tool_handler(arg1: str, arg2: int) -> dict:
        if not arg1:
            raise MCPToolError("arg1 is required", code=-32602)
        return {"result": f"Processed {arg1} with {arg2}"}

    # Create server
    server = MCPServer(
        name="my_service",
        version="1.0.0",
        port=9000,
        tool_definitions={
            "my_tool": {
                "description": "Does something useful",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "arg1": {"type": "string"},
                        "arg2": {"type": "integer"}
                    },
                    "required": ["arg1", "arg2"]
                }
            }
        },
        tool_handlers={
            "my_tool": my_tool_handler
        }
    )

    # Start server (runs forever)
    await server.start()
    ```

Components using this library:
- Horace (testbed - first implementation)
- Dewey (migration planned)
- Fiedler (migration planned)
- Godot (migration planned)

Design based on synthesis of:
- Dewey's reliable implementation patterns
- Fiedler's HTTP proxy integration
- Gemini-2.5-pro's root cause analysis
- GPT-4o-mini's simplified API design
- DeepSeek's decorator pattern considerations

Version: 1.1.0

Changelog:
- v1.1.0: Added notification handling, WebSocket keep-alives, health check endpoint
- v1.0.0: Initial synthesis from triplet reviews
"""

from .server import MCPServer, MCPToolError
from .client import MCPClient

__version__ = "1.2.0"
__all__ = ["MCPServer", "MCPClient", "MCPToolError"]
