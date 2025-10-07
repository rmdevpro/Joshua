Creating a standardized Python library for WebSocket MCP server implementation, called `iccm-network`, involves refining the best practices from existing implementations and resolving the identified connection issues. The core features will include seamless JSON-RPC 2.0 handling, connection stability, logging, and zero configuration.

### 1. Library API Design

The `iccm-network` library will contain the following classes and methods:

#### Classes and Methods

1. **MCPServer**
   - **Attributes:**
     - `name`: str - Name of the MCP Server
     - `version`: str - Version of the MCP Server
     - `port`: int - Port for the WebSocket connection
     - `tools`: dict - Dictionary of tool definitions
   - **Methods:**
     - `__init__(self, name: str, version: str, port: int, tools: dict)`: Initializes the server.
     - `start(self)`: Starts the WebSocket server.
     - `stop(self)`: Stops the WebSocket server.
     - `handle_request(self, websocket, path)`: Handles incoming requests from clients.
     - `process_request(self, request: dict)`: Processes a JSON-RPC request and routes commands accordingly.
     - `prepare_response(self, result: Any, request_id: Any)`: Prepares the JSON-RPC response.

2. **MCPClient (optional)**
   - **Methods:**
     - `__init__(self, name: str, port: int)`: Initializes the MCP Client.
     - `call(self, method: str, params: dict)`: Calls the specified method on the MCP server.

3. **Logging**
   - Optional logging integration which can be hooked into the server to handle logs via an external service such as Godot.

#### Protocol Error Handling
- Standard error response structure will follow JSON-RPC 2.0 protocol with various predefined error codes.

### 2. Implementation Code for MCPServer Class

The implementation of the `MCPServer` class will be as follows:

```python
import asyncio
import json
import logging
import websockets
from websockets.server import WebSocketServerProtocol
from typing import Any, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServer:
    """Standardized WebSocket MCP Server for ICCM."""

    def __init__(self, name: str, version: str, port: int, tools: dict):
        self.name = name
        self.version = version
        self.port = port
        self.tools = tools
        self.server = None

    async def handle_request(self, websocket: WebSocketServerProtocol, path: str):
        logger.info(f"Client connected from {websocket.remote_address}")

        try:
            async for message in websocket:
                request = json.loads(message)
                response = await self.process_request(request)
                await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON-RPC request."""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        logger.debug(f"Processing request: {method}")

        if method == "initialize":
            logger.info("Client initializing MCP connection")
            return {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.name, "version": self.version}
                },
                "id": request_id
            }

        elif method == "tools/list":
            logger.info(f"Listing {len(self.tools)} available tools")
            return {
                "jsonrpc": "2.0",
                "result": {"tools": [{"name": name, **spec} for name, spec in self.tools.items()]},
                "id": request_id
            }

        # Additional tool calls would follow the same pattern
        # Return an error if the method is not found
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}
            },
            "id": request_id
        }

    async def start(self):
        """Start the MCP server."""
        logger.info(f"Starting MCP Server '{self.name}' on port {self.port}")
        self.server = await websockets.serve(self.handle_request, "0.0.0.0", self.port)
        await asyncio.Future()  # Run forever

    async def stop(self):
        """Stop the MCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("MCP Server stopped")
```

### 3. Protocol Handler for JSON-RPC 2.0

The `process_request` function in the `MCPServer` class will handle the JSON-RPC 2.0 protocol, ensuring proper structure for both requests and responses as illustrated above. 

### 4. Migration Guide for Existing Components

To migrate from existing components to the `iccm-network` library:

1. **Import the new library**: Replace all instances of custom WebSocket server implementations with `from iccm_network import MCPServer`.

2. **Instantiate MCPServer**:
   - Replace server initialization with:
     ```python
     server = MCPServer(name="component_name", version="1.0.0", port=YOUR_PORT, tools={...})
     ```

3. **Run the server**:
   - Start server using `await server.start()`.

4. **Adapt tool calls**:
   - Ensure tools are defined consistently as dictionaries that can inform the new server's listing.

5. **Remove legacy connection error handling**:
   - Replace custom WebSocket connection management code with the simplified error handling mechanisms of the new server.

### Conclusion

By adopting the `iccm-network` library, all ICCM microservices will have a standardized and reliable means of handling WebSocket connections via JSON-RPC 2.0, significantly reducing debugging time and increasing stability across the network.