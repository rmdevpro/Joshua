# Logging System - Godot & Dewey

## Overview
All system logging flows through **Godot** (logger) and is stored/retrieved via **Dewey** (conversation & log storage).

---

## Architecture

```
Component → Godot (log writer) → Dewey (storage) → Query via Dewey tools
```

**Godot**: Centralized logging service (write-only queue)
**Dewey**: Persistent storage and retrieval (read/search)

---

## Writing Logs

### Via Godot Logger Tool

**Send log entry:**
```
mcp__iccm__godot_logger_log
  component: "fiedler"
  level: "INFO"
  message: "Successfully processed request"
  data: {"request_id": "123", "duration_ms": 45}
  trace_id: "abc-def-123" (optional)
```

**Log levels:**
- `ERROR` - Critical failures
- `WARN` - Warning conditions
- `INFO` - Informational messages
- `DEBUG` - Debugging information
- `TRACE` - Detailed trace information

---

## Retrieving Logs

### Via Dewey Query Tools

**Query logs by component:**
```
mcp__iccm__dewey_query_logs
  component: "fiedler"
  level: "ERROR"
  limit: 50
```

**Query logs by time range:**
```
mcp__iccm__dewey_query_logs
  start_time: "2025-10-10T00:00:00Z"
  end_time: "2025-10-10T23:59:59Z"
  limit: 100
```

**Query logs by trace ID:**
```
mcp__iccm__dewey_query_logs
  trace_id: "abc-def-123"
  limit: 100
```

**Full-text search in logs:**
```
mcp__iccm__dewey_query_logs
  search: "authentication failed"
  level: "ERROR"
  limit: 50
```

---

## Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `component` | string | Filter by component name |
| `level` | string | Minimum log level (ERROR, WARN, INFO, DEBUG, TRACE) |
| `start_time` | ISO 8601 | Start of time range |
| `end_time` | ISO 8601 | End of time range |
| `trace_id` | string | Distributed trace ID |
| `search` | string | Full-text search in message |
| `limit` | int | Max results (1-1000, default 100) |

---

## Log Statistics

**Get log overview:**
```
mcp__iccm__dewey_get_log_stats
```

**Returns:**
- Total log count
- Count by level
- Count by component
- Time range of logs
- Storage size

---

## Setting Log Levels

**Control verbosity per component:**
```
mcp__iccm__godot_logger_set_level
  component: "fiedler"
  level: "DEBUG"
```

**Effect:**
- Only logs at specified level or higher are stored
- Useful for reducing noise in production
- Can be changed dynamically without restart

---

## Clearing Logs

**Clear old logs:**
```
mcp__iccm__godot_logger_clear
  before_time: "2025-10-01T00:00:00Z"
  component: "fiedler" (optional - clears all if omitted)
```

**⚠️ Caution:** This permanently deletes logs. Ensure you have backups if needed.

---

## Common Use Cases

### Debugging Component Issues

**1. Check recent errors:**
```
mcp__iccm__dewey_query_logs
  component: "fiedler"
  level: "ERROR"
  limit: 20
```

**2. Get context around error:**
```
mcp__iccm__dewey_query_logs
  component: "fiedler"
  trace_id: "abc-123" (from error log)
  limit: 50
```

**3. See full request flow:**
```
# All logs with same trace_id show distributed request path
```

---

### Monitoring System Health

**Check error rates:**
```
# Query ERROR logs over time period
mcp__iccm__dewey_query_logs
  level: "ERROR"
  start_time: "2025-10-10T00:00:00Z"
  end_time: "2025-10-10T23:59:59Z"
```

**Monitor specific component:**
```
mcp__iccm__dewey_query_logs
  component: "dewey-mcp"
  level: "WARN"
  limit: 100
```

---

### Troubleshooting Workflow

**Step 1: Identify the issue**
```
# Check recent errors across all components
mcp__iccm__dewey_query_logs
  level: "ERROR"
  limit: 50
```

**Step 2: Get component context**
```
# Drill down to specific component
mcp__iccm__dewey_query_logs
  component: "fiedler"
  level: "DEBUG"
  start_time: "2025-10-10T14:00:00Z"
  limit: 100
```

**Step 3: Trace distributed request**
```
# Follow trace_id through system
mcp__iccm__dewey_query_logs
  trace_id: "abc-123"
  limit: 100
```

---

## Best Practices

### 1. Use Appropriate Log Levels

- `ERROR`: Only for failures requiring attention
- `WARN`: Potential issues, degraded performance
- `INFO`: Normal operations, milestones
- `DEBUG`: Detailed diagnostic information
- `TRACE`: Very verbose, usually disabled in production

### 2. Include Trace IDs

**For distributed requests:**
```python
trace_id = generate_trace_id()
log(component="fiedler", level="INFO", message="Processing request", trace_id=trace_id)
# Pass trace_id to downstream calls
```

**Benefits:**
- Track request across multiple components
- Debug distributed workflows
- Correlate logs from different services

### 3. Add Structured Data

**Good:**
```
data: {
  "user_id": "123",
  "operation": "fetch_data",
  "duration_ms": 45,
  "status": "success"
}
```

**Bad:**
```
message: "User 123 fetched data in 45ms successfully"  # Hard to query
```

### 4. Set Appropriate Levels in Production

**Development:**
```
set_level(component="fiedler", level="DEBUG")
```

**Production:**
```
set_level(component="fiedler", level="INFO")
```

---

## Component Naming

**Standard component names:**
- `fiedler` - LLM orchestration
- `dewey-mcp` - Conversation storage
- `godot-mcp` - Logging service
- `horace-mcp` - File management
- `playfair-mcp` - Diagram generation
- `gates-mcp` - Document creation
- `marco-mcp` - Browser automation

**Use consistent names across logs for easier querying.**

---

## Troubleshooting

### Logs Not Appearing

**Check Godot logger:**
```
mcp__iccm__godot_logger_set_level
  component: "your-component"
  level: "DEBUG"
```

**Verify Godot running:**
```bash
docker ps | grep godot-mcp
docker logs godot-mcp --tail 20
```

### Query Returns Empty

**Possible causes:**
1. Time range too narrow
2. Component name mismatch
3. Log level too restrictive
4. Logs haven't been written yet

**Solution:**
```
# Broaden search
mcp__iccm__dewey_query_logs
  limit: 100
  # No filters - see what's there
```

---

## Example: Complete Debug Session

```
# 1. User reports Fiedler error
# Check recent Fiedler errors
mcp__iccm__dewey_query_logs
  component: "fiedler"
  level: "ERROR"
  limit: 10

# 2. Found error with trace_id "xyz-789"
# Get full request trace
mcp__iccm__dewey_query_logs
  trace_id: "xyz-789"
  limit: 50

# 3. See the error started in dewey-mcp
# Check dewey logs around that time
mcp__iccm__dewey_query_logs
  component: "dewey-mcp"
  start_time: "2025-10-10T14:30:00Z"
  end_time: "2025-10-10T14:35:00Z"
  level: "DEBUG"
  limit: 100

# 4. Root cause found in logs
# Fix the issue

# 5. Verify fix by checking new logs
mcp__iccm__dewey_query_logs
  component: "dewey-mcp"
  level: "ERROR"
  start_time: "2025-10-10T15:00:00Z"
  limit: 20
```

---

## See Also

- `/mnt/projects/Joshua/knowledge-base/Error_Handling_Protocol.md` - Error handling workflow
- `/mnt/projects/Joshua/knowledge-base/Relay_Troubleshooting.md` - MCP relay issues

---

*Last Updated: 2025-10-10*
