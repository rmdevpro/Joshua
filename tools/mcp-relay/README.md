# MCP Relay V3.7

**stdio-to-WebSocket multiplexer for Claude Code**

The MCP Relay is the central nervous system of the Joshua project - it connects Claude Code to all MAD (Multipurpose Agentic Duo) services, aggregates their tools, and intelligently routes tool calls to the appropriate backend.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Relay Management Tools](#relay-management-tools)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Version History](#version-history)

---

## Overview

### What is the MCP Relay?

The MCP Relay implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to bridge Claude Code's stdio interface with multiple WebSocket-based backend services.

**Key Capabilities:**
- **Protocol Translation**: stdio (Claude Code) ↔ WebSocket (MAD backends)
- **Tool Aggregation**: Combines tools from all backends into a unified interface
- **Intelligent Routing**: Routes tool calls to the correct backend
- **Connection Management**: Automatic reconnection, health monitoring, graceful degradation
- **Dynamic Configuration**: Hot-reload backends without restarting Claude Code

### Why Does Joshua Need It?

Joshua uses a **microservices architecture** where each MAD provides specialized capabilities:
- **Dewey**: Conversation storage & retrieval
- **Fiedler**: LLM orchestration
- **Godot**: Centralized logging
- **Horace**: File management & versioning
- **Marco**: Browser automation (Playwright)
- **Playfair**: Diagram generation
- **Gates**: Document creation
- **Sergey**: Google Workspace integration

Without the relay, Claude Code would need to:
1. Manage separate connections to 8+ services
2. Know which service provides which tool
3. Handle connection failures individually
4. Restart when configuration changes

The relay **abstracts all of this complexity** into a single stdio interface.

---

## Architecture

###

 System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Claude Code (MCP Client)                    │
│                                                                      │
│  Uses tools via stdio: fiedler_send, dewey_search, marco_navigate  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ stdio (JSON-RPC 2.0)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          MCP Relay (This Service)                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Tool Aggregation Layer                                        │  │
│  │ - relay_get_status (5 management tools)                       │  │
│  │ - fiedler_send, fiedler_list_models (from Fiedler)           │  │
│  │ - dewey_search, dewey_get_conversation (from Dewey)           │  │
│  │ - marco_navigate, marco_click (from Marco)                    │  │
│  │ - ... (90+ tools total from all backends)                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Routing Engine                                                │  │
│  │ - tool_routing: {"fiedler_send": "fiedler", ...}            │  │
│  │ - Connection pool: {backend_name: ws_connection}             │  │
│  │ - Health monitoring: healthy/degraded/failed                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Resilience Layer                                              │  │
│  │ - Auto-reconnect with exponential backoff                     │  │
│  │ - Keep-alive pings (30s interval)                             │  │
│  │ - Graceful degradation (continue if backend fails)            │  │
│  │ - Tool validation (schema + naming conflict detection)        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────┬────────────────────────┬─┘
                     │ WebSocket           │ WebSocket              │ WebSocket
                     ▼                     ▼                        ▼
          ┌──────────────────┐  ┌──────────────────┐    ┌──────────────────┐
          │ Fiedler MCP      │  │ Dewey MCP        │    │ Marco MCP        │
          │ ws://localhost:  │  │ ws://localhost:  │    │ ws://localhost:  │
          │ 9010             │  │ 9022             │    │ 9031             │
          │                  │  │                  │    │                  │
          │ 8 tools          │  │ 7 tools          │    │ 21 tools         │
          └──────────────────┘  └──────────────────┘    └──────────────────┘
                                 ... (5 more backends)
```

### Data Flow

**1. Tool Discovery (Initialization)**
```
Claude Code → stdio → Relay
                       ↓
            Relay.initialize()
                       ↓
         Connect to all backends (parallel)
                       ↓
         For each backend:
           - WebSocket connect
           - MCP initialize handshake
           - tools/list request
           - Validate tool schemas
           - Build routing table
                       ↓
         Aggregate all tools
                       ↓
Claude Code ← stdio ← Relay (returns 90+ tools)
```

**2. Tool Call Execution**
```
Claude Code → stdio → Relay.call_tool("fiedler_send", {...})
                       ↓
         Look up routing: fiedler_send → fiedler backend
                       ↓
         Check connection (reconnect if needed)
                       ↓
         WebSocket → Fiedler MCP.tools/call(...)
                       ↓
Claude Code ← stdio ← Relay ← WebSocket ← Fiedler (result)
```

**3. Dynamic Reconfiguration**
```
backends.yaml modified
         ↓
File watcher detects change
         ↓
Relay.reload_config()
         ↓
Compare old vs new backends
         ↓
- Close removed backends
- Reconnect changed backends
- Add new backends
         ↓
Send notifications/tools/list_changed to Claude
         ↓
Claude refreshes tool list automatically
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Running MAD containers (dewey-mcp, fiedler-mcp, etc.)
- `backends.yaml` configuration file

### Installation

```bash
cd /home/aristotle9/mcp-relay

# Create virtual environment
python3 -m venv .venv

# Install dependencies
.venv/bin/pip install websockets pyyaml watchdog

# Add joshua_logger (assumes /mnt/projects/Joshua/lib is available)
.venv/bin/pip install -e /mnt/projects/Joshua/lib
```

### Configuration

Create or verify `backends.yaml`:

```yaml
# MCP Relay Backend Configuration
backends:
  - name: fiedler
    url: ws://localhost:9010
  - name: dewey
    url: ws://localhost:9022
  - name: godot
    url: ws://localhost:9060
  # ... more backends
```

### Running

**Option 1: Direct Execution**
```bash
.venv/bin/python mcp_relay.py
```

**Option 2: Claude Code Integration**

Add to Claude Code MCP configuration:
```json
{
  "mcpServers": {
    "iccm": {
      "command": "/home/aristotle9/mcp-relay/.venv/bin/python",
      "args": ["/home/aristotle9/mcp-relay/mcp_relay.py"]
    }
  }
}
```

### Verify It's Working

Once running, the relay logs will show:
```
2025-10-10 12:00:00 - INFO - Loaded 8 backends: ['dewey', 'fiedler', 'godot', ...]
2025-10-10 12:00:01 - INFO - Connected to 8/8 backends
2025-10-10 12:00:01 - INFO - ✅ fiedler: healthy (8 tools)
2025-10-10 12:00:01 - INFO - ✅ dewey: healthy (7 tools)
...
2025-10-10 12:00:02 - INFO - MCP Relay ready
```

In Claude Code, check available tools:
```
Use relay_get_status to see all backends and their health
```

---

## Configuration

### backends.yaml Format

```yaml
# MCP Relay Backend Configuration
# This file is auto-updated by relay management tools

backends:
  - name: backend_name     # Unique identifier
    url: ws://host:port    # WebSocket URL
```

**Important:**
- **name** must be unique across all backends
- **url** must be a valid WebSocket URL (ws:// or wss://)
- File is watched - changes trigger automatic reload
- **DO NOT manually edit while relay is running** (use relay tools instead)

### Environment Variables

```bash
# Optional: Custom config file path
python mcp_relay.py --config /path/to/backends.yaml

# Joshua Logger URL (auto-detected from /mnt/projects/Joshua/lib)
export JOSHUA_LOGGER_URL=ws://godot-mcp:9060
```

### File Locations

```
/home/aristotle9/mcp-relay/
├── mcp_relay.py           # Main relay server
├── backends.yaml          # Backend configuration (DO NOT EDIT)
├── .venv/                 # Python virtual environment
├── README.md             # This file
└── BUG8_RESILIENCE_FIX.md # Historical bug fix documentation
```

---

## Relay Management Tools

The relay provides 5 built-in tools for runtime management:

### 1. `relay_get_status`

**Description:** Get detailed status of all MCP servers

**Parameters:** None

**Returns:**
```json
{
  "total_servers": 8,
  "connected_servers": 7,
  "servers": [
    {
      "name": "fiedler",
      "url": "ws://localhost:9010",
      "connected": true,
      "health": "healthy",
      "tools": 8,
      "tool_names": ["fiedler_send", "fiedler_list_models", ...]
    },
    {
      "name": "marco",
      "url": "ws://localhost:9031",
      "connected": true,
      "health": "degraded",
      "tools": 21,
      "error": "Invalid response structure"
    }
  ]
}
```

**Health States:**
- **healthy**: Connected, all tools valid
- **degraded**: Connected, but some tools invalid or errors present
- **failed**: Connection failed
- **unknown**: Not yet attempted

**Example:**
```
Use relay_get_status

Result shows:
- 7/8 backends connected
- Marco is degraded (connection issue)
- 85 tools available total
```

---

### 2. `relay_reconnect_server`

**Description:** Force reconnect to a specific MCP server

**Parameters:**
```json
{
  "name": "backend_name"  // Required: name of backend to reconnect
}
```

**Returns:**
```
✅ Server 'marco' reconnected.
Valid Tools: 21
Health: healthy
```

**When to Use:**
- Backend shows as degraded/failed in status
- After restarting a backend container
- To refresh tool list after backend update

**Example:**
```
Use relay_reconnect_server with:
  name: "marco"

Result:
- Closes existing connection
- Re-establishes WebSocket
- Re-discovers tools
- Updates routing table
```

---

### 3. `relay_add_server`

**Description:** Add a new MCP server to the relay at runtime

**Parameters:**
```json
{
  "name": "new_backend",              // Required: unique name
  "url": "ws://localhost:9999"        // Required: WebSocket URL
}
```

**Returns:**
```
✅ Server 'new_backend' added and connected
URL: ws://localhost:9999
Tools discovered: 5
Health: healthy

💾 Configuration saved.
```

**Important:**
- Automatically saves to backends.yaml
- Triggers tool list refresh in Claude Code
- Connection is attempted immediately

**Example:**
```
Use relay_add_server with:
  name: "new_service"
  url: "ws://localhost:9100"

Result:
- Backend added to configuration
- Connection established
- Tools discovered and added to routing
- backends.yaml updated automatically
```

---

### 4. `relay_remove_server`

**Description:** Remove an MCP server from the relay

**Parameters:**
```json
{
  "name": "backend_name"  // Required: name of backend to remove
}
```

**Returns:**
```
✅ Server 'old_backend' removed.

💾 Configuration saved.
```

**Important:**
- Closes WebSocket connection
- Removes all tools from routing table
- Updates backends.yaml automatically
- Claude Code's tool list refreshes

**Example:**
```
Use relay_remove_server with:
  name: "deprecated_service"

Result:
- Connection closed
- Tools removed from Claude Code
- Configuration updated
```

---

### 5. `relay_list_servers`

**Description:** List all MCP servers with summary information

**Parameters:** None

**Returns:**
```
**MCP Relay - Connected Servers:**

- **fiedler**: ✅ Connected (healthy)
  - URL: ws://localhost:9010
  - Valid Tools: 8

- **marco**: ⚠️ Connected (degraded)
  - URL: ws://localhost:9031
  - Valid Tools: 21
  - Invalid Tools: 0
  - Error: Method 'notifications/initialized' is not supported

- **gates**: ❌ Disconnected (failed)
  - URL: ws://localhost:9050
  - Valid Tools: 0
  - Error: Connection refused
```

**Example:**
```
Use relay_list_servers

Quick overview of all backends:
- Which are connected/disconnected
- Health status at a glance
- Error messages for failed backends
```

---

## How It Works

### MCP Protocol Basics

The relay implements the [MCP specification](https://modelcontextprotocol.io/docs/specification/basic/lifecycle):

**1. Initialization Sequence**
```json
Client → Server: {"method": "initialize", "params": {...}, "id": 1}
Server → Client: {"result": {"capabilities": {...}}, "id": 1}
Client → Server: {"method": "notifications/initialized"}
```

**2. Tool Discovery**
```json
Client → Server: {"method": "tools/list", "id": 2}
Server → Client: {"result": {"tools": [...]}, "id": 2}
```

**3. Tool Execution**
```json
Client → Server: {"method": "tools/call", "params": {"name": "tool_name", "arguments": {...}}, "id": 3}
Server → Client: {"result": {"content": [...]}, "id": 3}
```

### Tool Validation

The relay validates **every tool** from every backend:

**Required Fields:**
- `name` (string) - Tool identifier
- `description` (string) - Human-readable description
- `inputSchema` (object) - JSON Schema for parameters

**Input Schema Requirements:**
- Must be type `object`
- `properties` field (if present) must be an object
- `required` field (if present) must be a list of strings
- All required fields must exist in properties

**Naming Conflict Detection:**
- Tool names must be unique across ALL backends
- If two backends provide the same tool name, the second is marked invalid
- Example: If both `fiedler` and `dewey` provide `search`, only the first is registered

**Example Invalid Tool:**
```json
{
  "name": "bad_tool",
  "description": "Missing input schema"
  // ❌ Missing inputSchema field
}
```

**Validation Errors Logged:**
```
WARNING - Invalid tool from marco: bad_tool - Missing 'inputSchema' field
```

### Connection Management

**Keep-Alive Strategy:**
- Sends WebSocket ping every 30 seconds
- Prevents idle connection timeouts
- Automatically stops when connection closes

**Reconnection Logic:**
```
Connection fails
    ↓
Mark backend as failed
    ↓
Wait 5 seconds (exponential backoff)
    ↓
Attempt reconnect
    ↓
Success? → Mark healthy
    ↓
Failed? → Retry (infinite loop)
```

**Tool Call Resilience:**
```
Tool call received
    ↓
Backend disconnected?
    ↓
Yes: Reconnect with 10s timeout
    ↓
Success? → Execute tool call
    ↓
Failed during call? → Reconnect + retry once
    ↓
Still failed? → Return error to Claude Code
```

### Dynamic Reconfiguration

**File Watching:**
- Monitors `backends.yaml` for changes (using watchdog)
- Detects modifications in real-time
- Triggers `reload_config()` automatically

**Reload Process:**
1. Load new configuration
2. Compare with current backends
3. **Changed URLs**: Close old connection, reconnect with new URL
4. **New backends**: Add and connect
5. **Removed backends**: Close connection, purge tools from routing
6. **Notify Claude Code**: Send `notifications/tools/list_changed`

**Race Condition Protection:**
- Uses `reload_lock` to prevent concurrent reloads
- Tools purged from routing table BEFORE backend deletion
- Routing table reads protected by `routing_lock`

---

## Troubleshooting

### Common Issues

#### Issue 1: "No such tool available"

**Symptoms:**
```
Error: No such tool available: fiedler_send
```

**Diagnosis:**
```
Use relay_get_status
```

**Common Causes:**
1. Backend not connected
2. Tool name typo (check exact name in status)
3. Backend hasn't registered the tool yet

**Solution:**
```
Use relay_reconnect_server with:
  name: "fiedler"
```

---

#### Issue 2: Backend Shows as "degraded"

**Symptoms:**
```
⚠️ marco: degraded - Invalid response structure
```

**Diagnosis:**
```
Use relay_get_status

Check the "error" field for specific issue
```

**Common Causes:**
1. Backend MCP protocol bug (incorrect response format)
2. Some tools have invalid schemas
3. Tool naming conflicts

**Solution:**
1. Fix the backend's MCP implementation
2. Restart backend container: `docker restart marco-mcp`
3. Reconnect: `relay_reconnect_server` with name "marco"

---

#### Issue 3: "Connection refused"

**Symptoms:**
```
❌ gates: failed - Connection refused: [Errno 111] Connect call failed ('127.0.0.1', 9050)
```

**Diagnosis:**
```bash
# Check if container is running
docker ps | grep gates-mcp

# Check container logs
docker logs gates-mcp --tail 50
```

**Common Causes:**
1. Container not running
2. Wrong port in backends.yaml
3. Container running on different port

**Solution:**
```bash
# Check actual port
docker ps | grep gates-mcp
# Shows: 0.0.0.0:9051->8050/tcp

# If port is wrong, use relay tools to fix:
Use relay_remove_server with name: "gates"
Use relay_add_server with:
  name: "gates"
  url: "ws://localhost:9051"  # Correct port
```

---

#### Issue 4: Relay Not Responding

**Symptoms:**
- Relay tools don't work
- No tool responses in Claude Code

**Diagnosis:**
```bash
# Check if relay process is running
ps aux | grep mcp_relay

# Check relay logs (stderr output)
# Look for errors or connection issues
```

**Solution:**
1. Check what changed recently (did you edit relay files?)
2. Verify backends.yaml is valid YAML
3. Restart Claude Code (last resort)

---

### Debugging Tips

**Enable Debug Logging:**
Edit `mcp_relay.py` line 35:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    ...
)
```

**Check Tool Routing:**
```
Use relay_get_status

Look at tool_names for each backend:
- Are the expected tools listed?
- Do tool names match what you're calling?
```

**Verify Backend Health:**
```bash
# Test backend directly (outside relay)
docker logs fiedler-mcp --tail 20

# Check if backend is actually running
docker ps | grep mcp
```

**Common Mistakes:**
- ❌ Editing `backends.yaml` while relay is running (use relay tools)
- ❌ Restarting Claude Code instead of reconnecting backend
- ❌ Assuming relay is broken (it's almost always the backend)
- ❌ Forgetting to check container ports with `docker ps`

---

## Development

### Code Structure

```
mcp_relay.py (800 lines)
├── ConfigFileHandler          # Watches backends.yaml for changes
├── MCPRelay                   # Main relay class
│   ├── __init__              # Load configuration
│   ├── load_config()          # Parse backends.yaml
│   ├── reload_config()        # Hot-reload configuration
│   │
│   ├── connect_backend()      # WebSocket connection
│   ├── _perform_handshake()   # MCP initialize
│   ├── discover_tools()       # Tool discovery + validation
│   ├── _fetch_and_validate_tools()  # Health assessment
│   │
│   ├── keep_alive()           # WebSocket ping loop
│   ├── reconnect_backend()    # Retry logic
│   │
│   ├── call_tool()            # Route tool calls
│   ├── handle_request()       # MCP protocol handler
│   │
│   ├── handle_add_server()    # relay_add_server impl
│   ├── handle_remove_server() # relay_remove_server impl
│   ├── handle_list_servers()  # relay_list_servers impl
│   ├── handle_reconnect_server()  # relay_reconnect_server impl
│   ├── handle_get_status()    # relay_get_status impl
│   │
│   └── run()                  # Main stdio loop
```

### Adding a New Management Tool

1. **Define tool in `get_all_tools()`:**
```python
{
    "name": "relay_my_tool",
    "description": "What this tool does",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        },
        "required": ["param1"]
    }
}
```

2. **Implement handler:**
```python
async def handle_my_tool(self, arguments: dict) -> dict:
    param1 = arguments.get("param1")
    # ... implementation ...
    return {
        "jsonrpc": "2.0",
        "result": {
            "content": [{
                "type": "text",
                "text": "Result message"
            }]
        }
    }
```

3. **Add to routing in `call_tool()`:**
```python
handlers = {
    ...
    "relay_my_tool": self.handle_my_tool
}
```

### Testing

**Unit Testing Backends:**
```bash
# Start a mock backend
cd /mnt/projects/Joshua/tests
python mock_backend.py --port 9999

# Add to relay
Use relay_add_server with:
  name: "test"
  url: "ws://localhost:9999"

# Test tool discovery
Use relay_get_status

# Cleanup
Use relay_remove_server with name: "test"
```

**Integration Testing:**
```bash
# Test tool call flow
Use fiedler_send with:
  model: "gpt-4"
  prompt: "Hello"

# Check relay logs for routing
# Should show:
#   - Tool call received: fiedler_send
#   - Routing tool to backend: fiedler
#   - Sending request to backend
#   - Received response from backend
```

### Performance Considerations

**WebSocket Timeouts:**
- Default: 900 seconds (15 minutes)
- LLM calls can be slow - don't reduce this
- Adjust via `self.websocket_timeout`

**Reconnect Timeout:**
- Default: 10 seconds for tool call reconnects
- Prevents hanging on dead backends
- Adjust via `self.tool_call_reconnect_timeout`

**Keep-Alive Interval:**
- Default: 30 seconds
- Balance between responsiveness and overhead
- Adjust in `keep_alive()` function

---

## Version History

### V3.7.0 (Current)
**Critical Bug Fix:**
- Added missing `"jsonrpc": "2.0"` field to all relay management tool responses
- All 5 management tools now return proper MCP protocol-compliant responses
- Relay tools were silently failing in Claude Code without this field

### V3.6.0
**Resilience Improvements:**
- Fixed race condition during backend removal
- Tools now purged from routing table BEFORE backend deletion
- Improved file locking for backends.yaml updates
- Enhanced error logging with trace IDs

### V3.4.0
**Connection Management:**
- Non-blocking reconnect during config reload
- Keep-alive task cancellation improvements
- Better handling of concurrent reconnection attempts

### V3.0.0
**Major Refactor:**
- Switched from stdio subprocess spawning to WebSocket backends
- Added tool validation and health monitoring
- Implemented dynamic configuration with hot-reload
- Added 5 management tools for runtime control

---

## See Also

- **Troubleshooting Guide:** `/mnt/projects/Joshua/knowledge-base/Relay_Troubleshooting.md`
- **MCP Specification:** https://modelcontextprotocol.io/
- **Joshua Architecture:** `/mnt/projects/Joshua/CURRENT_STATUS.md`
- **Deployment Guide:** `/mnt/projects/Joshua/docs/deployment/relay_v3.6_deployment_plan.md`

---

## Contributing

**Before modifying the relay:**
1. Read `CLAUDE.md` Rule #1: DO NOT CHANGE WORKING SYSTEMS
2. The relay is battle-tested - if tools aren't working, check the backend first
3. Create a GitHub issue describing the proposed change
4. Test thoroughly in a dev environment
5. Document all changes in this README

**Critical Files (DO NOT EDIT without approval):**
- `backends.yaml` - Use relay tools instead
- `mcp_relay.py` - Requires extensive testing
- `.venv/` - Managed by pip

---

**Last Updated:** 2025-10-10
**Maintainer:** Joshua Project
**License:** Internal Use Only
