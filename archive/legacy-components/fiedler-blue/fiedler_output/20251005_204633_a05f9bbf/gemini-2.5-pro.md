Excellent request. This is a classic and critical engineering problem: standardizing infrastructure to eliminate recurring bugs and accelerate development. The provided code examples are perfect for this analysis.

Here is a complete design and implementation for the `iccm-network` library.

### Analysis: What Makes Dewey Reliable? Why Do Godot/Horace Fail?

The core issue lies in how a server process inside a container binds to a network interface.

1.  **Localhost vs. Network:**
    *   When you run a server on your local machine and connect from a client on the *same machine*, using `localhost` or `127.0.0.1` as the host works fine.
    *   When you run that same server inside a Docker container, `localhost` refers to the container's *internal* network namespace. It is completely isolated.
    *   For another container (like the MCP relay) to connect to it, the server must bind to `0.0.0.0`. This special address means "listen on all available network interfaces," including the one connected to the Docker bridge network.

2.  **What Dewey and Fiedler Do Right:**
    *   Both Dewey and Fiedler explicitly use `host = "0.0.0.0"` when calling `websockets.serve()`. This is the single most important reason they are reliable from the network.
    *   `Dewey`: `self.server = await websockets.serve(self.handle_request, self.host, self.port)` where `self.host` is configured to be `0.0.0.0`.
    *   `Fiedler`: `async with websockets.serve(handle_client, "0.0.0.0", port):` The host is hardcoded correctly.

3.  **Why Godot and Horace Fail (The Root Cause):**
    *   The code for Godot shows `websockets.serve(handle_client, "0.0.0.0", config.MCP_PORT)`. This *should* work. However, the fact that it fails from the network suggests that in the actual deployed environment, the configuration being used is likely `localhost` or `127.0.0.1`.
    *   Horace's code is more revealing: `server = HoraceMCPServer(config.MCP_HOST, config.MCP_PORT)`. This pattern allows a developer to easily set `MCP_HOST=localhost` for local testing, forget to change it for deployment, and cause the exact timeout issue described. The relay tries to connect to `horace-mcp:8070`, which resolves to the container's IP, but the server inside is only listening for connections to `127.0.0.1`, so the connection is refused, resulting in a timeout.

The `iccm-network` library will solve this by **removing the `host` configuration entirely** and forcing it to `0.0.0.0` internally.

---

### 1. Library API Design

The API should be simple, declarative, and hide all networking boilerplate.

#### `iccm_network/server.py`

```python
from typing import Dict, Any, Callable, Awaitable

class MCPServer:
    """
    A standardized, zero-configuration WebSocket MCP server for ICCM microservices.
    This server automatically handles JSON-RPC 2.0 protocol, error responses,
    and binds to the correct network interface for containerized environments.
    """

    def __init__(
        self,
        name: str,
        version: str,
        port: int,
        tool_definitions: Dict[str, Any],
        tool_handlers: Dict[str, Callable[..., Awaitable[Any]]],
    ):
        """
        Initializes the MCP Server.

        Args:
            name: The name of the microservice (e.g., "horace").
            version: The version of the microservice (e.g., "1.0.0").
            port: The TCP port to listen on.
            tool_definitions: A dictionary defining the tool schemas, keyed by tool name.
                              (e.g., {"horace_register_file": {"description": ...}}).
            tool_handlers: A dictionary mapping tool names to their async handler functions.
                           (e.g., {"horace_register_file": my_async_func}).
        """
        # ... implementation ...

    async def start(self):
        """
        Starts the MCP server and runs forever.
        This method handles graceful shutdown on KeyboardInterrupt.
        """
        # ... implementation ...

    async def stop(self):
        """
        Stops the MCP server gracefully.
        """
        # ... implementation ...

# Custom exception for tools to raise structured errors
class MCPToolError(Exception):
    """Custom exception for tool-specific errors."""
    def __init__(self, message: str, code: int = -32000, data: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data
```

---

### 2. Implementation Code for `MCPServer` Class

This is the complete, self-contained library code.

**File: `iccm_network/server.py`**

```python
import asyncio
import json
import logging
from typing import Dict, Any, Callable, Awaitable, List

import websockets
from websockets.server import WebSocketServer, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

# Configure a logger for the library
logger = logging.getLogger("iccm_network")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class MCPToolError(Exception):
    """Custom exception for tool-specific errors.
    Allows tools to return structured JSON-RPC errors.
    """
    def __init__(self, message: str, code: int = -32000, data: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data

class MCPServer:
    """
    A standardized, zero-configuration WebSocket MCP server for ICCM microservices.
    This server automatically handles JSON-RPC 2.0 protocol, error responses,
    and binds to the correct network interface for containerized environments.
    """

    def __init__(
        self,
        name: str,
        version: str,
        port: int,
        tool_definitions: Dict[str, Any],
        tool_handlers: Dict[str, Callable[..., Awaitable[Any]]],
    ):
        """
        Initializes the MCP Server.

        Args:
            name: The name of the microservice (e.g., "horace").
            version: The version of the microservice (e.g., "1.0.0").
            port: The TCP port to listen on.
            tool_definitions: A dictionary defining the tool schemas, keyed by tool name.
            tool_handlers: A dictionary mapping tool names to their async handler functions.
        """
        if not all(k in tool_handlers for k in tool_definitions.keys()):
            raise ValueError("Mismatch between tool_definitions and tool_handlers. All defined tools must have a handler.")

        self.name = name
        self.version = version
        self.port = port
        self.tool_definitions = tool_definitions
        self.tool_handlers = tool_handlers
        
        # CRITICAL: Always bind to 0.0.0.0 to be accessible from other containers.
        # This is the core fix for the network timeout issues.
        self.host = "0.0.0.0"
        
        self._server: WebSocketServer = None

    async def start(self):
        """
        Starts the MCP server and runs until stopped.
        """
        if self._server:
            logger.warning("Server is already running.")
            return
            
        logger.info(f"Starting {self.name} MCP server v{self.version} on {self.host}:{self.port}")
        
        try:
            self._server = await websockets.serve(
                self._connection_handler,
                self.host,
                self.port
            )
            logger.info(f"Server is listening on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
        except OSError as e:
            logger.error(f"Failed to start server on port {self.port}: {e}")
            raise
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Shutdown signal received.")
        finally:
            await self.stop()

    async def stop(self):
        """
        Stops the MCP server gracefully.
        """
        if self._server:
            logger.info("Stopping MCP server...")
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            logger.info("MCP server stopped.")

    async def _connection_handler(self, websocket: WebSocketServerProtocol, path: str):
        """Handles a single client WebSocket connection."""
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected from {client_addr}")

        try:
            async for message in websocket:
                response = await self._process_message(message)
                await websocket.send(json.dumps(response))
        except ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"Unhandled error in connection handler for {client_addr}: {e}", exc_info=True)
            # Try to send a final error message if the connection is still open
            if websocket.open:
                error_response = self._create_error_response(-32603, "Internal server error", None)
                await websocket.send(json.dumps(error_response))

    async def _process_message(self, message: str) -> Dict[str, Any]:
        """Parses and routes a single JSON-RPC message."""
        request = {}
        try:
            request = json.loads(message)
            request_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            logger.debug(f"Received method '{method}' with id '{request_id}'")

            if method == "initialize":
                return self._handle_initialize(request_id)
            elif method == "tools/list":
                return self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params)
            else:
                return self._create_error_response(-32601, f"Method not found: {method}", request_id)

        except json.JSONDecodeError:
            return self._create_error_response(-32700, "Parse error: Invalid JSON", None)
        except Exception as e:
            logger.error(f"Error processing request: {request}. Error: {e}", exc_info=True)
            request_id = request.get("id") if isinstance(request, dict) else None
            return self._create_error_response(-32603, f"Internal server error: {e}", request_id)

    def _handle_initialize(self, request_id: Any) -> Dict[str, Any]:
        """Handles the 'initialize' MCP method."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version},
            },
        }

    def _handle_tools_list(self, request_id: Any) -> Dict[str, Any]:
        """Handles the 'tools/list' MCP method."""
        tools_list = [
            {"name": name, **spec} for name, spec in self.tool_definitions.items()
        ]
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools_list},
        }

    async def _handle_tools_call(self, request_id: Any, params: Dict) -> Dict[str, Any]:
        """Handles the 'tools/call' MCP method."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        handler = self.tool_handlers.get(tool_name)
        if not handler:
            return self._create_error_response(-32601, f"Tool not found: {tool_name}", request_id)
        
        logger.info(f"Executing tool: {tool_name}")
        try:
            result = await handler(**arguments)
            
            # Per MCP spec, tool result must be wrapped in a content block.
            # We standardize on JSON output for consistency.
            content = [{"type": "text", "text": json.dumps(result, default=str)}]
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": content},
            }
        except MCPToolError as e:
            logger.warning(f"Tool '{tool_name}' failed with controlled error: {e.message}")
            return self._create_error_response(e.code, e.message, request_id, e.data)
        except TypeError as e:
            # Catches missing/incorrect arguments
            logger.error(f"Tool '{tool_name}' called with invalid arguments: {e}")
            return self._create_error_response(-32602, f"Invalid params: {e}", request_id)
        except Exception as e:
            logger.error(f"Unhandled exception in tool '{tool_name}': {e}", exc_info=True)
            return self._create_error_response(-32603, f"Internal server error while executing tool: {e}", request_id)

    def _create_error_response(self, code: int, message: str, request_id: Any, data: Any = None) -> Dict[str, Any]:
        """Creates a standardized JSON-RPC 2.0 error response."""
        error_obj = {"code": code, "message": message}
        if data:
            error_obj["data"] = data
        return {"jsonrpc": "2.0", "id": request_id, "error": error_obj}

```
**File: `iccm_network/__init__.py`**
```python
from .server import MCPServer, MCPToolError

__all__ = ["MCPServer", "MCPToolError"]
```
**File: `pyproject.toml` (for packaging)**
```toml
[project]
name = "iccm-network"
version = "1.0.0"
dependencies = [
    "websockets>=11.0"
]
[tool.setuptools.packages.find]
where = ["."]
```

---

### 3. Protocol Handler for JSON-RPC 2.0

The protocol handling is implemented privately within the `MCPServer` class in the methods:
*   `_connection_handler`: Manages the WebSocket lifecycle.
*   `_process_message`: Parses JSON and routes to specific handlers.
*   `_handle_initialize`, `_handle_tools_list`, `_handle_tools_call`: Implement the specific MCP methods.
*   `_create_error_response`: A utility to ensure all errors conform to the JSON-RPC 2.0 spec.

This design encapsulates the protocol completely, so developers using the library only need to provide their business logic (the tool handlers).

---

### 4. Migration Guide for Existing Components

Migrating an existing component like Horace to `iccm-network` is now a simple refactoring task.

**Component: Horace**

#### Before Migration (`src/mcp_server.py`)

The file contains the `HoraceMCPServer` class with ~150 lines of boilerplate for handling requests, processing JSON-RPC, starting the server, etc.

#### After Migration (`src/mcp_server.py`)

The new file will be dramatically shorter and focused only on Horace's logic.

```python
# src/mcp_server.py
import asyncio

# 1. Import the new library
from iccm_network import MCPServer, MCPToolError
from .config import config
from .database import Database
from .tools import Tools
from .utils.logger import logger
from .exceptions import HoraceError, DuplicateFileError # Keep your app-specific exceptions

async def main():
    """Main entry point for Horace MCP Server."""
    
    # --- Step 2: Initialize application logic (same as before) ---
    db = Database()
    await db.connect()
    tools_instance = Tools(db)
    logger.info("Horace database and tools initialized.")

    # --- Step 3: Define tool schemas and handlers for the library ---
    
    # Tool schemas (copy-pasted from the old HoraceMCPServer class)
    tool_definitions = {
        "horace_register_file": {
            "description": "Register a file with Horace catalog",
            # ... rest of the schema
        },
        "horace_search_files": {
            "description": "Search file catalog by metadata",
            # ... rest of the schema
        },
        # ... all other tool schemas
    }

    # Custom wrapper to adapt existing tool methods to the library's error handling
    async def horace_register_file_handler(**kwargs):
        try:
            return await tools_instance.horace_register_file(kwargs)
        except DuplicateFileError as e:
            # Per spec, this is a success case with a specific message
            return {"file_id": e.file_id, "message": e.message}
        except HoraceError as e:
            # Convert application error to a standard library error
            raise MCPToolError(message=e.message, data={"error_code": e.error_code})

    # Tool handlers mapping names to the async functions
    tool_handlers = {
        "horace_register_file": horace_register_file_handler,
        "horace_search_files": lambda **kwargs: tools_instance.horace_search_files(kwargs),
        "horace_get_file_info": lambda **kwargs: tools_instance.horace_get_file_info(kwargs),
        # ... map all other tools
    }

    # --- Step 4: Instantiate and start the server ---
    server = MCPServer(
        name="horace",
        version="1.0.0",
        port=config.MCP_PORT,
        tool_definitions=tool_definitions,
        tool_handlers=tool_handlers
    )

    try:
        await server.start()
    finally:
        await db.disconnect()
        logger.info("Horace has shut down.")

if __name__ == "__main__":
    asyncio.run(main())
```

**Summary of Migration Steps:**

1.  **Add Dependency:** Add `iccm-network` to the component's `requirements.txt` or `pyproject.toml`.
2.  **Delete Boilerplate:** Remove the entire custom `MCPServer` class and its methods (`handle_request`, `process_request`, `start`, `stop`).
3.  **Refactor `main`:**
    *   Import `MCPServer` from `iccm-network`.
    *   Collect the tool schemas into a `tool_definitions` dictionary.
    *   Collect the tool implementation functions into a `tool_handlers` dictionary.
    *   Instantiate `MCPServer` with the service name, port, and the two dictionaries.
    *   Call `await server.start()`.
4.  **Update Error Handling (Optional but Recommended):** Modify tool functions to raise `MCPToolError` for controlled, application-specific errors instead of returning custom error dictionaries.

This migration eliminates ~90% of the networking code in each microservice, enforces the critical `0.0.0.0` binding, and guarantees a consistent, reliable implementation of the MCP protocol across the entire system. Debugging time for connection issues will drop to near zero.
