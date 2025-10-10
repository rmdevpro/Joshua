# Sergey MAD Implementation Notes

## Standard Libraries Usage

### 1. iccm-network (WebSocket MCP Server)

**Location**: `/mnt/projects/Joshua/libs/iccm-network/`

**Usage**:
```python
from iccm_network import MCPServer, MCPToolError

# Define tools
TOOLS = {
    "sergey_create_document": {
        "description": "Create a new Google Document",
        "inputSchema": {...}
    },
    "sergey_read_sheet": {
        "description": "Read data from Google Sheet",
        "inputSchema": {...}
    }
}

# Define handlers
async def create_document(title: str, content: str = None) -> dict:
    # Implementation using Google Docs API
    pass

HANDLERS = {
    "sergey_create_document": create_document,
    "sergey_read_sheet": read_sheet
}

# Start server
server = MCPServer(
    name="sergey",
    version="1.0.0",
    port=8095,
    tool_definitions=TOOLS,
    tool_handlers=HANDLERS
)
await server.start()
```

**Benefits**:
- ✅ No custom WebSocket code needed
- ✅ Always binds to 0.0.0.0 (network accessible)
- ✅ Standard JSON-RPC 2.0 protocol
- ✅ Proper error handling

### 2. Godot MCP Logger

**Pattern**: Copy `mcp_logger.py` from another MAD into `sergey/godot/`

**Usage**:
```python
from godot.mcp_logger import MCPLogger

# Initialize logger
logger = MCPLogger(
    component="sergey",
    godot_url="ws://godot-mcp:8060"
)

# Log operations
await logger.info("Creating Google Document", {"title": title})
await logger.error("Failed to access sheet", {"sheet_id": sheet_id, "error": str(e)})
```

**Benefits**:
- ✅ Centralized logging in Godot/Dewey
- ✅ Queryable via `dewey_query_logs` tool
- ✅ Standard log levels (trace, debug, info, warn, error)
- ✅ Structured logging with metadata

## Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy libraries
COPY --from=joshua /mnt/projects/Joshua/libs/iccm-network /app/iccm-network

# Copy application
COPY sergey/ /app/sergey/

CMD ["python", "-m", "sergey"]
```

```yaml
# docker-compose.yml
services:
  sergey-mcp:
    build: .
    container_name: sergey-mcp
    ports:
      - "8095:8095"
    volumes:
      - ../libs/iccm-network:/app/iccm-network:ro
      - ./config:/config:ro
    environment:
      - SERGEY_PORT=8095
      - GODOT_URL=ws://godot-mcp:8060
    networks:
      - joshua_network
```

## Google API Integration

**Source**: Based on `api_manager.py` from advanced-mcp-server

**Services to implement**:
- Google Docs API (docs, v1)
- Google Sheets API (sheets, v4)
- Google Slides API (slides, v1)
- Google Drive API (drive, v3)
- Google Calendar API (calendar, v3)

**Authentication**:
- Service account: `advanced-mcp-server@cs-poc-qybtdrmnhcet8mfq3rqlzwv.iam.gserviceaccount.com`
- Credentials: `/config/google-service-account-credentials.json`

## Testing Compliance

Per Issue #13, after implementation verify:
- [ ] Container builds successfully
- [ ] All tools appear in `relay_get_status()`
- [ ] Tools callable from Claude Code
- [ ] Logs appear in Dewey (`dewey_query_logs`)
- [ ] No regressions in functionality

## No Custom Code Policy

**DO NOT**:
- Write custom WebSocket servers
- Implement custom MCP protocol
- Create custom logging systems
- Bind to 127.0.0.1 or localhost

**DO**:
- Use iccm-network for all MCP/WebSocket needs
- Use mcp_logger for all logging
- Follow established patterns from other MADs
- Always bind to 0.0.0.0 (handled by iccm-network)

---
*Following ICCM standard library architecture per Issue #13*