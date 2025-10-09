import asyncio
import logging

import pytest
import pytest_asyncio

from joshua_network.client import Client
from joshua_network.server import Server
from joshua_logger import logger as joshua_default_logger

pytestmark = pytest.mark.asyncio
logger = logging.getLogger(__name__)

async def tool_handler_with_logging(arguments):
    """A tool handler that uses the joshua_logger to simulate a real service."""
    logger.info(f"Tool handler received arguments: {arguments}")
    await joshua_default_logger.log(
        level="INFO",
        message="Executing tool_handler_with_logging",
        component="test_integration_server",
        data=arguments
    )
    if arguments.get("magic_word") == "please":
        return {"status": "granted", "args": arguments}
    return {"status": "denied"}

@pytest_asyncio.fixture
async def integration_server(unused_tcp_port):
    """A server fixture that uses a tool handler with logging capabilities."""
    server = Server(
        port=unused_tcp_port,
        tool_handlers={"log_and_execute": tool_handler_with_logging}
    )
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.01) # let server start
    yield server
    await server.stop()
    await server_task

@pytest.mark.usefixtures("integration_server")
async def test_relay_pattern_simulation(integration_server, mock_godot_server, mocker):
    """
    Tests the full end-to-end "Relay Pattern":
    1. A Client calls a tool on the Server.
    2. The Server's tool handler uses the default joshua_logger to log the event.
    3. The mock_godot_server receives the log message from the Server.
    4. The Client receives the correct tool result from the Server.
    """
    # Configure the default logger instance to point to our mock Godot server
    mocker.patch.object(joshua_default_logger, 'url', mock_godot_server["url"])
    mocker.patch.object(joshua_default_logger, 'timeout', 1.0)

    # 1. Client calls a tool
    client = Client(url=f"ws://localhost:{integration_server.port}")
    tool_args = {"magic_word": "please", "user_id": 123}

    result = await client.call_tool("log_and_execute", tool_args)

    # 4. The Client receives the correct tool result
    assert result == {"status": "granted", "args": tool_args}

    # 3. The mock_godot_server receives the log message
    log_message = await asyncio.wait_for(mock_godot_server["messages"].get(), timeout=1)

    assert log_message["method"] == "tools/call"
    log_params = log_message["params"]["arguments"]
    assert log_params["level"] == "INFO"
    assert log_params["message"] == "Executing tool_handler_with_logging"
    assert log_params["component"] == "test_integration_server"
    assert log_params["data"] == tool_args

    # Clean up connections
    await client.disconnect()
    await joshua_default_logger.close()
