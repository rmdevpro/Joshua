# joshua-libs

**Standardized networking and logging libraries for Joshua MAD components**

Version: 1.0.0

## Overview

`joshua-libs` is a unified Python package that provides two essential libraries for all Joshua MAD (Modular Autonomous Daemon) components:

- **`joshua_network`**: WebSocket-based MCP (Model Context Protocol) server/client implementation
- **`joshua_logger`**: Centralized logging to Godot MCP service

Both libraries are installed together as a single package to ensure consistency across all MAD deployments.

## Installation

### For MAD Dockerfiles

All MADs should install joshua-libs during their Docker build process:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install joshua-libs (both joshua_network and joshua_logger)
COPY --chown=root:root lib/joshua_network /tmp/joshua-libs-install/joshua_network
COPY --chown=root:root lib/joshua_logger /tmp/joshua-libs-install/joshua_logger
COPY --chown=root:root lib/pyproject.toml /tmp/joshua-libs-install/
RUN pip install --no-cache-dir /tmp/joshua-libs-install && rm -rf /tmp/joshua-libs-install

# Install your MAD's specific dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .
```

**Important**: The Docker `build.context` in `docker-compose.yml` must be set to the Joshua project root (`../..` from `mads/<mad-name>/`) so the `lib/` directory is accessible.

Example `docker-compose.yml`:
```yaml
services:
  my-mad:
    build:
      context: ../..  # Joshua project root
      dockerfile: mads/my-mad/Dockerfile
```

### For Development/Testing

```bash
cd /mnt/projects/Joshua/lib
pip install -e .
```

## Quick Start

### MCP Server Example

```python
import asyncio
from joshua_network import Server
from joshua_logger import Logger

# Initialize logger
logger = Logger()

# Define tool handlers
async def hello_world(**arguments):
    name = arguments.get('name', 'World')
    await logger.log('INFO', f'hello_world called with name={name}', 'my-mad')
    return {
        "content": [{
            "type": "text",
            "text": f"Hello, {name}!"
        }]
    }

# Tool definitions (MCP protocol format)
TOOL_DEFINITIONS = {
    "hello_world": {
        "description": "Say hello to someone",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name to greet"}
            }
        }
    }
}

# Create handlers
TOOL_HANDLERS = {
    "hello_world": hello_world
}

async def main():
    await logger.log('INFO', 'Starting MCP server', 'my-mad')

    server = Server(
        name="my-mad-server",
        version="1.0.0",
        port=9030,
        tool_definitions=TOOL_DEFINITIONS,
        tool_handlers=TOOL_HANDLERS
    )

    await server.start()
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
```

### MCP Client Example

```python
from joshua_network import Client

async def call_remote_tool():
    client = Client(url="ws://localhost:9030")

    try:
        result = await client.call_tool("hello_world", {"name": "Joshua"})
        print(result)
    finally:
        await client.disconnect()
```

## Library Documentation

### joshua_network

WebSocket-based MCP protocol implementation with:
- **Server**: Host MCP tools for other components to call
- **Client**: Call tools on remote MCP servers
- Auto-reconnection and connection pooling
- Health check endpoint (`/healthz`)
- Full MCP 2024-11-05 protocol compliance

**Key Classes:**
- `Server(name, version, port, tool_definitions, tool_handlers, logger=None)`
- `Client(url, timeout=30.0, logger=None)`

**Environment Variables:**
- None required (configured via constructor arguments)

### joshua_logger

Centralized logging with:
- Fire-and-forget async logging (never blocks application)
- Structured metadata support
- Trace ID correlation
- Silent failure (logging errors never crash your app)

**Usage:**
```python
from joshua_logger import Logger

logger = Logger()

# Basic log
await logger.log("INFO", "Application started", "my-component")

# With metadata
await logger.log(
    "ERROR",
    "Database connection failed",
    "my-component",
    data={"host": "localhost", "port": 5432}
)

# With trace ID
await logger.log(
    "DEBUG",
    "Processing request",
    "my-component",
    data={"request_id": "123"},
    trace_id="trace-abc-123"
)
```

**Environment Variables:**
- `GODOT_URL` or `JOSHUA_LOGGER_URL`: WebSocket URL (default: `ws://godot-mcp:9060`)
- `JOSHUA_LOGGER_TIMEOUT`: Request timeout in seconds (default: `2.0`)

**Log Levels:**
- `TRACE`: Detailed debugging information
- `DEBUG`: Debug-level messages
- `INFO`: Informational messages
- `WARN`: Warning messages
- `ERROR`: Error messages

## Docker Networking

All MADs run in Docker and communicate via the `iccm_network`:

```yaml
services:
  my-mad:
    networks:
      - iccm_network
    environment:
      - GODOT_URL=ws://godot-mcp:9060  # Logger endpoint
      - LOGGING_ENABLED=true

networks:
  iccm_network:
    external: true
```

The default `ws://godot-mcp:9060` assumes Godot is running as `godot-mcp` on the same Docker network.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Your MAD                           │
│  ┌──────────────┐              ┌──────────────┐        │
│  │ joshua_network│              │ joshua_logger│        │
│  │   Server      │              │              │        │
│  └──────┬────────┘              └──────┬───────┘        │
│         │                               │                │
└─────────┼───────────────────────────────┼────────────────┘
          │                               │
          │ MCP Protocol                  │ Logging
          │ (WebSocket)                   │ (WebSocket)
          │                               │
          ▼                               ▼
  ┌───────────────┐             ┌──────────────────┐
  │  MCP Relay    │             │  Godot MCP       │
  │  (Port 8765)  │             │  (Port 9060)     │
  └───────────────┘             └──────────────────┘
          │                               │
          │                               ▼
          │                      ┌──────────────────┐
          │                      │  Dewey MCP       │
          │                      │  (Logs → DB)     │
          │                      └──────────────────┘
          ▼
  ┌───────────────┐
  │  Claude Code  │
  │  (LLM Client) │
  └───────────────┘
```

## Common Patterns

### Pattern 1: Tool Handler with Logging

```python
async def my_tool(**arguments):
    """Tool handler with proper logging and error handling."""
    await logger.log('TRACE', 'Tool called', 'my-mad', data={'arguments': arguments})

    try:
        # Your tool logic here
        result = await do_something(arguments)

        await logger.log('TRACE', 'Tool completed', 'my-mad', data={'success': True})

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    except Exception as e:
        await logger.log('ERROR', f'Tool failed: {str(e)}', 'my-mad',
                        data={'error': str(e), 'type': type(e).__name__})
        raise
```

### Pattern 2: Factory Function for Tool Handlers

When you need to create multiple similar handlers (e.g., from a loop), use a factory function to avoid closure issues:

```python
def make_handler(tool_name):
    async def handler(**args):
        return await wrap_tool_handler(tool_name, **args)
    return handler

TOOL_HANDLERS = {
    tool_name: make_handler(tool_name)
    for tool_name in TOOL_DEFINITIONS.keys()
}
```

### Pattern 3: Server with Cleanup

```python
async def main():
    await db_pool.initialize()

    server = Server(
        name="my-mad",
        version="1.0.0",
        port=9030,
        tool_definitions=TOOL_DEFINITIONS,
        tool_handlers=TOOL_HANDLERS
    )

    await server.start()

    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await server.stop()
        await db_pool.close()
```

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'joshua_network'`

**Solution**: Ensure joshua-libs is installed via pip in your Dockerfile:
```dockerfile
RUN pip install --no-cache-dir /tmp/joshua-libs-install
```

### Connection Errors

**Problem**: Logger shows connection refused errors

**Solution**:
1. Verify `GODOT_URL` environment variable is correct
2. Ensure both containers are on the same Docker network
3. Check Godot container is running: `docker ps | grep godot`

### Tool Discovery Failures

**Problem**: MCP Relay shows 0 tools for your MAD

**Solution**:
1. Check container logs: `docker logs <mad-name>-mcp`
2. Verify joshua_network.Server is being used (not custom implementation)
3. Ensure `tool_definitions` and `tool_handlers` are properly defined
4. Restart relay connection: Use `mcp__iccm__relay_reconnect_server`

### Silent Logging Failures

**Problem**: Logs not appearing in Godot but no errors shown

**Solution**: joshua_logger fails silently by design. Check:
1. Godot container health: `docker ps`
2. Network connectivity between containers
3. Godot logs for backend errors

## Migration Guide

### From Custom MCP Server → joshua_network.Server

**Before**:
```python
# Custom WebSocket server implementation
class MyMCPServer:
    async def handle_request(self, message):
        # Custom protocol handling
        pass
```

**After**:
```python
# Use joshua_network.Server
from joshua_network import Server

server = Server(
    name="my-server",
    version="1.0.0",
    port=9030,
    tool_definitions=TOOL_DEFINITIONS,
    tool_handlers=TOOL_HANDLERS
)
await server.start()
```

### From Custom Logger → joshua_logger

**Before**:
```python
# Custom logging implementation
await custom_logger.log("INFO", "Message", "component", {"data": "value"})
```

**After**:
```python
# Use joshua_logger with keyword arguments
from joshua_logger import Logger

logger = Logger()
await logger.log("INFO", "Message", "component", data={"data": "value"})
```

**⚠️ CRITICAL**: Always use keyword arguments for `data` and `trace_id` parameters!

## Testing

Run the test suite:
```bash
cd /mnt/projects/Joshua/lib
pytest --cov=joshua_network --cov=joshua_logger tests/
```

Test your MAD deployment:
```bash
# 1. Check health endpoint
curl http://localhost:<your-port>/healthz

# 2. Check relay status
# Use mcp__iccm__relay_get_status tool

# 3. Check logs in Godot
# Use mcp__iccm__godot_logger_query tool
```

## Version History

### v1.0.0 (2025-10-10)
- Combined joshua_network and joshua_logger into single package
- Full MCP 2024-11-05 protocol compliance
- Auto-reconnection for both server and client
- Silent failure logging design
- Comprehensive error handling

## License

Internal Joshua Project component - not for external distribution.

## Support

- **Documentation**: `/mnt/projects/Joshua/lib/`
- **Issues**: GitHub Issues in Joshua repository
- **Examples**: See `mads/*/mcp_server.py` for real-world implementations
