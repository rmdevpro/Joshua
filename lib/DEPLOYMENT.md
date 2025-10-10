# Joshua Libraries Deployment Guide

This guide provides comprehensive instructions for deploying, configuring, and using the standardized `joshua_network` and `joshua_logger` libraries.

## 1. Prerequisites

- **Python:** Python 3.10 or newer.
- **System Dependencies:** No special system dependencies are required beyond a standard Linux environment (Ubuntu 24.04 is the target).
- **Docker:** A working Docker installation is required for containerized deployment, which is the standard for Joshua projects. Ensure Docker and Docker Compose are installed.

## 2. Installation

### Step-by-Step Library Installation

The libraries are intended to be used directly from the project's monorepo structure.

1.  **Clone the Repository:**
    Ensure you have the latest version of the `/mnt/projects/Joshua/` repository.

2.  **Set `PYTHONPATH`:**
    To make the libraries importable by your application, add the `lib` directory to your `PYTHONPATH`.

    ```bash
    export PYTHONPATH="/mnt/projects/Joshua/lib:$PYTHONPATH"
    ```
    For Docker deployments, this is handled by setting `ENV PYTHONPATH` in the `Dockerfile`.

3.  **Install Dependencies:**
    The libraries require `websockets`. Install it using pip.

    ```bash
    # From your project's root directory
    pip install websockets>=12.0
    ```

4.  **Verify Installation:**
    Run a simple Python command to ensure the modules are discoverable.

    ```bash
    python -c "from joshua_network.server import Server; from joshua_logger import logger; print('Joshua libraries imported successfully!')"
    # Expected output: Joshua libraries imported successfully!
    ```

## 3. Configuration

Configuration is primarily managed through environment variables and constructor arguments, which is ideal for containerized environments.

### Network Library Configuration (`joshua_network`)

The `joshua_network.Server` class is configured at instantiation time.

-   **Port Selection:** The `port` is passed as an argument to the `Server` constructor. It is recommended to make this configurable via an environment variable in your application.
-   **Tool Handlers:** A dictionary mapping tool names to handler functions must be passed to the `Server` constructor.

**Example:**

```python
import os
import asyncio
from joshua_network.server import Server

# Load port from environment variable, default to 9000
APP_PORT = int(os.environ.get("APP_PORT", 9000))

async def my_tool_handler(args):
    return {"message": f"Hello, {args['name']}"}

tool_handlers = {
    "say_hello": my_tool_handler
}

server = Server(port=APP_PORT, tool_handlers=tool_handlers)
# await server.start()
```

### Logging Library Configuration (`joshua_logger`)

The `joshua_logger` is configured entirely through environment variables. The default logger instance reads these upon first use.

-   **`JOSHUA_LOGGER_URL`**
    -   **Description:** The WebSocket URL of the Godot MCP logging service.
    -   **Default:** `ws://godot-mcp:9060`
    -   **Example:** `JOSHUA_LOGGER_URL=ws://godot.joshua.local:9060`

-   **`JOSHUA_LOGGER_TIMEOUT`**
    -   **Description:** The timeout in seconds for sending a log message.
    -   **Default:** `2.0`
    -   **Example:** `JOSHUA_LOGGER_TIMEOUT=5.0`

#### Docker Networking Considerations

When running your service and the Godot logger in Docker containers, use Docker's internal DNS names. The default `ws://godot-mcp:9060` assumes your Godot service is named `godot-mcp` within the same Docker network.

## 4. Migration from Old Libraries

This section provides before-and-after examples for migrating from legacy libraries.

### From `iccm_network` to `joshua_network`

The new library simplifies server setup and standardizes the API.

**Before (`iccm_network.MCPServer`):**

```python
# old_service.py
from iccm_network import MCPServer

class MyOldServer(MCPServer):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.register_tool("old_tool", self.handle_old_tool)

    async def handle_old_tool(self, args):
        return {"result": "ok"}

server = MyOldServer("0.0.0.0", 8080)
server.run()
```

**After (`joshua_network.Server`):**

```python
# new_service.py
import asyncio
from joshua_network.server import Server

# Handlers are now simple async functions
async def handle_old_tool(args):
    return {"result": "ok"}

# Tool registration is done at instantiation
tool_handlers = { "old_tool": handle_old_tool }

async def main():
    server = Server(port=8080, tool_handlers=tool_handlers)
    await server.start()
    await asyncio.Event().wait() # Keep server running

if __name__ == "__main__":
    asyncio.run(main())
```

### From `godot/mcp_logger` to `joshua_logger`

The new logger removes configuration from the call site and relies on a shared, pre-configured instance.

**Before (`godot.mcp_logger`):**

```python
# old_component.py
from godot.mcp_logger import GodotLogger

GODOT_URL = "ws://godot-mcp:9060"

async def do_something():
    logger = GodotLogger(godot_url=GODOT_URL)
    await logger.log(
        level="INFO",
        message="Something happened",
        component="old_component",
        data={"user_id": 123}
    )
```

**After (`joshua_logger`):**

```python
# new_component.py
from joshua_logger import logger # Import the default instance

# Configuration is now handled by environment variables.
# Set JOSHUA_LOGGER_URL="ws://godot-mcp:9060" in your environment.

async def do_something():
    # No instantiation or URL needed at call site.
    await logger.log(
        level="INFO",
        message="Something happened",
        component="new_component",
        data={"user_id": 123}
    )
```

## 5. Testing the Deployment

### How to Run the Test Suite

A comprehensive test suite is provided to verify the libraries' functionality.

1.  Navigate to the `lib` directory:
    ```bash
    cd /mnt/projects/Joshua/lib
    ```

2.  Install test dependencies:
    ```bash
    pip install -r tests/requirements-test.txt
    ```

3.  Run pytest with coverage:
    ```bash
    pytest --cov=joshua_network --cov=joshua_logger tests/
    ```
A successful run will show all tests passing and a coverage report meeting or exceeding 80%.

### Verifying in Production

1.  **Check Health Endpoint:** For any service using `joshua_network.Server`, access its `/healthz` endpoint.
    ```bash
    curl http://<your-service-ip>:<port>/healthz
    ```
    You should receive an `OK` response with a 200 status code.

2.  **Check Logs:** Trigger an action in your service that should generate a log message. Verify that the log appears in the Godot UI as expected.

## 6. Integration Examples

### Example 1: Simple MCP Server
A complete, runnable server exposing one tool.

```python
# simple_server.py
import asyncio
import os
from joshua_network.server import Server
from joshua_logger import logger

async def get_system_status(arguments: dict):
    """A simple tool that returns a status message and logs the call."""
    await logger.log("INFO", "get_system_status tool was called", "simple_server", arguments)
    return {"status": "All systems nominal", "request_args": arguments}

async def main():
    port = int(os.environ.get("PORT", 9001))
    server = Server(port=port, tool_handlers={"get_system_status": get_system_status})
    print(f"Starting server on port {port}...")
    await server.start()
    await asyncio.Event().wait() # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server shutting down.")
```

### Example 2: MCP Client
A script that connects to the server from Example 1 and calls its tool.

```python
# simple_client.py
import asyncio
from joshua_network.client import Client

async def main():
    server_url = "ws://localhost:9001"
    client = Client(url=server_url)

    try:
        print(f"Calling 'get_system_status' on {server_url}...")
        result = await client.call_tool("get_system_status", {"user": "joshua"})
        print("Response received:", result)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Logging from a Service
This shows how easily `joshua_logger` can be added to any async application.

```python
# logging_service.py
import asyncio
from joshua_logger import logger

async def process_data(data_id):
    await logger.log("INFO", f"Starting processing for data ID: {data_id}", "data_processor")
    try:
        await asyncio.sleep(0.5) # Simulate work
        if data_id % 3 == 0:
            raise ValueError("Simulated processing error")
        await logger.log("INFO", f"Successfully processed data ID: {data_id}", "data_processor")
    except Exception as e:
        await logger.log("ERROR", f"Failed to process data ID: {data_id}", "data_processor", data={"error": str(e)})

async def main():
    tasks = [process_data(i) for i in range(5)]
    await asyncio.gather(*tasks)
    await logger.close() # Gracefully close connection on shutdown

if __name__ == "__main__":
    # Ensure JOSHUA_LOGGER_URL is set in your environment!
    # export JOSHUA_LOGGER_URL=ws://localhost:9060
    asyncio.run(main())
```

### Example 4: Full MAD Integration (Docker Compose)
This example shows a `docker-compose.yml` for a typical MAD (Modular Autonomous Daemon) that uses both libraries.

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  my-mad-service:
    build:
      context: .
      dockerfile: Dockerfile.mad
    container_name: my-mad-service
    ports:
      - "9001:9001" # Expose the MCP server port
    environment:
      # Configure the logger to talk to the Godot service on the docker network
      - JOSHUA_LOGGER_URL=ws://godot-mcp:9060
      - JOSHUA_LOGGER_TIMEOUT=3.0
      # Application-specific config
      - PORT=9001
      # Set pythonpath to find libs
      - PYTHONPATH=/app/lib
    networks:
      - joshua-net

  godot-mcp:
    image: joshua/godot-mcp:latest # Fictional Godot logger image
    container_name: godot-mcp
    ports:
      - "9060:9060" # Expose the logger port
    networks:
      - joshua-net

networks:
  joshua-net:
    driver: bridge
```

**`Dockerfile.mad` for `my-mad-service`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Set PYTHONPATH to include the libraries
ENV PYTHONPATH="/app/lib:${PYTHONPATH}"

# Copy application code and libraries
# Assumes your service code and the 'lib' directory are in the build context
COPY ./my_mad_service.py /app/
COPY ./lib /app/lib

# Install dependencies
RUN pip install --no-cache-dir websockets>=12.0

# Command to run the service
CMD ["python", "my_mad_service.py"]
```

## 7. Production Checklist

- [ ] Libraries are available via `PYTHONPATH` in the production environment.
- [ ] All pip dependencies are installed.
- [ ] `JOSHUA_LOGGER_URL` environment variable is set correctly for the environment.
- [ ] `JOSHUA_LOGGER_TIMEOUT` is set if a non-default value is needed.
- [ ] Network connectivity (e.g., Docker network, firewall rules) allows the service to reach the Godot MCP URL.
- [ ] The service's own MCP port is exposed and accessible by clients.
- [ ] The full test suite passes before deployment.
- [ ] The `/healthz` endpoint on the deployed service is responding with `OK`.
- [ ] Test logs sent from the deployed service appear correctly in the Godot UI.

## 8. Troubleshooting

-   **Issue: `ImportError: No module named joshua_network`**
    -   **Solution:** The `PYTHONPATH` is not set correctly. Ensure the `lib` directory is in your `PYTHONPATH`. In Docker, verify the `ENV PYTHONPATH` and `WORKDIR` commands.

-   **Issue: Connection refused errors when logging.**
    -   **Solution:** This means the logger cannot reach the `JOSHUA_LOGGER_URL`.
        1.  Verify the `JOSHUA_LOGGER_URL` is correct.
        2.  If using Docker, ensure both your service and the Godot service are on the same Docker network and use the correct service name (e.g., `godot-mcp`).
        3.  Check for firewall rules blocking the connection.

-   **Issue: Logs do not appear in Godot, but no errors are shown.**
    -   **Solution:** The `joshua_logger` is designed to fail silently. The connection issue is likely still present. Follow the "Connection refused" steps. Check the service's own logs for any warnings from the logger itself.

-   **Issue: Client tool calls time out.**
    -   **Solution:**
        1.  Check for high load or long-running tasks on the server.
        2.  Verify network latency between the client and server.
        3.  Increase the `timeout` parameter when creating the `joshua_network.Client` instance if longer-running tools are expected.
