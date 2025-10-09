import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Callable

import pytest
import pytest_asyncio
import websockets
from websockets.server import WebSocketServer, serve

from joshua_network.server import Server
from joshua_network.errors import ToolError

# Configure logging for tests to aid in debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def unused_tcp_port() -> int:
    """Find and yield an unused TCP port to prevent test collisions."""
    import socket
    from contextlib import closing
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

@pytest.fixture
def mock_tool_handler() -> Callable:
    """A mock tool handler that can be configured to test different scenarios."""
    def handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
        if arguments.get("should_error"):
            raise ToolError(code=-32001, message="Tool failed as requested")
        if arguments.get("unhandled_exception"):
            raise ValueError("An unexpected error occurred")
        return {"status": "success", "input": arguments}
    return handler

@pytest_asyncio.fixture
async def joshua_server(unused_tcp_port: int, mock_tool_handler: Callable) -> AsyncGenerator[Server, None]:
    """Starts a joshua_network.Server instance with a mock tool for testing."""
    tool_handlers = {
        "test_tool": mock_tool_handler
    }
    server = Server(port=unused_tcp_port, tool_handlers=tool_handlers)
    server_task = asyncio.create_task(server.start())

    # Give the server a moment to start up before yielding
    await asyncio.sleep(0.01)

    yield server

    # Teardown: ensure server is stopped cleanly
    await server.stop()
    await server_task

@pytest_asyncio.fixture
async def mock_godot_server(unused_tcp_port: int) -> AsyncGenerator[Dict[str, Any], None]:
    """
    A mock Godot WebSocket server that listens for log messages.
    It stores received messages in a queue for assertions in tests.
    """
    received_messages = asyncio.Queue()

    async def handler(websocket):
        try:
            async for message in websocket:
                await received_messages.put(json.loads(message))
        except websockets.ConnectionClosed:
            pass

    server: WebSocketServer = await serve(handler, "0.0.0.0", unused_tcp_port)

    context = {
        "port": unused_tcp_port,
        "url": f"ws://localhost:{unused_tcp_port}",
        "messages": received_messages
    }

    yield context

    # Teardown: close the mock server
    server.close()
    await server.wait_closed()
