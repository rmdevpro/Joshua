# Shared Libraries for Joshua Components

**Last Updated**: 2025-10-09
**Status**: Active Reference

---

## Overview

This document catalogs the shared libraries used across Joshua components to ensure consistency, reduce code duplication, and prevent recurring bugs. All new MADs and components should use these standard libraries instead of implementing custom solutions.

---

## 1. iccm-network

**Location**: `/mnt/projects/Joshua/libs/iccm-network/`
**Purpose**: Standardized WebSocket MCP server implementation
**Version**: 1.1.0

### What It Does
- Provides zero-configuration MCP server over WebSocket
- **ALWAYS** binds to `0.0.0.0` (never configurable - prevents network bugs)
- Handles JSON-RPC 2.0 protocol correctly (initialize, tools/list, tools/call)
- Eliminates the recurring "connection timeout" issues from custom implementations

### Installation

**Docker (recommended for MADs)**:
```dockerfile
# In docker-compose.yml
volumes:
  - ../../../libs/iccm-network:/app/iccm-network:ro

# In requirements.txt
/app/iccm-network
```

**Local Development**:
```bash
pip install -e /mnt/projects/Joshua/libs/iccm-network
```

### Usage Example
```python
from iccm_network import MCPServer, MCPToolError

# Define tools and handlers
TOOLS = {
    "my_tool": {
        "description": "Does something",
        "inputSchema": {...}
    }
}

HANDLERS = {
    "my_tool": my_tool_handler
}

# Create and start server
server = MCPServer(
    name="my-component",
    version="1.0.0",
    port=8080,
    tool_definitions=TOOLS,
    tool_handlers=HANDLERS
)
await server.start()  # Runs forever
```

### Components Using This
- Sergey MAD (Google Workspace)
- Horace (File catalog) - Successfully deployed
- Others pending migration

---

## 2. godot/mcp_logger

**Location**: Copied to each MAD as `godot/mcp_logger.py`
**Purpose**: Centralized logging to Godot service via MCP
**Source**: Originally from Dewey MAD

### What It Does
- Sends structured logs to Godot logging service
- Logs stored in PostgreSQL for analysis
- Supports log levels: ERROR, WARN, INFO, DEBUG, TRACE
- Non-blocking - logging failures don't break the application

### Installation

**Copy from existing MAD**:
```bash
# Copy the godot module to your MAD
cp -r /mnt/projects/Joshua/mads/dewey/dewey/godot /mnt/projects/Joshua/mads/your-mad/
```

### Usage Example
```python
from godot.mcp_logger import log_to_godot

# Send a log
await log_to_godot(
    level="INFO",
    message="Processing request",
    component="my-component",
    data={"request_id": "123", "user": "test"},
    godot_url="ws://godot-mcp:8060"  # Usually from env var
)
```

### Components Using This
- Dewey (Conversation storage)
- Sergey (Google Workspace)
- Playfair (Diagram generation)
- Gates (Document generation)
- All new MADs should use this

---

## 3. Docker Network Configuration

**Network**: `joshua_network`
**Type**: External Docker network
**Purpose**: Inter-container communication

### Standard docker-compose.yml Pattern
```yaml
services:
  my-mad:
    # ... other config ...
    networks:
      - joshua_network

networks:
  joshua_network:
    external: true
```

### Why External Network?
- All MADs can communicate without complex network configuration
- Consistent container discovery
- Simplifies service-to-service communication (e.g., MAD → Godot)

---

## 4. Environment Variable Patterns

### Standard Environment Variables
All MADs should support these standard environment variables:

```bash
# Port configuration
{MAD_NAME}_PORT=8080  # e.g., SERGEY_PORT=8095

# Godot logging service
GODOT_URL=ws://godot-mcp:8060

# Python path for mounted libraries
PYTHONPATH=/app:/app/iccm-network

# Logging level
LOG_LEVEL=info  # trace, debug, info, warn, error
```

### Service-Specific Credentials
```bash
# Examples from various MADs
GOOGLE_SERVICE_ACCOUNT_PATH=/config/google-service-account-credentials.json  # Sergey
POSTGRES_CONNECTION_STRING=postgresql://user:pass@host/db  # Dewey
```

---

## 5. File System Mounts

### Standard Volume Mounts
```yaml
volumes:
  # Shared libraries (read-only)
  - ../../../libs/iccm-network:/app/iccm-network:ro

  # Service configuration (read-only)
  - ./config:/config:ro

  # Working storage (read-write)
  - /mnt/irina_storage/{service-name}:/data
```

### Mount Points Convention
- `/app/` - Application code and libraries
- `/config/` - Configuration files and credentials
- `/data/` - Working directory for file operations

---

## 6. MCP Tool Naming Convention

All MCP tools must follow the naming pattern:
```
{service_name}_{operation}
```

Examples:
- `sergey_docs_create`
- `horace_register_file`
- `dewey_get_conversation`
- `godot_logger_log`

**IMPORTANT**: When accessed via MCP relay, tools are prefixed with namespace:
- Direct: `sergey_docs_create`
- Via relay: `mcp__iccm__sergey_docs_create`

---

## 7. Error Handling Pattern

### MCPToolError Usage
```python
from iccm_network import MCPToolError

# Standard error codes (JSON-RPC 2.0)
raise MCPToolError("Invalid input", code=-32602)  # Invalid params
raise MCPToolError("Not initialized", code=-32603)  # Internal error
raise MCPToolError("Operation failed", code=-32000)  # Server error (custom)
```

### Error Codes Reference
- `-32700` - Parse error (invalid JSON)
- `-32600` - Invalid request
- `-32601` - Method not found
- `-32602` - Invalid params
- `-32603` - Internal error
- `-32000` - Server error (application-specific)

---

## 8. Health Check Pattern

### Standard Docker Health Check
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import websocket; ws = websocket.create_connection('ws://localhost:8080'); ws.close()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

This verifies the WebSocket server is responding.

---

## 9. Blue/Green Deployment Pattern

Components should support blue/green deployment:

```yaml
services:
  my-mad-blue:
    container_name: my-mad-blue
    # ... configuration ...

  my-mad-green:
    container_name: my-mad-green
    # ... same configuration ...
    profiles: ["green"]  # Only starts when explicitly requested
```

This allows testing new versions without disrupting the running service.

---

## Migration Checklist

When migrating a component to use shared libraries:

- [ ] Replace custom WebSocket server with `iccm-network`
- [ ] Replace custom logging with `godot/mcp_logger`
- [ ] Ensure binding to `0.0.0.0` (automatic with iccm-network)
- [ ] Use standard environment variable patterns
- [ ] Follow MCP tool naming convention
- [ ] Add to `joshua_network`
- [ ] Implement standard health check
- [ ] Support blue/green deployment
- [ ] Update component README with library versions

---

## Adding New Shared Libraries

When creating a new shared library:

1. Place in `/mnt/projects/Joshua/libs/{library-name}/`
2. Create comprehensive README with migration guide
3. Include version management
4. Provide migration examples from existing components
5. Update this document
6. Announce to team via GitHub issue

---

## Known Issues & Workarounds

### Issue: "Connection refused" from network
**Cause**: Component binding to `127.0.0.1` instead of `0.0.0.0`
**Solution**: Use `iccm-network` library which enforces correct binding

### Issue: Logs not reaching Godot
**Cause**: Godot service down or wrong URL
**Solution**: Check `GODOT_URL` environment variable and Godot container status

### Issue: Import errors for shared libraries
**Cause**: Library not mounted or PYTHONPATH not set
**Solution**: Check docker-compose volumes and PYTHONPATH environment variable

---

## Future Additions

Potential shared libraries to develop:
- Authentication/authorization library
- Rate limiting/quota management
- Caching layer
- Metrics collection
- Configuration management
- Secret management

---

*This document is a living reference. Update as new shared libraries are added or patterns evolve.*