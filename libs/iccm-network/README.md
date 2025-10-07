# iccm-network: Standardized MCP Networking Library

**End the nightmare of WebSocket connection debugging.**

This library provides a battle-tested, zero-configuration MCP server implementation that eliminates the recurring networking issues that have wasted 10+ hours across ICCM development.

## Problem Solved

Before `iccm-network`, every ICCM component reimplemented WebSocket MCP servers from scratch, causing:

- ❌ **Connection timeouts** - Components bound to `127.0.0.1` instead of `0.0.0.0`, unreachable from network
- ❌ **Inconsistent behavior** - Some components worked, others timed out, same bugs fixed multiple times
- ❌ **Protocol bugs** - Different JSON-RPC 2.0 implementations with varying error handling
- ❌ **Wasted time** - 10+ hours debugging connection failures, handshake issues, IP vs hostname problems

With `iccm-network`:

- ✅ **Always works from network** - Automatically binds to `0.0.0.0` (never configurable)
- ✅ **Consistent protocol** - Correct JSON-RPC 2.0 implementation (initialize, tools/list, tools/call)
- ✅ **Standardized errors** - `MCPToolError` with proper error codes
- ✅ **Zero configuration** - Just provide tools and handlers, networking is handled

## Installation

### Option 1: Local Development Install (Recommended for ICCM)

```bash
# From component directory (e.g., /mnt/projects/ICCM/horace)
pip install -e /mnt/projects/ICCM/iccm-network
```

### Option 2: PyPI Install (Future)

```bash
pip install iccm-network
```

### Option 3: Docker Requirements

Add to `requirements.txt`:
```
/app/iccm-network
```

Then mount the library in `docker-compose.yml`:
```yaml
volumes:
  - ../iccm-network:/app/iccm-network:ro
```

## Quick Start

```python
import asyncio
from iccm_network import MCPServer, MCPToolError

# 1. Define your tool handlers (async functions)
async def register_file(file_path: str, metadata: dict = None) -> dict:
    """Register a file in the system."""
    if not file_path:
        raise MCPToolError("file_path is required", code=-32602)

    # Your business logic here
    return {
        "status": "registered",
        "file_path": file_path,
        "metadata": metadata or {}
    }

async def search_files(query: str, limit: int = 10) -> dict:
    """Search for files."""
    # Your business logic here
    return {
        "results": [...],
        "count": len(results)
    }

# 2. Define tool schemas (MCP format)
TOOLS = {
    "horace_register_file": {
        "description": "Register a file with metadata",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata"
                }
            },
            "required": ["file_path"]
        }
    },
    "horace_search_files": {
        "description": "Search for files by query",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    }
}

# 3. Map tools to handlers
HANDLERS = {
    "horace_register_file": register_file,
    "horace_search_files": search_files
}

# 4. Create and start server
async def main():
    server = MCPServer(
        name="horace",
        version="1.0.0",
        port=8070,
        tool_definitions=TOOLS,
        tool_handlers=HANDLERS
    )

    await server.start()  # Runs forever

if __name__ == "__main__":
    asyncio.run(main())
```

**That's it.** No WebSocket configuration, no binding logic, no protocol handling. Just tools and handlers.

## API Reference

### `MCPServer`

```python
MCPServer(
    name: str,
    version: str,
    port: int,
    tool_definitions: Dict[str, Any],
    tool_handlers: Dict[str, Callable[..., Awaitable[Any]]],
    logger: Optional[logging.Logger] = None
)
```

**Parameters:**
- `name` - Service name (e.g., "horace", "dewey")
- `version` - Service version (e.g., "1.0.0")
- `port` - Port to listen on (e.g., 8070)
- `tool_definitions` - Dict mapping tool names to MCP tool schemas
- `tool_handlers` - Dict mapping tool names to async handler functions
- `logger` - Optional custom logger (creates default if None)

**Methods:**
- `await server.start()` - Start server and run forever (blocks)
- `await server.stop()` - Gracefully stop server (for testing)

**What it handles for you:**
- ✅ Binds to `0.0.0.0:{port}` (NEVER configurable - this prevents bugs)
- ✅ JSON-RPC 2.0 protocol (initialize, tools/list, tools/call)
- ✅ WebSocket connection lifecycle
- ✅ Error handling and standard responses
- ✅ Logging (connection events, tool calls, errors)

### `MCPToolError`

```python
MCPToolError(message: str, code: int = -32000, data: Any = None)
```

Raise this exception in your tool handlers to return standardized JSON-RPC errors.

**Parameters:**
- `message` - Human-readable error description
- `code` - JSON-RPC error code (default -32000 for server error)
  - `-32700` - Parse error (invalid JSON)
  - `-32600` - Invalid request
  - `-32601` - Method not found
  - `-32602` - Invalid params
  - `-32603` - Internal error
  - `-32000` - Server error (custom)
- `data` - Optional additional error data

**Example:**
```python
async def my_tool(arg: str) -> dict:
    if not arg:
        raise MCPToolError("arg is required", code=-32602)  # Invalid params

    if arg == "forbidden":
        raise MCPToolError("Access denied", code=-32000, data={"reason": "forbidden"})

    return {"result": "success"}
```

## Migration Guide

### Migrating from Custom WebSocket MCP Server

**Before (Custom Implementation):**

```python
# Old: Custom WebSocket server (50-200 lines of boilerplate)
import websockets
import json

class HoraceMCPServer:
    def __init__(self, host, port):
        self.host = host  # BUG: Often set to 127.0.0.1
        self.port = port

    async def handle_client(self, websocket):
        async for message in websocket:
            data = json.loads(message)
            # Custom protocol handling (often incomplete)
            if data["method"] == "initialize":
                # ... custom code
            elif data["method"] == "tools/list":
                # ... custom code
            # ... etc (lots of boilerplate)

    async def start(self):
        await websockets.serve(self.handle_client, self.host, self.port)
        await asyncio.Future()

# In config.py or main.py
config.MCP_HOST = "127.0.0.1"  # BUG: Not reachable from network
server = HoraceMCPServer(config.MCP_HOST, config.MCP_PORT)
await server.start()
```

**After (iccm-network):**

```python
# New: Use iccm-network (5-10 lines)
from iccm_network import MCPServer

server = MCPServer(
    name="horace",
    version="1.0.0",
    port=8070,  # Just the port, host is always 0.0.0.0
    tool_definitions=TOOLS,
    tool_handlers=HANDLERS
)
await server.start()
```

### Step-by-Step Migration (Horace Example)

**1. Install the library:**

Edit `horace/requirements.txt`:
```diff
  asyncpg==0.30.0
  websockets==14.1
+ /app/iccm-network
```

Edit `docker-compose.yml`:
```diff
  volumes:
    - ./horace:/app/horace
+   - ../iccm-network:/app/iccm-network:ro
```

**2. Update your MCP server file:**

Edit `horace/src/mcp_server.py`:

```diff
- import websockets
- import json
+ from iccm_network import MCPServer, MCPToolError

- class HoraceMCPServer:
-     # ... 200 lines of custom WebSocket code
-     pass

+ # Define tools (you probably already have this)
+ TOOLS = {
+     "horace_register_file": {...},
+     "horace_search_files": {...},
+ }
+
+ # Define handlers (extract from your existing code)
+ async def register_file(file_path: str, metadata: dict = None) -> dict:
+     # Your existing business logic
+     return {"status": "registered", ...}
+
+ HANDLERS = {
+     "horace_register_file": register_file,
+     "horace_search_files": search_files,
+ }
```

**3. Update your main entry point:**

Edit `horace/src/__main__.py` or `horace/horace_server.py`:

```diff
- from .mcp_server import HoraceMCPServer
- import config
+ from iccm_network import MCPServer
+ from .mcp_server import TOOLS, HANDLERS

  async def main():
-     server = HoraceMCPServer(config.MCP_HOST, config.MCP_PORT)
+     server = MCPServer(
+         name="horace",
+         version="1.0.0",
+         port=8070,
+         tool_definitions=TOOLS,
+         tool_handlers=HANDLERS
+     )
      await server.start()
```

**4. Remove now-unnecessary configuration:**

Edit `horace/src/config.py`:

```diff
- MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")  # DELETE: No longer needed
  MCP_PORT = int(os.getenv("MCP_PORT", "8070"))   # KEEP: Port still configurable
```

**5. Rebuild and test:**

```bash
docker compose build horace-blue
docker compose up -d horace-blue

# Test from localhost
docker exec horace-blue python -c "
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://localhost:8070') as ws:
        await ws.send(json.dumps({'jsonrpc': '2.0', 'method': 'tools/list', 'id': 1}))
        print(await ws.recv())

asyncio.run(test())
"

# Test from network (this is what matters!)
docker exec dewey-blue python -c "
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://172.29.0.70:8070') as ws:
        await ws.send(json.dumps({'jsonrpc': '2.0', 'method': 'tools/list', 'id': 1}))
        print(await ws.recv())

asyncio.run(test())
"
```

If both tests succeed, add to relay:
```python
# Via MCP tools
relay_add_server(name="horace", url="ws://172.29.0.70:8070")
```

## Design Principles

### 1. **Always Bind to 0.0.0.0**

The #1 cause of connection issues in ICCM was components binding to `127.0.0.1` or `localhost`, which makes them unreachable from other containers.

**Rule:** The library ALWAYS binds to `0.0.0.0`. This is NOT configurable. If you think you need `127.0.0.1`, you're wrong - that's the bug we're eliminating.

```python
# In iccm_network/server.py
self.host = "0.0.0.0"  # CRITICAL: Never configurable
```

### 2. **Standard JSON-RPC 2.0**

All ICCM components use JSON-RPC 2.0 over WebSocket with three methods:
- `initialize` - Handshake and capability exchange
- `tools/list` - Return available tools
- `tools/call` - Execute a tool

The library handles this protocol correctly so you don't have to.

### 3. **Zero Configuration**

Components should "just work" without configuration. The only parameter that varies is the port.

**Good:**
```python
server = MCPServer(name="horace", version="1.0.0", port=8070, ...)
```

**Bad (what we're avoiding):**
```python
server = CustomServer(
    host=config.HOST,  # Bug waiting to happen
    port=config.PORT,
    protocol_version=config.VERSION,  # Unnecessary
    timeout=config.TIMEOUT,  # Over-configuration
    ...
)
```

### 4. **Relay Compatibility**

The MCP relay works perfectly and will NOT change. This library is designed to work seamlessly with the existing relay implementation.

**Relay connection pattern (reference only):**
```python
# The relay connects like this:
backend_ws = await websockets.connect(f"ws://{container_ip}:{port}")
```

This library ensures components are always reachable at their container IP.

## Troubleshooting

### "Connection refused" or timeout from network

**Symptom:**
```bash
# Works:
docker exec horace-blue python -c "websockets.connect('ws://localhost:8070')"

# Fails:
docker exec dewey-blue python -c "websockets.connect('ws://172.29.0.70:8070')"
```

**Solution:**
You're not using `iccm-network` correctly, or your container isn't rebuilding. Ensure:

1. Library is installed: `pip list | grep iccm-network`
2. Server uses `MCPServer`: Check your code imports `from iccm_network import MCPServer`
3. Container rebuilt: `docker compose build --no-cache horace-blue`
4. No host configuration: Don't pass `host` parameter anywhere

### Tool not appearing in tools/list

**Symptom:**
Tool defined in `TOOLS` but not showing when calling `tools/list`.

**Solution:**
1. Check `tool_definitions` and `tool_handlers` have matching keys
2. Rebuild container (without cache): `docker compose build --no-cache`
3. Check server logs for errors during startup

### MCPToolError not working

**Symptom:**
Raising `MCPToolError` but getting generic error instead.

**Solution:**
Make sure you're importing from the library:
```python
from iccm_network import MCPToolError  # Correct

# NOT:
from some_custom_module import MCPToolError  # Wrong
```

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (when available)
pytest tests/

# Manual testing
python -m iccm_network.examples.simple_server  # TODO: Add examples
```

## Components Using This Library

| Component | Status | Version | Notes |
|-----------|--------|---------|-------|
| **Horace** | ✅ **DEPLOYED** | 1.0.0 | Successfully deployed, all 7 tools working via relay |
| Dewey | ⏳ Planned | - | Migration after Horace validation |
| Fiedler | ⏳ Planned | - | HTTP proxy integration maintained |
| Godot | ⏳ Planned | - | Logging service migration |
| Playfair | ⏳ Planned | - | Diagram generation service |
| Gates | ⏳ Planned | - | Document generation service |
| Marco | ⏳ Planned | - | Browser automation service |

**Status as of 2025-10-06:**
- ✅ Library created and tested
- ✅ Horace Blue deployed using iccm-network v1.1.0
- ✅ All 7 Horace tools accessible via MCP Relay
- ✅ Network connectivity verified (works from localhost AND network)
- ⏸️ Other component migrations pending

## Architecture

### Component View

```
┌─────────────────┐
│  Claude Code    │
│  (MCP Client)   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│   MCP Relay     │  ← Never changes, works perfectly
│  (Port 8000)    │
└────────┬────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         v                                     v
┌─────────────────┐                  ┌─────────────────┐
│ Dewey           │                  │ Horace          │
│ (iccm-network)  │                  │ (iccm-network)  │
│ Port 9050       │                  │ Port 8070       │
└─────────────────┘                  └─────────────────┘
    Binds to 0.0.0.0                     Binds to 0.0.0.0
    (Network reachable)                  (Network reachable)
```

### Call Flow

```
1. Claude Code → Relay: JSON-RPC request
2. Relay → Component (e.g., Horace): Forward request
3. Component: iccm-network handles protocol
4. Component: Routes to tool handler
5. Tool handler: Executes business logic
6. Component: iccm-network formats response
7. Relay → Claude Code: Forward response
```

## Why This Library Exists

From GitHub Issue #11:

> "**10+ hours wasted** debugging connection timeouts, handshake failures, IP vs hostname issues"
>
> "Each component reimplements networking from scratch causing inconsistent behavior"
>
> "Same bugs fixed multiple times across components"

This library consolidates all the lessons learned from:
- ✅ Dewey (most reliable implementation)
- ✅ Fiedler (HTTP proxy integration patterns)
- ✅ Gemini-2.5-pro's root cause analysis (bind to 0.0.0.0)
- ✅ Relay stability (proven over dozens of tool discoveries)

**Goal:** Make networking invisible and bulletproof. Components focus on business logic, not WebSockets.

## Contributing

See the main [ICCM repository](https://github.com/rmdevpro/ICCM) for contribution guidelines.

**When reporting issues:**
1. Component name and version
2. Docker network configuration
3. Test results from localhost AND network
4. Relevant logs from component and relay

## License

MIT License - See LICENSE file for details.

## Support

- **GitHub Issues:** https://github.com/rmdevpro/ICCM/issues
- **Documentation:** https://github.com/rmdevpro/ICCM/tree/main/iccm-network
- **ICCM Architecture:** `/mnt/projects/ICCM/architecture/`

---

**Made with 🔧 by the ICCM Project**

*Solving WebSocket hell once and for all.*
