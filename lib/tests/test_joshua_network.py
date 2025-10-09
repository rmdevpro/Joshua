import asyncio
import json

import aiohttp
import pytest
import websockets
from websockets.exceptions import ConnectionClosed

from joshua_network.client import Client
from joshua_network.server import Server
from joshua_network.errors import ToolError

pytestmark = pytest.mark.asyncio


class TestToolError:
    def test_tool_error_creation(self):
        """Tests that ToolError can be instantiated correctly."""
        error = ToolError(code=-32000, message="Test error")
        assert error.code == -32000
        assert error.message == "Test error"

    def test_tool_error_to_json_rpc_error(self):
        """Tests serialization to the JSON-RPC error format."""
        error = ToolError(code=-32001, message="Another test")
        json_rpc_error = error.to_json_rpc_error()
        assert json_rpc_error == {"code": -32001, "message": "Another test"}


class TestServer:
    async def test_server_starts_and_binds(self, joshua_server: Server):
        """Verifies the server starts, binds to a port, and is serving."""
        assert joshua_server.is_serving()
        assert joshua_server.port > 0

    async def test_health_check_endpoint(self, joshua_server: Server):
        """Verifies the /healthz HTTP endpoint responds with 'OK'."""
        url = f"http://localhost:{joshua_server.port}/healthz"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                assert response.status == 200
                text = await response.text()
                assert text == "OK"

    async def test_websocket_connection_and_handshake(self, joshua_server: Server):
        """Tests a client can connect and perform the JSON-RPC handshake."""
        uri = f"ws://localhost:{joshua_server.port}"
        async with websockets.connect(uri) as ws:
            # Initialize
            init_req = {"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}
            await ws.send(json.dumps(init_req))
            response = json.loads(await ws.recv())
            assert response["id"] == 1
            assert "result" in response
            assert response["result"]["serverInfo"]["name"] == "joshua_network_server"

    async def test_tools_list(self, joshua_server: Server):
        """Tests the tools/list method returns the registered tools."""
        uri = f"ws://localhost:{joshua_server.port}"
        async with websockets.connect(uri) as ws:
            req = {"jsonrpc": "2.0", "method": "tools/list", "id": 2}
            await ws.send(json.dumps(req))
            response = json.loads(await ws.recv())
            assert response["id"] == 2
            assert "result" in response
            assert "tools" in response["result"]
            assert len(response["result"]["tools"]) == 1
            assert response["result"]["tools"][0]["name"] == "test_tool"

    async def test_tool_call_routes_correctly(self, joshua_server: Server):
        """Tests a valid tool call is routed to its handler and returns a result."""
        uri = f"ws://localhost:{joshua_server.port}"
        async with websockets.connect(uri) as ws:
            req = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "test_tool", "arguments": {"data": 123}},
                "id": 3
            }
            await ws.send(json.dumps(req))
            response = json.loads(await ws.recv())
            assert response["id"] == 3
            assert response["result"] == {"status": "success", "input": {"data": 123}}

    async def test_unknown_tool_call_returns_error(self, joshua_server: Server):
        """Tests calling a non-existent tool returns a 'Method not found' error."""
        uri = f"ws://localhost:{joshua_server.port}"
        async with websockets.connect(uri) as ws:
            req = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "unknown_tool", "arguments": {}},
                "id": 4
            }
            await ws.send(json.dumps(req))
            response = json.loads(await ws.recv())
            assert response["id"] == 4
            assert "error" in response
            assert response["error"]["code"] == -32601

    async def test_tool_handler_toolerror_exception(self, joshua_server: Server):
        """Tests that a ToolError raised by a handler is correctly returned to the client."""
        uri = f"ws://localhost:{joshua_server.port}"
        async with websockets.connect(uri) as ws:
            req = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "test_tool", "arguments": {"should_error": True}},
                "id": 5
            }
            await ws.send(json.dumps(req))
            response = json.loads(await ws.recv())
            assert response["id"] == 5
            assert "error" in response
            assert response["error"]["code"] == -32001
            assert response["error"]["message"] == "Tool failed as requested"

    async def test_tool_handler_unhandled_exception(self, joshua_server: Server):
        """Tests that an unexpected exception returns a generic server error."""
        uri = f"ws://localhost:{joshua_server.port}"
        async with websockets.connect(uri) as ws:
            req = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "test_tool", "arguments": {"unhandled_exception": True}},
                "id": 6
            }
            await ws.send(json.dumps(req))
            response = json.loads(await ws.recv())
            assert response["id"] == 6
            assert "error" in response
            assert response["error"]["code"] == -32000


class TestClient:
    @pytest.fixture
    def client(self, joshua_server: Server):
        """Provides a client instance configured to talk to the test server."""
        return Client(url=f"ws://localhost:{joshua_server.port}", timeout=2)

    async def test_client_connects_on_first_call(self, client: Client):
        """Tests that the client connects implicitly on the first tool call."""
        assert not client.is_connected
        result = await client.call_tool("test_tool", {"arg": "value"})
        assert client.is_connected
        assert result["status"] == "success"
        await client.disconnect()

    async def test_client_disconnects_and_cleans_up(self, client: Client):
        """Tests disconnect() closes the connection and cancels background tasks."""
        await client.connect()
        assert client.is_connected
        assert client._listen_task is not None and not client._listen_task.done()

        await client.disconnect()
        assert not client.is_connected
        assert client.websocket is None
        assert client._listen_task is None or client._listen_task.done()

    async def test_client_handles_timeout(self, joshua_server: Server, mocker):
        """Tests that a request correctly times out if the server is too slow."""
        # Patch the server's handler to introduce a delay
        async def slow_handler(*args, **kwargs):
            await asyncio.sleep(2)
            return {"status": "delayed"}
        mocker.patch.object(joshua_server._tool_handlers["test_tool"], '__call__', side_effect=slow_handler)

        client = Client(url=f"ws://localhost:{joshua_server.port}", timeout=0.5)
        with pytest.raises(asyncio.TimeoutError):
            await client.call_tool("test_tool", {})
        await client.disconnect()

    async def test_client_cleans_pending_requests_on_disconnect(self, client: Client, joshua_server: Server, mocker):
        """Verifies pending requests are failed on disconnect, preventing hangs."""
        handler_started = asyncio.Event()
        async def hanging_handler(*args, **kwargs):
            handler_started.set()
            await asyncio.sleep(10) # Hang to simulate a long-running tool
        mocker.patch.object(joshua_server._tool_handlers["test_tool"], '__call__', side_effect=hanging_handler)

        call_task = asyncio.create_task(client.call_tool("test_tool", {}))
        await handler_started.wait() # Ensure the server has received the request

        # Disconnect the client while the request is pending
        await client.disconnect()

        # The call task should now fail with a ConnectionClosed exception
        with pytest.raises(ConnectionClosed):
            await call_task

    async def test_client_reconnects_after_disconnect(self, client: Client):
        """Tests that the client automatically reconnects on the next call after a disconnect."""
        await client.call_tool("test_tool", {"run": 1})
        assert client.is_connected

        await client.disconnect()
        assert not client.is_connected

        # This call should trigger an automatic reconnect
        result = await client.call_tool("test_tool", {"run": 2})
        assert client.is_connected
        assert result["input"] == {"run": 2}
        await client.disconnect()

    async def test_client_handles_server_disappearance(self, client: Client, joshua_server: Server):
        """Tests client behavior when the server connection is lost abruptly."""
        await client.connect()
        assert client.is_connected

        # Stop the server abruptly
        await joshua_server.stop()

        # The next call should fail because it cannot reconnect
        with pytest.raises(ConnectionRefusedError):
             await client.call_tool("test_tool", {})

        assert not client.is_connected
