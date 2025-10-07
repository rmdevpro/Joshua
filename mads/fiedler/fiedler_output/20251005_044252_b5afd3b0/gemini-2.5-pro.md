Of course. This is a critical issue, and a clear path forward is needed. The non-existent `mcp-tools-py` library was likely a placeholder from the synthesis process. We will replace it with a direct implementation using the `websockets` library, following the established patterns in your ICCM examples.

### 1. Recommended Architecture

**Option A is the correct and most robust approach.**

*   **Rationale:** Copying the proven pattern from Dewey ensures compatibility and leverages a known-good architecture within your ecosystem. It avoids adding unnecessary complexity like a stdio bridge (Option B) and uses the specified `websockets` library directly. This approach provides a clean separation of concerns: a reusable MCP client and a dedicated MCP server for the facade.

We will create a small, reusable MCP module within the Godot `src` directory to house the new client and server implementations.

### 2. Proposed Code Structure

I recommend creating a new `src/mcp` directory to encapsulate the WebSocket-based MCP logic.

```
godot/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py      # NEW: Reusable MCP Client (for worker and server)
│   │   └── server.py      # NEW: Reusable MCP Server (for facade)
│   ├── mcp_server.py    # REFACTORED: Godot Facade Server
│   └── worker.py        # REFACTORED: Godot Worker
├── requirements.txt     # UPDATED
└── supervisord.conf     # NO CHANGE NEEDED
```

---

### 3. Implementation Guidance & Code

Here are the specific code implementations for the new and refactored files.

#### **Step 1: Create the Reusable MCP Client**

This client will handle connecting, sending JSON-RPC messages, and correlating responses. Both `mcp_server.py` (for proxying) and `worker.py` will use this.

**File: `src/mcp/client.py`**
```python
import asyncio
import json
import logging
import uuid
from typing import Any, Dict

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)

class MCPClient:
    """A WebSocket-based MCP client using the JSON-RPC protocol."""

    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.timeout = timeout
        self.websocket: WebSocketClientProtocol | None = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._listen_task: asyncio.Task | None = None

    @property
    def is_connected(self) -> bool:
        """Check if the WebSocket is connected and open."""
        return self.websocket is not None and self.websocket.open

    async def connect(self):
        """Establishes a WebSocket connection and starts the listener task."""
        if self.is_connected:
            logger.warning("Already connected.")
            return

        try:
            logger.info(f"Connecting to MCP server at {self.url}...")
            self.websocket = await websockets.connect(self.url)
            self._listen_task = asyncio.create_task(self._listen())
            logger.info(f"Successfully connected to {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.url}: {e}")
            self.websocket = None
            raise

    async def disconnect(self):
        """Closes the WebSocket connection."""
        if self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        logger.info("MCP client disconnected.")

    async def _listen(self):
        """Listens for incoming messages and resolves pending requests."""
        try:
            async for message in self.websocket:
                try:
                    response = json.loads(message)
                    request_id = response.get("id")
                    if request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        if "error" in response:
                            future.set_exception(RuntimeError(f"MCP Error: {response['error']}"))
                        else:
                            # Extract result from standard tool call response
                            result = response.get("result", {})
                            if isinstance(result, dict) and "content" in result:
                                try:
                                    # The content is often a JSON string inside a text block
                                    content_text = result["content"][0]["text"]
                                    future.set_result(json.loads(content_text))
                                except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                                    # Fallback for non-standard or simple results
                                    future.set_result(result)
                            else:
                                future.set_result(result)

                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON response: {message}")
                except Exception as e:
                    logger.exception(f"Error processing incoming message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed by server.")
        finally:
            # Clean up any pending requests on disconnect
            for future in self._pending_requests.values():
                if not future.done():
                    future.set_exception(ConnectionAbortedError("WebSocket connection lost."))
            self._pending_requests.clear()
            self.websocket = None


    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Calls a tool on the remote MCP server.

        Args:
            tool_name: The name of the tool to call.
            arguments: A dictionary of arguments for the tool.

        Returns:
            The result from the tool call.
        """
        if not self.is_connected:
            raise ConnectionError("MCP client is not connected.")

        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": request_id,
        }

        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            await self.websocket.send(json.dumps(request))
            return await asyncio.wait_for(future, timeout=self.timeout)
        except Exception as e:
            # Clean up the pending request if something goes wrong
            self._pending_requests.pop(request_id, None)
            raise e
```

#### **Step 2: Create the MCP Server Base Class**

This is a simplified version of the Dewey server, designed specifically for Godot's needs.

**File: `src/mcp/server.py`**
```python
import asyncio
import json
import logging
from typing import Callable, Coroutine, Dict, Any

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

class MCPServer:
    """A WebSocket-based MCP server using the JSON-RPC protocol."""

    def __init__(self):
        self._tools: Dict[str, Callable[..., Coroutine]] = {}

    def register_tool(self, func: Callable[..., Coroutine]):
        """Registers an async function as an available tool."""
        tool_name = func.__name__
        if tool_name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool_name}")
        self._tools[tool_name] = func
        logger.info(f"Registered tool: {tool_name}")

    async def _handler(self, websocket: WebSocketServerProtocol, path: str):
        """Handles a single client connection."""
        logger.info(f"Client connected from {websocket.remote_address}")
        try:
            async for message in websocket:
                response = {}
                request = {}
                try:
                    request = json.loads(message)
                    response = await self._process_request(request)
                except json.JSONDecodeError:
                    response = self._create_error_response(-32700, "Parse error", None)
                except Exception as e:
                    logger.exception(f"Error processing request: {request}")
                    request_id = request.get("id") if isinstance(request, dict) else None
                    response = self._create_error_response(-32603, f"Internal server error: {e}", request_id)

                await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {websocket.remote_address} disconnected.")
        except Exception as e:
            logger.error(f"Handler error for {websocket.remote_address}: {e}")

    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a valid JSON-RPC request and calls the appropriate tool."""
        request_id = request.get("id")
        if request.get("method") != "tools/call":
            return self._create_error_response(-32601, "Method not found. Only 'tools/call' is supported.", request_id)

        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            return self._create_error_response(-32602, "Invalid params: 'name' is required.", request_id)

        tool_func = self._tools.get(tool_name)
        if not tool_func:
            return self._create_error_response(-32601, f"Tool not found: {tool_name}", request_id)

        logger.info(f"Calling tool '{tool_name}' with args: {arguments}")
        try:
            result = await tool_func(**arguments)
            # Standard MCP tool response wraps result in a specific structure
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}]
                },
                "id": request_id,
            }
        except Exception as e:
            logger.exception(f"Error executing tool '{tool_name}'")
            return self._create_error_response(-32000, f"Tool execution error: {e}", request_id)

    def _create_error_response(self, code: int, message: str, request_id: Any) -> Dict[str, Any]:
        """Creates a JSON-RPC error response dictionary."""
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": request_id,
        }

    async def start(self, host: str, port: int):
        """Starts the WebSocket server."""
        logger.info(f"Starting MCP server on {host}:{port}...")
        async with websockets.serve(self._handler, host, port):
            await asyncio.Future()  # Run forever
```

#### **Step 3: Refactor the Godot MCP Facade Server**

Update `mcp_server.py` to use the new `MCPServer` and `MCPClient`. The business logic in the tool functions remains unchanged.

**File: `src/mcp_server.py` (Refactored)**
```python
import asyncio
import json
import logging
import time
import redis.asyncio as redis
from src.mcp.server import MCPServer  # UPDATED
from src.mcp.client import MCPClient  # UPDATED
import src.config as config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [MCP_SERVER] %(message)s')

redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
dewey_client = MCPClient(config.DEWEY_MCP_URL)

async def logger_log(component: str, level: str, message: str, trace_id: str = None, data: dict = None):
    """Facade tool to push a single log entry to the Redis queue"""
    log_entry = {
        "component": component,
        "level": level.upper(),
        "message": message,
        "trace_id": trace_id,
        "data": data,
        "created_at": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
    }
    await redis_client.lpush(config.LOG_QUEUE_NAME, json.dumps(log_entry))
    await redis_client.ltrim(config.LOG_QUEUE_NAME, 0, config.MAX_QUEUE_SIZE - 1)
    return {"status": "ok", "message": "Log entry queued."}

async def logger_query(**kwargs):
    """Facade tool that calls dewey_query_logs"""
    logging.info(f"Forwarding query to Dewey: {kwargs}")
    # The new client expects tool name and arguments separately
    return await dewey_client.call_tool("dewey_query_logs", kwargs)

async def logger_clear(**kwargs):
    """Facade tool that calls dewey_clear_logs"""
    logging.info(f"Forwarding clear command to Dewey: {kwargs}")
    return await dewey_client.call_tool("dewey_clear_logs", kwargs)

async def logger_set_level(component: str, level: str):
    """
    Sets the log level for a component.
    Stores config in Redis hash for central management.
    """
    valid_levels = {'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'}
    if level.upper() not in valid_levels:
        raise ValueError(f"Invalid log level '{level}'. Must be one of {valid_levels}")

    await redis_client.hset("logger_config:levels", component, level.upper())
    return {"status": "ok", "message": f"Log level for '{component}' set to '{level.upper()}'."}

async def main():
    logging.info("Starting Godot MCP Server...")
    logging.info(f"Connecting to Dewey at {config.DEWEY_MCP_URL}")
    try:
        await dewey_client.connect()
        logging.info("Connected to Dewey.")
    except Exception as e:
        logging.critical(f"Could not connect to Dewey. Exiting. Error: {e}")
        return

    server = MCPServer()
    server.register_tool(logger_log)
    server.register_tool(logger_query)
    server.register_tool(logger_clear)
    server.register_tool(logger_set_level)

    logging.info(f"Godot MCP server listening on port {config.MCP_PORT}")
    try:
        await server.start(host="0.0.0.0", port=config.MCP_PORT)
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
    finally:
        await dewey_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
```

#### **Step 4: Refactor the Godot Worker**

Update `worker.py` to use the new `MCPClient`. The changes are minimal as the original code's interface was well-designed.

**File: `src/worker.py` (Refactored)**
```python
import asyncio
import json
import logging
import time
import redis.asyncio as redis
from src.mcp.client import MCPClient  # UPDATED
import src.config as config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [WORKER] %(message)s')

async def send_batch_to_dewey(mcp_client, batch):
    """Sends a batch of logs to Dewey with exponential backoff retry (REQ-REL-002)"""
    if not batch:
        return

    log_entries = [json.loads(item) for item in batch]

    delay = config.RETRY_INITIAL_DELAY
    for attempt in range(config.RETRY_MAX_ATTEMPTS):
        try:
            if not mcp_client.is_connected:
                logging.warning("Dewey client disconnected. Attempting to reconnect...")
                await mcp_client.connect()
                logging.info("Reconnected to Dewey.")

            logging.info(f"Sending batch of {len(log_entries)} logs to Dewey.")
            # The new client expects tool name and arguments separately
            await mcp_client.call_tool("dewey_store_logs_batch", {"logs": log_entries})
            logging.info(f"Successfully sent batch of {len(log_entries)} logs.")
            return
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed to send batch to Dewey: {e}")
            if attempt + 1 == config.RETRY_MAX_ATTEMPTS:
                logging.critical("Max retries reached. Discarding batch.")
                break

            logging.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, config.RETRY_MAX_DELAY)

async def main():
    """Main worker loop - consumes logs from Redis and sends to Dewey"""
    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
    mcp_client = MCPClient(config.DEWEY_MCP_URL, timeout=config.DEWEY_CONNECT_TIMEOUT)

    logging.info("Godot worker starting...")
    logging.info(f"Connecting to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}")

    # Initial connection with retry logic
    while not mcp_client.is_connected:
        try:
            await mcp_client.connect()
        except Exception as e:
            logging.error(f"Failed to connect to Dewey on startup: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

    while True:
        try:
            batch = []
            start_time = time.monotonic()

            while len(batch) < config.BATCH_SIZE and (time.monotonic() - start_time) * 1000 < config.BATCH_TIMEOUT_MS:
                try:
                    timeout = max(0.1, (config.BATCH_TIMEOUT_MS / 1000))
                    result = await redis_client.brpop(config.LOG_QUEUE_NAME, timeout=timeout)
                    if result:
                        _, item = result
                        batch.append(item)
                    else:
                        break # Timeout reached
                except redis.ConnectionError as e:
                    logging.error(f"Redis connection error: {e}. Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)
                    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
                    break

            if batch:
                await send_batch_to_dewey(mcp_client, batch)

            # NOTE: The ltrim is handled by the server on push now, but keeping it here
            # provides an extra layer of safety against queue overgrowth.
            await redis_client.ltrim(config.LOG_QUEUE_NAME, 0, config.MAX_QUEUE_SIZE - 1)

        except Exception as e:
            logging.critical(f"Unhandled exception in main worker loop: {e}", exc_info=True)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Dockerfile / Supervisord Changes

**`requirements.txt`**

Your `requirements.txt` file needs to be updated.

**REMOVE:**
```
mcp-tools-py>=0.4.0
```

**ADD:**
```
websockets>=14.0
```
*(Ensure `redis>=5.0.0` or your current version is also present)*

**`supervisord.conf`**

**No changes are required.** The entry points for the programs remain the same: `python -m src.mcp_server` and `python -m src.worker`. Supervisord will continue to manage them correctly.

This implementation directly resolves the bug by replacing the non-existent library with a robust, standard, and contextually appropriate solution using `websockets`. It maintains all approved requirements and aligns with your existing service patterns.
