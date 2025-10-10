# MAD Migration Guide - joshua-libs Implementation

**Purpose:** Migrate existing MADs to use standardized joshua-libs (joshua_network + joshua_logger)

**Target Audience:** This guide is for updating EXISTING MADs only. New MADs should follow `/mnt/projects/Joshua/lib/README.md` from the start.

**Reference Implementation:** Dewey MCP (fully migrated as of 2025-10-10)

---

## Overview

This guide ensures all existing MADs use:
1. **joshua_network.Server** - Standard MCP protocol implementation
2. **joshua_logger.Logger** - Centralized logging to Godot

**Why migrate?**
- ✅ Future-proof: Easy migration to Rogers Message Bus (just update library + restart)
- ✅ Consistent: All MADs use same protocol implementation
- ✅ Debuggable: All logs centralized in one place
- ✅ Reliable: Auto-reconnection, backup logging, silent failures

---

## Pre-Migration Checklist

Before starting migration, verify:

- [ ] MAD is currently working and all tools discoverable
- [ ] Have access to test the MAD after changes
- [ ] Understand current MAD architecture (read existing code)
- [ ] Blue/green deployment available (or plan for downtime)

---

## Migration Steps

### Step 1: Audit Current Implementation

**Goal:** Identify what needs to change

**Actions:**

1. **Check MCP Server Implementation:**
   ```bash
   grep -r "class.*Server\|websockets.serve\|WebSocket" mads/<mad-name>/ --include="*.py"
   ```
   - If custom WebSocket server → Needs migration to joshua_network.Server
   - If already using joshua_network.Server → ✅ Skip to Step 2

2. **Check Logging Implementation:**
   ```bash
   grep -r "import logging\|logger\.\|GodotLogger\|log_to_godot" mads/<mad-name>/ --include="*.py"
   ```
   - If using Python `logging` module → Needs migration to joshua_logger
   - If using custom Godot logger → Needs migration to joshua_logger
   - If already using joshua_logger → ✅ Skip to Step 3

3. **Check Dead Code:**
   ```bash
   # Look for custom logger modules that might be unused
   find mads/<mad-name>/ -name "*logger*.py" -o -name "*godot*.py"
   ```

**Document findings:**
- [ ] Server implementation type: _____________
- [ ] Logging implementation type: _____________
- [ ] Dead code found: _____________

---

### Step 2: Migrate MCP Server to joshua_network.Server

**Goal:** Replace custom WebSocket server with standardized joshua_network.Server

#### 2.1: Update Dockerfile

**Before:**
```dockerfile
# Old - no library installation or custom approach
COPY mads/<mad>/requirements.txt .
RUN pip install -r requirements.txt
```

**After:**
```dockerfile
# Install joshua-libs first
COPY --chown=root:root lib/joshua_network /tmp/joshua-libs-install/joshua_network
COPY --chown=root:root lib/joshua_logger /tmp/joshua-libs-install/joshua_logger
COPY --chown=root:root lib/pyproject.toml /tmp/joshua-libs-install/
RUN pip install --no-cache-dir /tmp/joshua-libs-install && rm -rf /tmp/joshua-libs-install

# Then install MAD-specific requirements
COPY mads/<mad>/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

#### 2.2: Update docker-compose.yml

**Before:**
```yaml
services:
  my-mad:
    build:
      context: .  # Wrong - can't access lib/
      dockerfile: Dockerfile
```

**After:**
```yaml
services:
  my-mad:
    build:
      context: ../..  # Joshua project root
      dockerfile: mads/<mad>/Dockerfile
```

**Also add environment variables:**
```yaml
    environment:
      # Godot Logging Integration
      GODOT_URL: ws://godot-mcp:9060
      LOGGING_ENABLED: "true"
```

#### 2.3: Update mcp_server.py

**Before (Custom Server):**
```python
import asyncio
import websockets
import json

async def handle_connection(websocket, path):
    async for message in websocket:
        # Custom MCP protocol handling
        pass

async def main():
    server = await websockets.serve(handle_connection, "0.0.0.0", 9000)
    await asyncio.Future()
```

**After (joshua_network.Server):**
```python
import asyncio
import json
import sys
from typing import Any, Dict

# Import joshua libraries
from joshua_network import Server
from joshua_logger import Logger

from <mad> import config
from <mad> import tools

# Initialize logger
logger = Logger()

# Define MCP tool schemas
TOOL_DEFINITIONS = {
    "my_tool": {
        "description": "Tool description",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param"]
        }
    }
}

# Create tool handler wrapper
async def wrap_tool_handler(tool_name: str, **arguments):
    """Wrapper to call tools and log execution."""
    await logger.log('TRACE', f'Tool call: {tool_name}', '<mad>-mcp', data={'arguments': arguments})

    try:
        # Get tool function from tools module
        tool_func = getattr(tools, tool_name, None)
        if not tool_func or not callable(tool_func):
            raise Exception(f"Tool not found: {tool_name}")

        # Execute tool
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**arguments)
        else:
            result = tool_func(**arguments)

        await logger.log('TRACE', f'Tool completed: {tool_name}', '<mad>-mcp', data={'success': True})

        # Format for MCP protocol
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }

    except Exception as e:
        await logger.log('ERROR', f'Tool failed: {tool_name}', '<mad>-mcp', data={'error': str(e)})
        raise

# Factory function for tool handlers (avoids closure issues)
def make_handler(tool_name):
    async def handler(**args):
        return await wrap_tool_handler(tool_name, **args)
    return handler

TOOL_HANDLERS = {
    tool_name: make_handler(tool_name)
    for tool_name in TOOL_DEFINITIONS.keys()
}

async def main():
    """Main entry point."""
    await logger.log('INFO', '<MAD> MCP server starting', '<mad>-mcp', data={'version': '1.0.0'})

    # Create server
    server = Server(
        name="<mad>-mcp-server",
        version="1.0.0",
        port=config.MCP_PORT,
        tool_definitions=TOOL_DEFINITIONS,
        tool_handlers=TOOL_HANDLERS
    )

    # Start server
    await server.start()
    await logger.log('INFO', '<MAD> MCP server operational', '<mad>-mcp',
                     data={'host': config.MCP_HOST, 'port': config.MCP_PORT})

    # Run forever
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        await logger.log('INFO', '<MAD> MCP server shutting down', '<mad>-mcp')
    finally:
        await server.stop()
        await logger.log('INFO', '<MAD> MCP server stopped', '<mad>-mcp')

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Pattern Notes:**
- ✅ Use factory function `make_handler()` to avoid closure issues with tool_name
- ✅ Wrap all tool calls for logging and error handling
- ✅ Return MCP protocol format: `{"content": [{"type": "text", "text": "..."}]}`
- ✅ Use joshua_logger for all logging (not Python logging)

---

### Step 3: Migrate Logging to joshua_logger

**Goal:** Replace ALL local logging with centralized joshua_logger

#### 3.1: Find All Logging Usage

```bash
cd /mnt/projects/Joshua/mads/<mad>
grep -rn "import logging\|logger = logging\|logger\." --include="*.py"
```

#### 3.2: Replace in Each File

**Before:**
```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Something happened")
    logger.error(f"Error: {error}")
```

**After:**
```python
from joshua_logger import Logger

logger = Logger()

async def my_function():  # Must be async to use await
    await logger.log("INFO", "Something happened", "<mad>-component")
    await logger.log("ERROR", f"Error: {error}", "<mad>-component")
```

**Component Naming Convention:**
- `<mad>-mcp` - MCP server lifecycle and tool execution
- `<mad>-database` - Database operations (if applicable)
- `<mad>-tools` - Tool execution and results
- `<mad>-<specific>` - Any other component-specific logging

**Critical Migration Rules:**

1. **ALL logging functions must be async:**
   ```python
   # Before
   def my_function():
       logger.info("message")

   # After
   async def my_function():
       await logger.log("INFO", "message", "component")
   ```

2. **Use keyword arguments for optional params:**
   ```python
   # ✅ CORRECT
   await logger.log("INFO", "message", "component", data={"key": "value"})

   # ❌ INCORRECT
   await logger.log("INFO", "message", "component", {"key": "value"})
   ```

3. **Log levels:**
   - `TRACE` - Detailed debugging (tool calls, internal state)
   - `DEBUG` - Debug information
   - `INFO` - Informational messages (lifecycle, operations)
   - `WARN` - Warnings
   - `ERROR` - Errors and exceptions

#### 3.3: Remove Python Logging Setup

**In config.py or main module:**

**Before:**
```python
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def setup_logging():
    """Configure Python logging."""
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("websockets").setLevel(logging.WARNING)

# Initialize logging
setup_logging()
```

**After:**
```python
# Remove logging setup entirely - joshua_logger handles it
# No logging configuration needed
```

#### 3.4: Remove Dead Custom Logger Code

**Check for and remove:**
- `mads/<mad>/godot/` directories with custom loggers
- `mcp_logger.py` files
- `GodotLogger` classes
- `log_to_godot()` functions

```bash
# Find potential dead code
find mads/<mad>/ -name "*logger*.py" -o -name "godot" -type d
```

**Delete if unused:**
```bash
rm -rf mads/<mad>/<module>/godot/
rm mads/<mad>/<module>/custom_logger.py
```

---

### Step 4: Rebuild and Test

#### 4.1: Rebuild Container

```bash
cd /mnt/projects/Joshua/mads/<mad>
docker compose build
```

**Expected output:**
- ✅ joshua-libs installation successful
- ✅ MAD requirements installation successful
- ✅ No build errors

#### 4.2: Restart Container

```bash
docker restart <mad>-mcp-blue  # or appropriate container name
```

#### 4.3: Check Startup Logs

```bash
docker logs <mad>-mcp-blue --tail 50
```

**Expected in logs:**
```
Logger initialized: url=ws://godot-mcp:9060, timeout=2.0, backup_dir=/tmp/joshua_logs
Starting <mad>-mcp-server server v1.0.0 on 0.0.0.0:9XXX
Tools available: ['tool1', 'tool2', ...]
✓ Server listening at ws://0.0.0.0:9XXX
✓ Health check available at http://0.0.0.0:9XXX/healthz
```

**No Python logging setup messages should appear for MAD code** (joshua_network.Server may have some for its own diagnostics - that's OK)

#### 4.4: Verify Relay Connection

Use MCP relay tools:
```python
# Check status
mcp__iccm__relay_get_status()

# Reconnect if needed
mcp__iccm__relay_reconnect_server(name="<mad>")
```

**Expected:**
- ✅ `"connected": true`
- ✅ `"health": "healthy"`
- ✅ `"tools": N` (correct tool count)

#### 4.5: Test Tool Execution

Call a tool to verify logging:
```python
# Call any MAD tool
mcp__iccm__<mad>_<tool_name>(...)
```

Then check Godot for logs:
```python
mcp__iccm__godot_logger_query(component="<mad>-mcp", limit=10)
```

**Expected:**
- ✅ TRACE logs for tool call and completion
- ✅ Component name correct
- ✅ Structured data included

#### 4.6: Verify Backup Logging

**Check no backup files created (means Godot connection working):**
```bash
docker exec <mad>-mcp-blue ls -la /tmp/joshua_logs/
```

**Expected:**
```
total 8
drwxr-xr-x 2 root root 4096 <date> .
drwxrwxrwt 1 root root 4096 <date> ..
```

Empty = good! Godot connection working, no backup needed.

---

### Step 5: Commit Changes

#### 5.1: Review Changes

```bash
git status
git diff mads/<mad>/
```

#### 5.2: Stage Changes

```bash
git add mads/<mad>/
```

#### 5.3: Commit with Descriptive Message

```bash
git commit -m "Migrate <MAD> to joshua-libs (joshua_network + joshua_logger)

**MCP Server Migration:**
- Migrated from custom WebSocket server to joshua_network.Server
- Implemented tool handler wrapper pattern with factory functions
- All tools now use standard MCP protocol format

**Logging Migration:**
- Replaced Python logging with joshua_logger in all files
- All logs now go to Godot (backup to /tmp/joshua_logs if unavailable)
- Removed custom logger code from <module>/godot/
- Removed Python logging setup from config.py

**Files Changed:**
- mads/<mad>/Dockerfile - Added joshua-libs installation
- mads/<mad>/docker-compose.yml - Updated build context to ../..
- mads/<mad>/<module>/mcp_server.py - Complete rewrite using joshua_network
- mads/<mad>/<module>/tools.py - Replaced logging with joshua_logger
- mads/<mad>/<module>/config.py - Removed logging setup
- mads/<mad>/<module>/<other>.py - Replaced logging with joshua_logger

**Logging Components:**
- <mad>-mcp: Server lifecycle and tool execution
- <mad>-<component>: Component-specific operations

**Verification:**
✅ Container rebuilt successfully
✅ All N tools healthy and discoverable
✅ joshua_logger connected to Godot
✅ Tool execution logging verified

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 5.4: Push Changes

```bash
git push
```

---

### Step 6: Run Checkpoint Process

**Goal:** Document completion and update project status

**REQUIRED:** After completing each MAD migration, follow the checkpoint process from `/mnt/projects/Joshua/processes/Checkpoint_Process.md`

**Quick Checklist:**

1. **Update CURRENT_STATUS.md:**
   - Add migration completion to Recent Completions
   - Document what was changed
   - Update component status table if applicable

2. **Update Project Board:**
   - Check off completed MAD in "Migrate all MADs to joshua-libs standard" item
   - Update progress percentage

3. **Verify Git State:**
   - All changes committed and pushed
   - Working directory clean

4. **Update Migration Tracking:**
   - Update this document's MAD Migration Tracking section
   - Mark MAD as complete with commit hash

**Then proceed to next MAD migration.**

---

## Common Issues and Solutions

### Issue: Build fails with "ModuleNotFoundError: No module named 'joshua_network'"

**Cause:** Dockerfile not installing joshua-libs or build context wrong

**Solution:**
1. Verify Dockerfile has joshua-libs installation section
2. Verify docker-compose.yml has `context: ../..`
3. Rebuild: `docker compose build --no-cache`

---

### Issue: Tool discovery shows 0 tools, error "Method 'notifications/initialized' is not supported"

**Cause:** Not using joshua_network.Server (custom server missing MCP handlers)

**Solution:**
1. Verify mcp_server.py imports `from joshua_network import Server`
2. Verify creating `Server()` instance (not custom WebSocket server)
3. Check `tool_definitions` and `tool_handlers` passed to Server()

---

### Issue: Logs not appearing in Godot

**Cause:** Several possibilities

**Solution:**
1. Check logger initialized: `logger = Logger()` at module level
2. Check using `await logger.log(...)` (not `logger.log(...)` without await)
3. Check component name is consistent
4. Check Godot is running: `docker ps | grep godot`
5. Check backup logs: `docker exec <mad>-mcp ls /tmp/joshua_logs/`

---

### Issue: AsyncIO errors "object NoneType can't be used in 'await' expression"

**Cause:** Calling sync function as async or vice versa

**Solution:**
1. Tool handler functions must be `async def`
2. Logger calls must use `await logger.log(...)`
3. Check `asyncio.iscoroutinefunction()` before calling with await

---

### Issue: Lambda closure bug - all tools call the same function

**Cause:** Using lambda in TOOL_HANDLERS dictionary

**Solution:**
Use factory function pattern:
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

---

## MAD Migration Tracking

Use this checklist to track progress:

### Priority MADs (Active/Frequently Used)

- [x] **Dewey** - ✅ COMPLETE (Reference implementation)
- [ ] **Fiedler** - LLM orchestration
- [ ] **Godot** - Logging hub (already uses joshua_network, verify logging)
- [ ] **Horace** - File management
- [ ] **Sergey** - Google Workspace integration

### Secondary MADs (Less Frequently Used)

- [ ] **Marco** - Browser automation (currently degraded)
- [ ] **Playfair** - Diagram generation (currently degraded)
- [ ] **Gates** - Document creation (currently failed)

---

## Post-Migration Benefits

After migrating all MADs:

1. **Future-Proof Architecture:**
   - Change logging backend (Godot → Rogers Bus) = update 1 library + restart containers
   - All MADs automatically use new backend

2. **Centralized Debugging:**
   - All logs in one place (Godot → Dewey → PostgreSQL)
   - Query by component, trace ID, time range, etc.

3. **Consistent Protocol:**
   - All MADs use same MCP implementation
   - Same error handling, reconnection logic, health checks

4. **Reliable Operation:**
   - Auto-reconnection on failures
   - Backup logging if Godot unavailable
   - Silent logging failures (never crash MAD)

---

## Reference Files

**Completed Migration:**
- `/mnt/projects/Joshua/mads/dewey/` - Full reference implementation

**Library Documentation:**
- `/mnt/projects/Joshua/lib/README.md` - joshua-libs documentation
- `/mnt/projects/Joshua/lib/joshua_logger/README.md` - Logger details

**Architecture:**
- `/mnt/projects/Joshua/TECHNICAL_ARCHITECTURE.md` - System overview
- `/mnt/projects/Joshua/knowledge-base/File_System_Architecture.md` - File system

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-10
**Reference Implementation:** Dewey MCP (commit 17e499c)
