#!/usr/bin/env python3
"""
Minimal test of iccm-network library without Horace dependencies.

This tests ONLY the library functionality:
- Server starts
- Binds to 0.0.0.0:8070
- Responds to JSON-RPC 2.0 requests
- Health check works
"""

import asyncio
import sys
sys.path.insert(0, '/app')

from iccm_network import MCPServer, MCPToolError


# Simple test tool
async def test_tool_handler(message: str = "Hello") -> dict:
    """A simple test tool that just echoes a message."""
    return {"echo": message, "status": "success"}


# Tool definitions
TOOLS = {
    "test_echo": {
        "description": "Echo a message back",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo",
                    "default": "Hello"
                }
            }
        }
    }
}

# Tool handlers
HANDLERS = {
    "test_echo": test_tool_handler
}


async def main():
    """Run minimal MCP server for testing."""
    print("=" * 60)
    print("iccm-network Library Test Server")
    print("=" * 60)
    print()
    print("This server tests ONLY the iccm-network library.")
    print("No Horace database or business logic required.")
    print()

    server = MCPServer(
        name="test-server",
        version="1.0.0",
        port=8070,
        tool_definitions=TOOLS,
        tool_handlers=HANDLERS
    )

    print("Starting server...")
    print("Health check: http://0.0.0.0:8070/healthz")
    print("WebSocket: ws://0.0.0.0:8070")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
